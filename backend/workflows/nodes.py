"""
LangGraph Nodes for Code Architecture Analysis

This module contains all the node implementations for the LangGraph workflow.
Each node represents a specific step in the architecture analysis process.
"""

from typing import Dict, Any
from backend.config import TOP_FILES, COMPONENT_COUNT, USE_LLM_FOR_DEPENDENCY_ANALYSIS
from backend.services.analysis.orchestrator import AnalysisOrchestrator  
from backend.services.content_generation import ContentGenerationService
from backend.utils.logger import get_logger
from .state import AnalysisState

# Import progress tracking function
def update_analysis_progress(analysis_id: str, progress_status: str):
    """Update analysis progress status"""
    try:
        from backend.storage.dao import AnalysisDAO
        from backend.database.connection import get_db
        
        db = next(get_db())
        try:
            AnalysisDAO.update_analysis(db, analysis_id, {"progress_status": progress_status})
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️  Failed to update progress for {analysis_id}: {e}")

logger = get_logger(__name__)

# Initialize services (similar to current pipeline)
orchestrator = AnalysisOrchestrator()
content_service = ContentGenerationService()


def core_analysis_node(state: AnalysisState) -> AnalysisState:
    """
    Core Analysis Node (Step 1 - Static Analysis)
    
    Performs:
    - Repository cloning and scanning
    - Dependency extraction 
    - Metrics calculation
    - Complexity analysis
    - Architectural pattern identification
    """
    logger.info(f"🔍 Starting core analysis for {state['repo_url']}")
    
    # Update progress
    update_analysis_progress(state['analysis_id'], "Cloning repository and performing static analysis...")
    
    try:
        # Use existing orchestrator for core analysis
        core_results = orchestrator.perform_core_analysis(state['repo_url'])
        
        # Extract data for next steps
        repository_info = core_results["repository"]
        file_infos = core_results["files"]["file_infos"]
        repository_metrics = core_results["files"]["repository_metrics"] 
        metrics_data = core_results["metrics"]
        dependency_analysis = core_results["dependencies"]["dependency_analysis"]
        
        # Prepare data for LLM processing
        top_files = metrics_data["top_files"][:TOP_FILES]
        json_graph = metrics_data["json_graph"]
        language_stats = repository_metrics["language_stats"]
        
        # Get excerpts for LLM
        excerpts = orchestrator.prepare_excerpts_for_llm(core_results, COMPONENT_COUNT)
        
        # Optional: Enhance dependency analysis with LLM
        if USE_LLM_FOR_DEPENDENCY_ANALYSIS and dependency_analysis:
            try:
                dependency_analysis = content_service.enhance_dependency_analysis(
                    dependency_analysis, language_stats, 
                    repository_metrics["file_count"], top_files
                )
                logger.info("✅ LLM-enhanced dependency analysis completed")
            except Exception as e:
                logger.warning(f"⚠️ LLM dependency analysis failed: {e}")
                state["errors"].append(f"Dependency enhancement failed: {e}")
        
        # Update state with core analysis results
        state.update({
            "repository_info": repository_info,
            "file_infos": file_infos,
            "repository_metrics": repository_metrics,
            "metrics_data": metrics_data,
            "dependency_analysis": dependency_analysis,
            "top_files": top_files,
            "json_graph": json_graph,
            "language_stats": language_stats,
            "excerpts": excerpts,
            "processing_status": "core_complete"
        })
        
        logger.info("✅ Core analysis completed successfully")
        return state
        
    except Exception as e:
        error_msg = f"Core analysis failed: {e}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state


def architecture_overview_node(state: AnalysisState) -> AnalysisState:
    """
    Architecture Overview Node (Step 2 - LLM)
    
    Generates architectural markdown overview using LLM.
    Sequential node that depends on core analysis.
    """
    logger.info("📝 Generating architecture overview")
    
    # Update progress
    update_analysis_progress(state['analysis_id'], "Generating architecture overview using AI...")
    
    try:
        # Generate architecture overview using existing content service
        architecture_md = content_service.generate_architecture_overview(
            state["language_stats"], 
            state["top_files"][:30], 
            state["excerpts"][:12]
        )
        
        state.update({
            "architecture_markdown": architecture_md,
            "processing_status": "overview_complete"
        })
        
        logger.info("✅ Architecture overview generated successfully")
        return state
        
    except Exception as e:
        error_msg = f"Architecture overview generation failed: {e}"
        logger.error(error_msg) 
        state["errors"].append(error_msg)
        return state


