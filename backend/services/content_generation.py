"""
Content Generation Service

Handles all LLM-powered content generation including:
- Architecture overview generation
- Component extraction and analysis  
- Diagram generation with LLM enhancement
- Dependency analysis enhancement

Extracted from pipeline.py to improve separation of concerns.
"""

import json
import re
from typing import Dict, Any, List, Tuple

from backend.config import COMPONENT_COUNT
from backend.graphing import folders_mermaid
from backend.llm.gemini import generate_markdown, GeminiQuotaExhaustedError, GeminiAPIError
from backend.llm.prompts import (
    OVERVIEW_SYSTEM, OVERVIEW_USER_TMPL,
    COMPONENT_SYSTEM, COMPONENT_USER_TMPL,
    DEPENDENCY_ANALYSIS_SYSTEM, DEPENDENCY_ANALYSIS_USER_TMPL,
    MERMAID_GENERATION_SYSTEM, MERMAID_GENERATION_USER_TMPL,
    # New ChatGPT improved prompts
    MERMAID_OVERVIEW_SYSTEM_NEW, MERMAID_OVERVIEW_USER_TMPL_NEW,
    MERMAID_BALANCED_SYSTEM_NEW, MERMAID_BALANCED_USER_TMPL_NEW,
    MERMAID_DETAILED_SYSTEM_NEW, MERMAID_DETAILED_USER_TMPL_NEW,
    MERMAID_CORRECTION_SYSTEM, MERMAID_CORRECTION_USER_TMPL
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ContentGenerationService:
    """
    Simple service for LLM-powered content generation
    
    Handles architecture overview, component extraction, and diagram generation
    without complex abstractions or over-engineering.
    """
    
    def generate_architecture_overview(self, language_stats: Dict[str, float], 
                                     top_files: List[str], excerpts: List[Tuple[str, str]]) -> str:
        """
        Generate architecture overview markdown using LLM
        
        Args:
            language_stats: Language distribution statistics
            top_files: List of most important files
            excerpts: List of (file_path, content) tuples
            
        Returns:
            Generated architecture markdown
        """
        top_lines = "\n".join([f"- {p}" for p in top_files[:30]])
        ex_str = "\n\n".join([f"<file name=\"{p}\">\n{t}\n</file>" for p, t in excerpts[:12]])
        user_prompt = OVERVIEW_USER_TMPL.format(language_stats=language_stats, top_files=top_lines) + "\n\n" + ex_str
        
        return generate_markdown(OVERVIEW_SYSTEM, user_prompt)
    
    def extract_components(self, top_files: List[str], excerpts: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Extract component analysis using LLM for key files
        
        Args:
            top_files: List of most important files
            excerpts: List of (file_path, content) tuples
            
        Returns:
            List of component analysis dictionaries
        """
        components = []
        
        if not top_files:
            return components
        
        # Group files by potential components (simple heuristic)
        component_groups = self._group_files_by_component(top_files)
        
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
                
                # Parse JSON response
                response_clean = self._clean_json_response(response)
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
    
    def generate_llm_diagram(self, dependency_analysis: Dict[str, Any], json_graph: Dict[str, Any], 
                           file_infos: List[Dict[str, Any]], mode: str, architecture_md: str = "") -> str:
        """
        Generate LLM-powered diagrams with enhanced context
        
        Args:
            dependency_analysis: Dependency analysis data
            json_graph: Graph data structure
            file_infos: List of file information
            mode: Diagram mode (simple, balanced, detailed)
            architecture_md: Architecture markdown for context
            
        Returns:
            Generated Mermaid diagram code
        """
        # Generate folder structure for context
        folder_structure_mermaid = folders_mermaid([fi["path"] for fi in file_infos])
        
        # Extract Component Map and Data Flow sections from architecture_md
        component_map = self._extract_markdown_section(architecture_md, "Component Map")
        data_flow = self._extract_markdown_section(architecture_md, "Data Flow")
        
        # Prepare enhanced dependency context
        internal_deps_summary = []
        for edge in dependency_analysis.get("internal_edges", [])[:30]:
            internal_deps_summary.append(f"{edge['src']} -> {edge['dst']}")
        
        external_deps_summary = []
        for category, deps in dependency_analysis.get("external_groups", {}).items():
            dep_count = len(deps)
            # Handle both tuple format (legacy) and dict format (new hybrid approach)
            sample_deps = []
            for dep in deps[:5]:
                if isinstance(dep, dict):
                    sample_deps.append(dep["dst"])
                else:
                    # Legacy tuple format (src, dst)
                    sample_deps.append(dep[1])
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
            "top_files": ", ".join([fi["path"] for fi in file_infos[:15]])
        }
        
        # Use mode-specific prompts for better results (ChatGPT improved)
        if mode == "simple":
            # Overview mode - high-level architecture for non-technical stakeholders
            user_prompt = MERMAID_OVERVIEW_USER_TMPL_NEW.format(**context)
            llm_diagram = generate_markdown(MERMAID_OVERVIEW_SYSTEM_NEW, user_prompt)
        elif mode == "balanced":
            # Balanced mode - organized modules for technical stakeholders
            user_prompt = MERMAID_BALANCED_USER_TMPL_NEW.format(**context)
            llm_diagram = generate_markdown(MERMAID_BALANCED_SYSTEM_NEW, user_prompt)
        elif mode == "detailed":
            # Detailed mode - individual modules for hardcore developers
            user_prompt = MERMAID_DETAILED_USER_TMPL_NEW.format(**context)
            llm_diagram = generate_markdown(MERMAID_DETAILED_SYSTEM_NEW, user_prompt)
        else:
            # Fallback to general prompt for unknown modes
            context["mode"] = mode
            user_prompt = MERMAID_GENERATION_USER_TMPL.format(**context)
            llm_diagram = generate_markdown(MERMAID_GENERATION_SYSTEM, user_prompt)
        
        # Clean up the response
        return self._extract_mermaid_code(llm_diagram)
    
    def correct_llm_diagram(self, broken_diagram: str, validation_errors: List[str]) -> str:
        """
        Correct a broken Mermaid diagram using LLM with specific error details
        
        Args:
            broken_diagram: The diagram with syntax errors
            validation_errors: List of specific validation error messages
            
        Returns:
            Corrected Mermaid diagram code
        """
        # Combine all validation errors into a comprehensive error message
        error_message = "\n".join([f"- {error}" for error in validation_errors])
        
        # Use the correction prompt
        user_prompt = MERMAID_CORRECTION_USER_TMPL.format(
            broken_mermaid_code=broken_diagram,
            error_message=error_message
        )
        
        # Generate corrected diagram
        corrected_diagram = generate_markdown(MERMAID_CORRECTION_SYSTEM, user_prompt)
        
        # Clean up the response
        return self._extract_mermaid_code(corrected_diagram)
    
    def enhance_dependency_analysis(self, dependency_analysis: Dict[str, Any], 
                                  language_stats: Dict[str, float],
                                  file_count: int, top_files: List[str]) -> Dict[str, Any]:
        """
        Enhance dependency analysis with LLM insights
        
        Args:
            dependency_analysis: Original dependency analysis
            language_stats: Language distribution statistics
            file_count: Total number of files
            top_files: List of most important files
            
        Returns:
            Enhanced dependency analysis with LLM insights
        """
        try:
            # Format the data for LLM analysis
            internal_deps = []
            for edge in dependency_analysis.get("internal_edges", []):
                internal_deps.append(f"{edge['src']} -> {edge['dst']}")
            
            external_deps = []
            for category, deps in dependency_analysis.get("external_groups", {}).items():
                dep_list = [f"{src} -> {dst}" for src, dst in deps[:5]]
                external_deps.append(f"{category}: {', '.join(dep_list)}")
            
            # Create prompts
            internal_deps_str = "\n".join(internal_deps[:30])
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
            response_clean = self._clean_json_response(response)
            llm_analysis = json.loads(response_clean)
            
            # Add LLM insights to the existing analysis
            dependency_analysis["llm_insights"] = llm_analysis
            
            return dependency_analysis
            
        except Exception as e:
            # Fallback: return original analysis if LLM fails
            logger.warning(f"LLM enhancement failed: {e}")
            return dependency_analysis
    
    def _group_files_by_component(self, files: List[str]) -> Dict[str, List[str]]:
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
    
    def _extract_markdown_section(self, markdown_text: str, section_name: str) -> str:
        """Extract a specific section from markdown text"""
        if not markdown_text:
            return ""
        
        # Pattern to match section headers (## Section Name)
        pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\n#|\Z)"
        match = re.search(pattern, markdown_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_mermaid_code(self, llm_response: str) -> str:
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
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from LLM (remove markdown formatting)"""
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
        
        return response_clean 