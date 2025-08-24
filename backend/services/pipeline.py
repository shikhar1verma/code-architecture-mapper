import os
from typing import Dict, Any, List
from collections import Counter
import json
import re

from backend.config import TOP_FILES, COMPONENT_COUNT, CHUNK_SIZE_CHARS, USE_LLM_FOR_DIAGRAMS, USE_LLM_FOR_DEPENDENCY_ANALYSIS
from backend.utils.git_tools import shallow_clone, walk_repo
from backend.utils.text import read_text, chunk_text
from backend.parsing.py_ast import is_python, py_import_edges
from backend.parsing.ts_imports import is_ts, ts_import_edges
from backend.graphing.build import build_graph
from backend.graphing.mermaid import modules_mermaid, folders_mermaid, intelligent_modules_mermaid
from backend.llm.gemini import generate_markdown, GeminiQuotaExhaustedError, GeminiAPIError
from backend.llm.prompts import OVERVIEW_SYSTEM, OVERVIEW_USER_TMPL, COMPONENT_SYSTEM, COMPONENT_USER_TMPL, DEPENDENCY_ANALYSIS_SYSTEM, DEPENDENCY_ANALYSIS_USER_TMPL, MERMAID_GENERATION_SYSTEM, MERMAID_GENERATION_USER_TMPL, MERMAID_BALANCED_GENERATION_SYSTEM, MERMAID_BALANCED_GENERATION_USER_TMPL

SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def _extract_markdown_section(markdown_text: str, section_name: str) -> str:
    """Extract a specific section from markdown text"""
    if not markdown_text:
        return ""
    
    # Pattern to match section headers (## Section Name)
    pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\n#|\Z)"
    match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return ""


def run_analysis(analysis_id: str, repo_url: str, force_refresh: bool = False) -> Dict[str, Any]:
    root, sha = shallow_clone(repo_url)

    file_infos: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []

    # scan & parse
    for abs_path in walk_repo(root):
        rel = os.path.relpath(abs_path, root)
        _, ext = os.path.splitext(rel)
        if ext not in SUPPORTED_EXTS:
            continue
        code = read_text(abs_path, max_bytes=200_000)
        loc = code.count("\n") + 1
        lang = lang_of_ext(ext)
        file_infos.append({"path": rel, "language": lang, "loc": loc})

        if is_python(rel):
            edges += py_import_edges(rel, code)
        elif is_ts(rel):
            edges += ts_import_edges(rel, code)

    # graph & ranking with intelligent dependency analysis
    metrics, json_graph = build_graph(root, file_infos, edges)
    top_files = metrics.get("top_files", [])[:TOP_FILES]
    dependency_analysis = metrics.get("dependency_analysis", {})
    
    # Optional: Enhance dependency analysis with LLM
    if USE_LLM_FOR_DEPENDENCY_ANALYSIS and dependency_analysis:
        try:
            dependency_analysis = enhance_dependency_analysis_with_llm(
                dependency_analysis, language_stats, file_count, top_files
            )
            print("✅ LLM-enhanced dependency analysis completed")
        except Exception as e:
            print(f"⚠️ LLM dependency analysis failed: {e}")
            # Continue with rule-based analysis

    # collect short excerpts for top files
    excerpts = []
    for rel in top_files:
        abs_path = os.path.join(root, rel)
        text = read_text(abs_path, max_bytes=4000)
        # tiny chunk: first ~1200 chars
        snippet = text[:1200]
        excerpts.append((rel, snippet))

    # language stats
    lang_counter = Counter([fi["language"] for fi in file_infos])
    total = sum(lang_counter.values()) or 1
    language_stats = {k: round(v*100/total, 1) for k, v in lang_counter.items()}

    # overview via LLM (one call)
    top_lines = "\n".join([f"- {p}" for p in top_files[:30]])
    ex_str = "\n\n".join([f"<file name=\"{p}\">\n{t}\n</file>" for p, t in excerpts[:12]])
    user_prompt = OVERVIEW_USER_TMPL.format(language_stats=language_stats, top_files=top_lines) + "\n\n" + ex_str
    
    # Don't catch quota errors here - let them bubble up to fail the entire analysis
    architecture_md = generate_markdown(OVERVIEW_SYSTEM, user_prompt)

    # component analysis  
    # Don't catch quota errors here - let them bubble up to fail the entire analysis
    components = extract_components(top_files[:COMPONENT_COUNT], excerpts[:COMPONENT_COUNT])

    # Create multiple diagram variations using intelligent analysis
    # Don't catch quota errors here - let them bubble up to fail the entire analysis
    diagrams = create_intelligent_diagrams(dependency_analysis, json_graph, file_infos, architecture_md)

    # trim metrics for response
    central = []
    for p in top_files[:50]:
        central.append({
            "path": p,
            "fan_in": metrics["fan_in"].get(p, 0),
            "fan_out": metrics["fan_out"].get(p, 0),
            "degree_centrality": round(metrics["degree_centrality"].get(p, 0.0), 4),
        })

    summary = {
        "status": "complete",
        "repo": {"url": repo_url, "commit_sha": sha},
        "language_stats": language_stats,
        "loc_total": sum(fi["loc"] for fi in file_infos),
        "file_count": len(file_infos),
        "metrics": {
            "central_files": central,
            "graph": json_graph,
            "dependency_analysis": dependency_analysis,  # Include dependency analysis
        },
        "components": components,
        "artifacts": {
            "architecture_md": architecture_md,
            **diagrams,  # Include all diagram variations
        },
        "token_budget": {"embed_calls": 0, "gen_calls": 1 + len(components), "chunks": 0},
    }
    return summary