def components_extraction_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Components Extraction Node (Step 3a - Parallel)
    
    Extracts and analyzes components using rule-based + LLM approach.
    Can run in parallel with diagram generation.
    """
    logger.info("🧩 Extracting components")
    
    # Update progress
    update_analysis_progress(state['analysis_id'], "Extracting and analyzing code components...")
    
    try:
        # Extract components using existing content service
        components = content_service.extract_components(
            state["top_files"][:COMPONENT_COUNT], 
            state["excerpts"][:COMPONENT_COUNT]
        )
        
        logger.info(f"✅ Extracted {len(components)} components successfully")
        return {"components": components}
        
    except Exception as e:
        error_msg = f"Component extraction failed: {e}"
        logger.error(error_msg)
        # Return error message - LangGraph will add it to the errors list
        return {"errors": [error_msg]}


def diagram_generation_balanced_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Diagram Generation Node for Balanced Mode (Step 3b - Parallel)
    
    Generates balanced diagrams with self-correction.
    Runs in parallel with other diagram modes and component extraction.
    """
    logger.info("📊 Generating balanced diagrams")
    
    try:
        # Import here to avoid circular imports
        from .diagram_subgraph import create_diagram_subgraph
        
        # Create the diagram subgraph
        diagram_graph = create_diagram_subgraph()
        
        # Prepare diagram state
        from .state import DiagramState
        diagram_state: DiagramState = {
            "dependency_analysis": state["dependency_analysis"],
            "json_graph": state["json_graph"],
            "file_infos": state["file_infos"],
            "architecture_markdown": state["architecture_markdown"],
            "current_attempt": 0,
            "max_attempts": 3,
            "diagram_mode": "balanced",
            "raw_diagram": None,
            "validated_diagram": None,
            "validation_errors": [],
            "validation_warnings": [],
            "is_valid": False,
            "diagrams": {}
        }
        
        # Execute diagram subgraph
        result = diagram_graph.invoke(diagram_state)
        
        logger.info("✅ Balanced diagrams generated successfully")
        return {"diagrams_balanced": result["diagrams"]}
        
    except Exception as e:
        error_msg = f"Balanced diagram generation failed: {e}"
        logger.error(error_msg)
        
        # Fallback to basic diagrams
        logger.info("🔧 Falling back to basic balanced diagram generation")
        try:
            from backend.services.pipeline import create_intelligent_diagrams
            basic_diagrams = create_intelligent_diagrams(
                state["dependency_analysis"],
                state["json_graph"],
                state["file_infos"],
                state["architecture_markdown"]
            )
            return {
                "diagrams_balanced": basic_diagrams,
                "errors": [error_msg]
            }
        except Exception as fallback_e:
            fallback_error = f"Fallback balanced diagram generation failed: {fallback_e}"
            return {
                "diagrams_balanced": {},
                "errors": [error_msg, fallback_error]
            }


