"""
Main LangGraph Orchestrator for Code Architecture Analysis

This module creates and manages the main analysis graph that orchestrates
the entire code architecture analysis workflow using LangGraph.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from backend.utils.logger import get_logger
from .state import AnalysisState
from .nodes import (
    core_analysis_node,
    architecture_overview_node,
    components_extraction_node,
    diagram_generation_balanced_node,
    diagram_generation_simple_node,
    diagram_generation_detailed_node,
    parallel_completion_check,
    central_file_summary_node
)

logger = get_logger(__name__)


def create_analysis_graph() -> StateGraph:
    """
    Create the main analysis graph with the following structure:
    
    START -> Core Analysis -> Architecture Overview -> [Components Extraction || Diagram Generation Balanced || Diagram Generation Simple || Diagram Generation Detailed] -> Central File Summary -> END
    
    The workflow is:
    1. Core Analysis (Sequential) - Static analysis of repository
    2. Architecture Overview (Sequential) - LLM-generated overview
    3. Parallel Processing:
       - Components Extraction (Rule-based + LLM)
       - Diagram Generation Balanced (LLM with self-correction subgraph)
       - Diagram Generation Simple (LLM with self-correction subgraph)
       - Diagram Generation Detailed (LLM with self-correction subgraph)
    4. Central File Summary (Sequential) - Final results preparation
    """
    
    # Create the main graph
    graph = StateGraph(AnalysisState)
    
    # Add all nodes
    graph.add_node("core_analysis", core_analysis_node)
    graph.add_node("architecture_overview", architecture_overview_node)
    graph.add_node("components_extraction", components_extraction_node)
    graph.add_node("diagram_generation_balanced", diagram_generation_balanced_node)
    graph.add_node("diagram_generation_simple", diagram_generation_simple_node)
    graph.add_node("diagram_generation_detailed", diagram_generation_detailed_node)
    graph.add_node("parallel_check", parallel_completion_check)
    graph.add_node("final_summary", central_file_summary_node)
    
    # Define the workflow edges
    # Sequential flow: START -> Core Analysis -> Architecture Overview
    graph.add_edge(START, "core_analysis")
    graph.add_edge("core_analysis", "architecture_overview")
    
    # Parallel processing: Architecture Overview -> [Components + 3 Diagram Modes]
    graph.add_edge("architecture_overview", "components_extraction")
    graph.add_edge("architecture_overview", "diagram_generation_balanced")
    graph.add_edge("architecture_overview", "diagram_generation_simple")
    graph.add_edge("architecture_overview", "diagram_generation_detailed")
    
    # Convergence: All parallel tasks -> Completion Check
    graph.add_edge("components_extraction", "parallel_check")
    graph.add_edge("diagram_generation_balanced", "parallel_check")
    graph.add_edge("diagram_generation_simple", "parallel_check")
    graph.add_edge("diagram_generation_detailed", "parallel_check")
    
    # Final processing: Completion Check -> Final Summary -> END
    graph.add_edge("parallel_check", "final_summary")
    graph.add_edge("final_summary", END)
    
    logger.info("✅ Analysis graph structure created successfully")
    return graph.compile()


def initialize_analysis_state(analysis_id: str, repo_url: str, force_refresh: bool = False) -> AnalysisState:
    """
    Initialize the state for a new analysis workflow.
    
    Args:
        analysis_id: Unique identifier for this analysis
        repo_url: Repository URL to analyze
        force_refresh: Whether to force refresh of cached data
    
    Returns:
        Initialized AnalysisState
    """
    return AnalysisState(
        # Input data
        analysis_id=analysis_id,
        repo_url=repo_url,
        force_refresh=force_refresh,
        
        # Core analysis results (Step 1)
        repository_info=None,
        file_infos=None,
        repository_metrics=None,
        metrics_data=None,
        dependency_analysis=None,
        
        # LLM processing data
        top_files=None,
        json_graph=None,
        language_stats=None,
        excerpts=None,
        
        # Architecture overview results (Step 2)
        architecture_markdown=None,
        
        # Parallel processing results (Step 3)
        components=None,
        diagrams=None,
        
        # Final results (Step 4)
        central_files=None,
        final_summary=None,
        
        # Error handling and metadata
        errors=[],
        processing_status="initialized"
    )


class AnalysisWorkflow:
    """
    Main workflow manager for code architecture analysis using LangGraph.
    
    This class provides a high-level interface to run the complete analysis
    workflow and replaces the existing pipeline functionality.
    """
    
    def __init__(self):
        """Initialize the workflow with the compiled graph."""
        self.graph = create_analysis_graph()
        logger.info("🚀 AnalysisWorkflow initialized")
    
    def run_analysis(self, analysis_id: str, repo_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Run complete repository analysis using the LangGraph workflow.
        
        This method maintains the same interface as the original pipeline.run_analysis()
        but uses the new LangGraph-based approach internally.
        
        Args:
            analysis_id: Unique identifier for this analysis
            repo_url: Repository URL to analyze  
            force_refresh: Whether to force refresh of cached data
            
        Returns:
            Dictionary containing complete analysis results
        """
        logger.info(f"🔄 Starting LangGraph analysis for {repo_url}")
        
        try:
            # Initialize state
            initial_state = initialize_analysis_state(analysis_id, repo_url, force_refresh)
            
            # Execute the graph workflow
            final_state = self.graph.invoke(initial_state)
            
            # Extract and return final results
            if final_state["final_summary"]:
                logger.info("✅ LangGraph analysis completed successfully")
                
                # Clean up temporary files (same as pipeline)
                self._cleanup_temporary_files(final_state)
                
                return final_state["final_summary"]
            else:
                logger.error("❌ LangGraph analysis failed - no final summary generated")
                return self._create_error_response(analysis_id, repo_url, final_state["errors"])
                
        except Exception as e:
            logger.error(f"❌ LangGraph analysis failed with exception: {e}")
            return self._create_error_response(analysis_id, repo_url, [str(e)])
    
    def _cleanup_temporary_files(self, final_state: Dict[str, Any]) -> None:
        """Clean up temporary files after analysis completion (same as pipeline)."""
        try:
            import shutil
            import os
            
            repo_root = final_state["repository_info"]["root_path"]
            if os.path.exists(repo_root):
                try:
                    shutil.rmtree(repo_root)
                    logger.info(f"🧹 Cleaned up temporary repository: {repo_root}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup {repo_root}: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up temporary files: {e}")

    def _create_error_response(self, analysis_id: str, repo_url: str, errors: list) -> Dict[str, Any]:
        """Create an error response when analysis fails."""
        return {
            "status": "error",
            "analysis_id": analysis_id,
            "repository": {"url": repo_url},
            "error": "Analysis failed",
            "errors": errors,
            "architecture": {"overview": "", "components": [], "patterns": []},
            "diagrams": {},
            "files": {"central_files": [], "top_files": [], "file_count": 0},
            "dependencies": {},
            "complexity": {}
        }


