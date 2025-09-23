from typing import Dict, Any, List

from backend.config import TOP_FILES, COMPONENT_COUNT, USE_LLM_FOR_DIAGRAMS, USE_LLM_FOR_DEPENDENCY_ANALYSIS
from backend.services.analysis.orchestrator import AnalysisOrchestrator
from backend.services.content_generation import ContentGenerationService
from backend.graphing import modules_mermaid, folders_mermaid, intelligent_modules_mermaid
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize services for analysis
orchestrator = AnalysisOrchestrator()
content_service = ContentGenerationService()


def run_analysis(analysis_id: str, repo_url: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Run complete repository analysis using orchestrator for core analysis and LLM for content generation.
    
    This function maintains the same interface as before but internally uses the new service architecture
    for better separation of concerns and maintainability.
    """
    # STEP 1: Core Analysis using Orchestrator (replaces lines 35-84 of original)
    # This handles: repo cloning, file scanning, dependency extraction, metrics calculation
    core_results = orchestrator.perform_core_analysis(repo_url)
    
    # Extract data for LLM processing (same structure as before)
    repo_info = core_results["repository"]
    file_infos = core_results["files"]["file_infos"]
    repository_metrics = core_results["files"]["repository_metrics"]
    metrics_data = core_results["metrics"]
    dependency_analysis = core_results["dependencies"]["dependency_analysis"]
    
    # Get key variables for LLM processing
    top_files = metrics_data["top_files"][:TOP_FILES]
    json_graph = metrics_data["json_graph"]
    language_stats = repository_metrics["language_stats"]
    
    # STEP 2: Extract file excerpts for LLM (replaces lines 72-79 of original)
    excerpts = orchestrator.prepare_excerpts_for_llm(core_results, COMPONENT_COUNT)

    # Optional: Enhance dependency analysis with LLM
    if USE_LLM_FOR_DEPENDENCY_ANALYSIS and dependency_analysis:
        try:
            dependency_analysis = content_service.enhance_dependency_analysis(
                dependency_analysis, language_stats, repository_metrics["file_count"], top_files
            )
            logger.info("✅ LLM-enhanced dependency analysis completed")
        except Exception as e:
            logger.warning(f"⚠️ LLM dependency analysis failed: {e}")
            # Continue with rule-based analysis

    # STEP 3: LLM Content Generation using ContentGenerationService
    # Generate architecture overview using content service
    architecture_md = content_service.generate_architecture_overview(
        language_stats, top_files[:30], excerpts[:12]
    )

    # Generate component analysis using content service
    components = content_service.extract_components(top_files[:COMPONENT_COUNT], excerpts[:COMPONENT_COUNT])

    # Create multiple diagram variations using intelligent analysis
    # Don't catch quota errors here - let them bubble up to fail the entire analysis
    diagrams = create_intelligent_diagrams(dependency_analysis, json_graph, file_infos, architecture_md)

    # STEP 4: Prepare final response (unchanged from original)
    # trim metrics for response - use orchestrator's helper method
    central_files = orchestrator.metrics_service.get_central_files_summary(metrics_data, 50)

    summary = {
        "status": "complete",
        "repo": {"url": repo_url, "commit_sha": repo_info["commit_sha"]},
        "language_stats": language_stats,
        "loc_total": repository_metrics["loc_total"],
        "file_count": repository_metrics["file_count"],
        "metrics": {
            "central_files": central_files,
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
    
    # Clean up temporary files
    orchestrator.cleanup_temporary_files(core_results)
    
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
    logger.info("✅ Balanced diagram generated during initial analysis (LLM-powered)")
    
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
            return content_service.generate_llm_diagram(dependency_analysis, json_graph, file_infos, mode, architecture_md)
        except GeminiQuotaExhaustedError as e:
            logger.warning(f"🚫 LLM balanced diagram generation failed - quota exhausted ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except GeminiAPIError as e:
            logger.warning(f"🔧 LLM balanced diagram generation failed - API error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except Exception as e:
            logger.warning(f"⚠️ LLM balanced diagram generation failed - unexpected error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
    
    # For other modes, respect the USE_LLM_FOR_DIAGRAMS setting
    if USE_LLM_FOR_DIAGRAMS:
        try:
            # Try LLM-powered generation first using content service
            return content_service.generate_llm_diagram(dependency_analysis, json_graph, file_infos, mode, architecture_md)
        except GeminiQuotaExhaustedError as e:
            logger.warning(f"🚫 LLM diagram generation failed for {mode} - quota exhausted ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except GeminiAPIError as e:
            logger.warning(f"🔧 LLM diagram generation failed for {mode} - API error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
        except Exception as e:
            logger.warning(f"⚠️ LLM diagram generation failed for {mode} - unexpected error ({e})")
            return _generate_rule_based_diagram_mode(dependency_analysis, mode)
    else:
        logger.info(f"📋 Using rule-based diagram generation for {mode}")
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