def diagram_generation_simple_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Diagram Generation Node for Simple Mode (Step 3b - Parallel)
    
    Generates simple overview diagrams with self-correction.
    Runs in parallel with other diagram modes and component extraction.
    """
    logger.info("📊 Generating simple diagrams")
    
    try:
        # Import here to avoid circular imports
        from .diagram_subgraph import create_diagram_subgraph
        
        # Create the diagram subgraph
        diagram_graph = create_diagram_subgraph()
        
        # Prepare diagram state
        from .state import DiagramState
        diagram_state: DiagramState = {
            "dependency_analysis": state["dependency_analysis"],
            "json_graph": state["json_graph"],
            "file_infos": state["file_infos"],
            "architecture_markdown": state["architecture_markdown"],
            "current_attempt": 0,
            "max_attempts": 3,
            "diagram_mode": "simple",
            "raw_diagram": None,
            "validated_diagram": None,
            "validation_errors": [],
            "validation_warnings": [],
            "is_valid": False,
            "diagrams": {}
        }
        
        # Execute diagram subgraph
        result = diagram_graph.invoke(diagram_state)
        
        logger.info("✅ Simple diagrams generated successfully")
        return {"diagrams_simple": result["diagrams"]}
        
    except Exception as e:
        error_msg = f"Simple diagram generation failed: {e}"
        logger.error(error_msg)
        
        # Fallback to basic diagrams
        logger.info("🔧 Falling back to basic simple diagram generation")
        try:
            from backend.services.pipeline import create_intelligent_diagrams
            basic_diagrams = create_intelligent_diagrams(
                state["dependency_analysis"],
                state["json_graph"],
                state["file_infos"],
                state["architecture_markdown"]
            )
            return {
                "diagrams_simple": basic_diagrams,
                "errors": [error_msg]
            }
        except Exception as fallback_e:
            fallback_error = f"Fallback simple diagram generation failed: {fallback_e}"
            return {
                "diagrams_simple": {},
                "errors": [error_msg, fallback_error]
            }


def diagram_generation_detailed_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Diagram Generation Node for Detailed Mode (Step 3b - Parallel)
    
    Generates detailed diagrams with self-correction.
    Runs in parallel with other diagram modes and component extraction.
    """
    logger.info("📊 Generating detailed diagrams")
    
    try:
        # Import here to avoid circular imports
        from .diagram_subgraph import create_diagram_subgraph
        
        # Create the diagram subgraph
        diagram_graph = create_diagram_subgraph()
        
        # Prepare diagram state
        from .state import DiagramState
        diagram_state: DiagramState = {
            "dependency_analysis": state["dependency_analysis"],
            "json_graph": state["json_graph"],
            "file_infos": state["file_infos"],
            "architecture_markdown": state["architecture_markdown"],
            "current_attempt": 0,
            "max_attempts": 3,
            "diagram_mode": "detailed",
            "raw_diagram": None,
            "validated_diagram": None,
            "validation_errors": [],
            "validation_warnings": [],
            "is_valid": False,
            "diagrams": {}
        }
        
        # Execute diagram subgraph
        result = diagram_graph.invoke(diagram_state)
        
        logger.info("✅ Detailed diagrams generated successfully")
        return {"diagrams_detailed": result["diagrams"]}
        
    except Exception as e:
        error_msg = f"Detailed diagram generation failed: {e}"
        logger.error(error_msg)
        
        # Fallback to basic diagrams
        logger.info("🔧 Falling back to basic detailed diagram generation")
        try:
            from backend.services.pipeline import create_intelligent_diagrams
            basic_diagrams = create_intelligent_diagrams(
                state["dependency_analysis"],
                state["json_graph"],
                state["file_infos"],
                state["architecture_markdown"]
            )
            return {
                "diagrams_detailed": basic_diagrams,
                "errors": [error_msg]
            }
        except Exception as fallback_e:
            fallback_error = f"Fallback detailed diagram generation failed: {fallback_e}"
            return {
                "diagrams_detailed": {},
                "errors": [error_msg, fallback_error]
            }