# Global workflow instance (similar to how services are initialized in pipeline.py)
workflow = AnalysisWorkflow()


def run_analysis_with_langgraph(analysis_id: str, repo_url: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Entry point function that matches the original pipeline.run_analysis() signature.
    
    This function can be used as a drop-in replacement for the existing pipeline.
    """
    return workflow.run_analysis(analysis_id, repo_url, force_refresh)


# Additional utility functions for on-demand diagram generation
def fix_diagram_with_subgraph(analysis_id: str, mode: str, broken_diagram: str, 
                             error_message: str, dependency_analysis: Dict[str, Any],
                             json_graph: Dict[str, Any], file_infos: List[Dict[str, Any]],
                             architecture_md: str = "") -> str:
    """
    Fix a broken Mermaid diagram using the intelligent diagram subgraph.
    
    This function uses the same self-correcting subgraph that's used in the main
    analysis workflow, providing intelligent error detection and correction.
    
    Args:
        analysis_id: Analysis ID for context
        mode: Diagram mode (simple, balanced, detailed)
        broken_diagram: The broken Mermaid diagram code
        error_message: Error message from Mermaid renderer
        dependency_analysis: Dependency analysis data
        json_graph: Graph data structure
        file_infos: List of file information
        architecture_md: Architecture markdown for context
        
    Returns:
        Corrected Mermaid diagram code
    """
    from .diagram_subgraph import create_diagram_subgraph
    from .state import DiagramState
    
    logger = get_logger(__name__)
    logger.info(f"🔧 Fixing diagram with subgraph - Analysis: {analysis_id}, Mode: {mode}")
    
    try:
        # Create initial state for the diagram subgraph
        initial_state: DiagramState = {
            "analysis_id": analysis_id,
            "diagram_mode": mode,
            "dependency_analysis": dependency_analysis,
            "json_graph": json_graph,
            "file_infos": file_infos,
            "architecture_markdown": architecture_md,
            "raw_diagram": broken_diagram,  # Start with the broken diagram
            "current_attempt": 0,
            "max_attempts": 3,  # Allow up to 3 correction attempts
            "validation_errors": [error_message],
            "validation_warnings": [],
            "diagrams": {},  # Initialize diagrams collection
            "validated_diagram": None,
            "is_valid": False
        }
        
        print('Client error message:', error_message)
        
        # Create the diagram subgraph
        diagram_subgraph = create_diagram_subgraph()
        
        # Run the subgraph to fix the diagram
        logger.info("🤖 Running diagram subgraph for intelligent correction...")
        final_state = diagram_subgraph.invoke(initial_state)
        
        # Extract the corrected diagram
        # The subgraph stores the final diagram in the diagrams collection
        mode_key = f"mermaid_modules_{mode}"
        diagrams = final_state.get("diagrams", {})
        corrected_diagram = diagrams.get(mode_key, broken_diagram)
        
        # If not found in diagrams, try raw_diagram as fallback
        if corrected_diagram == broken_diagram:
            corrected_diagram = final_state.get("raw_diagram", broken_diagram)
        
        # Log the results
        validation_errors = final_state.get("validation_errors", [])
        validation_warnings = final_state.get("validation_warnings", [])
        
        logger.info(f"✅ Diagram subgraph completed:")
        logger.info(f"   - Attempts made: {final_state.get('current_attempt', 0)}")
        logger.info(f"   - Validation errors: {len(validation_errors)}")
        logger.info(f"   - Validation warnings: {len(validation_warnings)}")
        
        if validation_errors:
            logger.warning(f"   - Remaining errors: {validation_errors}")
        if validation_warnings:
            logger.info(f"   - Warnings: {validation_warnings}")
        
        return corrected_diagram
        
    except Exception as e:
        logger.error(f"❌ Diagram subgraph fixing failed: {e}")
        # Fallback to the original broken diagram if subgraph fails
        return broken_diagram


def generate_diagram_on_demand(_analysis_id: str, mode: str, dependency_analysis: Dict[str, Any], 
                               json_graph: Dict[str, Any], file_infos: list, 
                               architecture_md: str = "") -> str:
    """
    Generate a single diagram on-demand for specific modes (simple, detailed).
    
    This function supports the existing API endpoints that generate diagrams
    after the initial analysis is complete.
    """
    logger.info(f"📊 Generating on-demand {mode} diagram")
    
    try:
        from .diagram_subgraph import create_diagram_subgraph
        from .state import DiagramState
        
        # Create diagram subgraph
        diagram_graph = create_diagram_subgraph()
        
        # Prepare state for specific mode
        diagram_state: DiagramState = {
            "dependency_analysis": dependency_analysis,
            "json_graph": json_graph,
            "file_infos": file_infos,
            "architecture_markdown": architecture_md,
            "current_attempt": 0,
            "max_attempts": 3,
            "diagram_mode": mode,
            "raw_diagram": None,
            "validated_diagram": None,
            "validation_errors": [],
            "is_valid": False,
            "diagrams": {}
        }
        
        # Execute diagram generation
        result = diagram_graph.invoke(diagram_state)
        
        # Return the specific diagram
        mode_key = f"mermaid_modules_{mode}"
        return result["diagrams"].get(mode_key, "")
        
    except Exception as e:
        logger.error(f"❌ On-demand diagram generation failed: {e}")
        # Fallback to existing pipeline method
        from backend.services.pipeline import generate_single_diagram_mode
        return generate_single_diagram_mode(dependency_analysis, json_graph, file_infos, mode, architecture_md)