def create_intelligent_diagrams(dependency_analysis: Dict[str, Any], json_graph: Dict[str, Any], file_infos: List[Dict[str, Any]], architecture_md: str) -> Dict[str, str]:
    """Create multiple intelligent diagram variations with optional LLM enhancement"""
    diagrams = {}
    
    # Original backward-compatible diagram
    diagrams["mermaid_modules"] = modules_mermaid(json_graph["edges"])
    
    # Always generate balanced diagram during initial analysis (this is the default view)
    diagrams["mermaid_modules_balanced"] = generate_single_diagram_mode(
        dependency_analysis, json_graph, file_infos, "balanced", architecture_md
    )
    print("✅ Balanced diagram generated during initial analysis (LLM-powered)")
    
    # Overview and detailed will be generated on-demand via API
    # Initialize as empty - they'll be populated when requested
    diagrams["mermaid_modules_simple"] = ""
    diagrams["mermaid_modules_detailed"] = ""
    
    # Folder structure (unchanged)
    diagrams["mermaid_folders"] = folders_mermaid([fi["path"] for fi in file_infos])
    
    return diagrams


def generate_single_diagram_mode(dependency_analysis: Dict[str, Any], json_graph: Dict[str, Any], file_infos: List[Dict[str, Any]], mode: str, architecture_md: str = "") -> str:
    """Generate a single diagram mode with LLM or rule-based fallback"""
    
    # Always use LLM for balanced diagram (primary architectural view)
    if mode == "balanced":
        try:
            return _generate_llm_diagram_mode(dependency_analysis, json_graph, file_infos, mode, architecture_md)
        except GeminiQuotaExhaustedError as e:
            print(f"🚫 LLM balanced diagram generation failed - quota exhausted ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except GeminiAPIError as e:
            print(f"🔧 LLM balanced diagram generation failed - API error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except Exception as e:
            print(f"⚠️ LLM balanced diagram generation failed - unexpected error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
    
    # For other modes, respect the USE_LLM_FOR_DIAGRAMS setting
    if USE_LLM_FOR_DIAGRAMS:
        try:
            # Try LLM-powered generation first
            return _generate_llm_diagram_mode(dependency_analysis, json_graph, file_infos, mode, architecture_md)
        except GeminiQuotaExhaustedError as e:
            print(f"🚫 LLM diagram generation failed for {mode} - quota exhausted ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except GeminiAPIError as e:
            print(f"🔧 LLM diagram generation failed for {mode} - API error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except Exception as e:
            print(f"⚠️ LLM diagram generation failed for {mode} - unexpected error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
    else:
        print(f"📋 Using rule-based diagram generation for {mode}")
        return _generate_rule_based_diagram_mode(dependency_analysis, mode)


def _generate_rule_based_diagram_mode(dependency_analysis: Dict[str, Any], mode: str) -> str:
    """Generate a single diagram mode using rule-based approach"""
    if mode == "simple":
        return intelligent_modules_mermaid(
            dependency_analysis, 
            mode="simple", 
            title="Architecture Overview"
        )
    elif mode == "balanced":
        return intelligent_modules_mermaid(
            dependency_analysis, 
            mode="balanced", 
            title="Module Dependencies (Grouped)"
        )
    elif mode == "detailed":
        return intelligent_modules_mermaid(
            dependency_analysis, 
            mode="detailed", 
            title="Detailed Dependencies"
        )
    else:
        return ""


def _generate_llm_diagram_mode(dependency_analysis: Dict[str, Any], json_graph: Dict[str, Any], file_infos: List[Dict[str, Any]], mode: str, architecture_md: str = "") -> str:
    """Generate a single diagram mode using LLM with enhanced context"""
    
    # Generate folder structure for context
    folder_structure_mermaid = folders_mermaid([fi["path"] for fi in file_infos])
    
    # Extract Component Map and Data Flow sections from architecture_md
    component_map = _extract_markdown_section(architecture_md, "Component Map")
    data_flow = _extract_markdown_section(architecture_md, "Data Flow")
    
    # Prepare enhanced dependency context
    internal_deps_summary = []
    for edge in dependency_analysis.get("internal_edges", [])[:30]:  # Increased limit for better context
        internal_deps_summary.append(f"{edge['src']} -> {edge['dst']}")
    
    external_deps_summary = []
    for category, deps in dependency_analysis.get("external_groups", {}).items():
        dep_count = len(deps)
        sample_deps = [dst for src, dst in deps[:5]]  # More samples for better understanding
        external_deps_summary.append(f"{category} ({dep_count}): {', '.join(sample_deps)}")
    
    # Create enhanced context with architectural insights
    context = {
        "folder_structure": folder_structure_mermaid,
        "component_map": component_map or "No component map available",
        "data_flow": data_flow or "No data flow information available", 
        "internal_dependencies": "\n".join(internal_deps_summary) if internal_deps_summary else "No internal dependencies found",
        "external_dependencies": "\n".join(external_deps_summary) if external_deps_summary else "No external dependencies found",
        "total_files": len(file_infos),
        "dependency_summary": json.dumps(dependency_analysis.get("summary", {}), indent=2),
        "top_files": ", ".join([fi["path"] for fi in file_infos[:15]])  # Top files as comma-separated string
    }
    
    # Use dedicated balanced prompt or general prompt
    if mode == "balanced":
        # Use the special balanced prompt for the best architectural representation
        user_prompt = MERMAID_BALANCED_GENERATION_USER_TMPL.format(**context)
        # Generate LLM-powered Mermaid diagram with balanced-specific system prompt
        llm_diagram = generate_markdown(MERMAID_BALANCED_GENERATION_SYSTEM, user_prompt)
    else:
        # Use the general prompt for overview and detailed modes
        llm_mode = mode  # No mapping needed anymore, just use mode directly
        if mode == "simple":
            llm_mode = "overview"
        elif mode == "detailed":
            llm_mode = "detailed"
        
        # Add mode to context for formatting
        context["mode"] = llm_mode
        user_prompt = MERMAID_GENERATION_USER_TMPL.format(**context)
        # Generate LLM-powered Mermaid diagram
        llm_diagram = generate_markdown(MERMAID_GENERATION_SYSTEM, user_prompt)
    
    # Clean up the response (remove any markdown formatting)
    return extract_mermaid_code(llm_diagram)


def extract_mermaid_code(llm_response: str) -> str:
    """Extract clean Mermaid code from LLM response"""
    # Remove markdown code fences if present
    lines = llm_response.strip().split('\n')
    
    # Find start and end of mermaid code
    start_idx = 0
    end_idx = len(lines)
    
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if start_idx == 0:
                start_idx = i + 1
            else:
                end_idx = i
                break
        elif line.strip().startswith('flowchart') or line.strip().startswith('graph'):
            start_idx = i
            break
    
    # Extract the mermaid code
    mermaid_lines = lines[start_idx:end_idx]
    mermaid_code = '\n'.join(mermaid_lines).strip()
    
    # Ensure it starts with flowchart if it doesn't
    if not (mermaid_code.startswith('flowchart') or mermaid_code.startswith('graph')):
        mermaid_code = 'flowchart LR\n' + mermaid_code
    
    return mermaid_code


def enhance_dependency_analysis_with_llm(
    dependency_analysis: Dict[str, Any], 
    language_stats: Dict[str, float],
    file_count: int,
    top_files: List[str]
) -> Dict[str, Any]:
    """
    Optional: Use LLM to create even more intelligent dependency groupings
    This is a premium feature for complex projects
    """
    try:
        # Format the data for LLM analysis
        internal_deps = []
        for edge in dependency_analysis.get("internal_edges", []):
            internal_deps.append(f"{edge['src']} -> {edge['dst']}")
        
        external_deps = []
        for category, deps in dependency_analysis.get("external_groups", {}).items():
            dep_list = [f"{src} -> {dst}" for src, dst in deps[:5]]  # Limit for context
            external_deps.append(f"{category}: {', '.join(dep_list)}")
        
        # Create prompts
        internal_deps_str = "\n".join(internal_deps[:30])  # Limit for context
        external_deps_str = "\n".join(external_deps)
        top_files_str = ", ".join(top_files[:10])
        
        user_prompt = DEPENDENCY_ANALYSIS_USER_TMPL.format(
            internal_deps=internal_deps_str,
            external_deps=external_deps_str,
            language_stats=language_stats,
            file_count=file_count,
            top_files=top_files_str
        )
        
        # Generate enhanced analysis
        response = generate_markdown(DEPENDENCY_ANALYSIS_SYSTEM, user_prompt)
        
        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith('```'):
            lines = response_clean.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response_clean = '\n'.join(lines)
        
        llm_analysis = json.loads(response_clean)
        
        # Add LLM insights to the existing analysis
        dependency_analysis["llm_insights"] = llm_analysis
        
        return dependency_analysis
        
    except Exception as e:
        # Fallback: return original analysis if LLM fails
        print(f"LLM enhancement failed: {e}")
        return dependency_analysis


def extract_components(top_files: List[str], excerpts: List[tuple]) -> List[Dict[str, Any]]:
    """Extract component analysis using LLM for key files"""
    components = []
    
    if not top_files:
        return components
    
    # Group files by potential components (simple heuristic)
    component_groups = group_files_by_component(top_files)
    
    for group_name, files in component_groups.items():
        if len(files) == 0:
            continue
            
        # Get excerpts for this group
        group_excerpts = [(path, content) for path, content in excerpts if path in files]
        
        if not group_excerpts:
            continue
            
        try:
            # Prepare prompts
            files_str = "\n".join([f"- {f}" for f in files])
            excerpts_str = "\n\n".join([f"<file name=\"{p}\">\n{content[:800]}\n</file>" for p, content in group_excerpts])
            
            user_prompt = COMPONENT_USER_TMPL.format(files=files_str, excerpts=excerpts_str)
            
            # Generate component analysis
            response = generate_markdown(COMPONENT_SYSTEM, user_prompt)
            
            # Parse JSON response directly (improved prompts should give clean JSON)
            response_clean = response.strip()
            
            # Fallback: if response still has markdown, clean it
            if response_clean.startswith('```'):
                lines = response_clean.split('\n')
                # Remove first and last lines if they contain ```
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response_clean = '\n'.join(lines)
            
            component_data = json.loads(response_clean)
            
            # Validate and clean component data
            component = {
                "name": component_data.get("name", group_name),
                "purpose": component_data.get("purpose", ""),
                "key_files": component_data.get("key_files", [{"path": f, "reason": "Core file"} for f in files[:3]]),
                "apis": component_data.get("apis", []),
                "dependencies": component_data.get("dependencies", []),
                "risks": component_data.get("risks", []),
                "tests": component_data.get("tests", [])
            }
            
            components.append(component)
            
        except (GeminiQuotaExhaustedError, GeminiAPIError):
            # Let quota errors bubble up to fail the entire analysis
            raise
        except (json.JSONDecodeError, Exception):
            # General fallback for other errors
            components.append({
                "name": group_name,
                "purpose": f"Component containing {len(files)} key files",
                "key_files": [{"path": f, "reason": "Core file"} for f in files[:3]],
                "apis": [],
                "dependencies": [],
                "risks": ["Analysis incomplete due to processing error"],
                "tests": []
            })
    
    return components


def group_files_by_component(files: List[str]) -> Dict[str, List[str]]:
    """Group files into potential components based on path patterns"""
    components = {}
    
    for file_path in files:
        # Extract component name from path
        parts = file_path.split('/')
        
        if len(parts) >= 2:
            # Use directory structure to group
            if parts[0] in ['src', 'lib', 'app']:
                component_name = parts[1] if len(parts) > 1 else parts[0]
            else:
                component_name = parts[0]
        else:
            component_name = "Core"
        
        # Clean component name
        component_name = component_name.replace('_', ' ').replace('-', ' ').title()
        
        if component_name not in components:
            components[component_name] = []
        components[component_name].append(file_path)
    
    # Limit to most significant components
    sorted_components = sorted(components.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_components[:COMPONENT_COUNT])


def lang_of_ext(ext: str) -> str:
    return {
        ".py": "python",
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
    }.get(ext, "other") 