def diagram_generation_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Diagram Generation Node (Step 3b - Parallel)
    
    Generates intelligent diagrams with self-correction.
    Can run in parallel with component extraction.
    
    This node will invoke the diagram subgraph for self-correcting behavior.
    """
    logger.info("📊 Generating intelligent diagrams")
    
    # Update progress
    update_analysis_progress(state['analysis_id'], "Generating dependency diagrams using AI...")
    
    try:
        # Import here to avoid circular imports
        from .diagram_subgraph import create_diagram_subgraph
        
        # Create the diagram subgraph
        diagram_graph = create_diagram_subgraph()
        
        # Prepare diagram state
        from .state import DiagramState
        diagram_state: DiagramState = {
            "dependency_analysis": state["dependency_analysis"],
            "json_graph": state["json_graph"],
            "file_infos": state["file_infos"],
            "architecture_markdown": state["architecture_markdown"],
            "current_attempt": 0,
            "max_attempts": 3,
            "diagram_mode": "balanced",
            "raw_diagram": None,
            "validated_diagram": None,
            "validation_errors": [],
            "is_valid": False,
            "diagrams": {}
        }
        
        # Execute diagram subgraph
        result = diagram_graph.invoke(diagram_state)
        
        logger.info("✅ Intelligent diagrams generated successfully")
        return {"diagrams": result["diagrams"]}
        
    except Exception as e:
        error_msg = f"Diagram generation failed: {e}"
        logger.error(error_msg)
        
        # Fallback to basic diagrams
        logger.info("🔧 Falling back to basic diagram generation")
        try:
            from backend.services.pipeline import create_intelligent_diagrams
            basic_diagrams = create_intelligent_diagrams(
                state["dependency_analysis"], 
                state["json_graph"], 
                state["file_infos"],
                state["architecture_markdown"]
            )
            return {
                "diagrams": basic_diagrams,
                "errors": [error_msg]
            }
        except Exception as fallback_e:
            fallback_error = f"Fallback diagram generation failed: {fallback_e}"
            return {
                "diagrams": {},
                "errors": [error_msg, fallback_error]
            }


def parallel_completion_check(state: AnalysisState) -> AnalysisState:
    """
    Check if all parallel nodes (components + 3 diagram modes) are complete.
    This is a coordination node that waits for parallel processing to finish.
    """
    logger.info("🔄 Checking parallel processing completion")
    
    # Check if all parallel tasks have results
    components_complete = state.get("components") is not None
    diagrams_balanced_complete = state.get("diagrams_balanced") is not None
    diagrams_simple_complete = state.get("diagrams_simple") is not None
    diagrams_detailed_complete = state.get("diagrams_detailed") is not None
    
    all_complete = (
        components_complete and 
        diagrams_balanced_complete and 
        diagrams_simple_complete and 
        diagrams_detailed_complete
    )
    
    if all_complete:
        state["processing_status"] = "parallel_complete"
        logger.info("✅ All parallel processing completed")
        
        # Consolidate all diagrams into the legacy diagrams field for backward compatibility
        consolidated_diagrams = {}
        if state.get("diagrams_balanced"):
            consolidated_diagrams.update(state["diagrams_balanced"])
        if state.get("diagrams_simple"):
            consolidated_diagrams.update(state["diagrams_simple"])
        if state.get("diagrams_detailed"):
            consolidated_diagrams.update(state["diagrams_detailed"])
        
        state["diagrams"] = consolidated_diagrams
        logger.info(f"📊 Consolidated {len(consolidated_diagrams)} diagrams from all modes")
        
    else:
        logger.info(f"⏳ Parallel processing status:")
        logger.info(f"  - Components: {components_complete}")
        logger.info(f"  - Diagrams Balanced: {diagrams_balanced_complete}")
        logger.info(f"  - Diagrams Simple: {diagrams_simple_complete}")
        logger.info(f"  - Diagrams Detailed: {diagrams_detailed_complete}")
    
    return state


def central_file_summary_node(state: AnalysisState) -> AnalysisState:
    """
    Central File Summary Node (Step 4 - Final)
    
    Creates final file summary and prepares complete response.
    This is the final node in the workflow.
    """
    logger.info("📋 Creating central file summary")
    
    # Update progress
    update_analysis_progress(state['analysis_id'], "Finalizing analysis and generating summary...")
    
    try:
        # Generate central files summary using orchestrator
        central_files = orchestrator.metrics_service.get_central_files_summary(
            state["metrics_data"], 50
        )
        
        # Prepare final summary (matching pipeline format exactly)
        final_summary = {
            "status": "complete",
            "repo": {
                "url": state["repo_url"], 
                "commit_sha": state["repository_info"]["commit_sha"]
            },
            "language_stats": state["language_stats"],
            "loc_total": state["repository_metrics"]["loc_total"],
            "file_count": state["repository_metrics"]["file_count"],
            "metrics": {
                "central_files": central_files,
                "graph": state["json_graph"],
                "dependency_analysis": state["dependency_analysis"],
            },
            "components": state["components"],
            "artifacts": {
                "architecture_md": state["architecture_markdown"],
                **state["diagrams"],  # Include all diagram variations
            },
            "token_budget": {
                "embed_calls": 0, 
                "gen_calls": 1 + len(state["components"] or []), 
                "chunks": 0
            },
        }
        
        state.update({
            "central_files": central_files,
            "final_summary": final_summary,
            "processing_status": "complete"
        })
        
        logger.info("✅ Analysis workflow completed successfully")
        return state
        
    except Exception as e:
        error_msg = f"Final summary generation failed: {e}"
        logger.error(error_msg)
        state["errors"].append(error_msg)
        return state
