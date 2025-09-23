"""
LangGraph State Models for Code Architecture Analysis

This module defines the state models that are passed between nodes
in the LangGraph workflow for code architecture analysis.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel
import operator


class AnalysisState(TypedDict):
    """
    Main state for the architecture analysis graph.
    Contains all intermediate and final results.
    """
    # Input data
    analysis_id: str
    repo_url: str
    force_refresh: bool
    
    # Core analysis results (Step 1 - Static)
    repository_info: Optional[Dict[str, Any]]
    file_infos: Optional[List[Dict[str, Any]]]
    repository_metrics: Optional[Dict[str, Any]]
    metrics_data: Optional[Dict[str, Any]]
    dependency_analysis: Optional[Dict[str, Any]]
    
    # LLM processing data
    top_files: Optional[List[str]]
    json_graph: Optional[Dict[str, Any]]
    language_stats: Optional[Dict[str, float]]
    excerpts: Optional[List[Tuple[str, str]]]
    
    # Architecture overview results (Step 2 - LLM)
    architecture_markdown: Optional[str]
    
    # Parallel processing results (Step 3)
    components: Optional[List[Dict[str, Any]]]
    diagrams_balanced: Optional[Dict[str, str]]
    diagrams_simple: Optional[Dict[str, str]]
    diagrams_detailed: Optional[Dict[str, str]]
    
    # Legacy diagrams field for backward compatibility
    diagrams: Optional[Dict[str, str]]
    
    # Final results (Step 4)
    central_files: Optional[List[Dict[str, Any]]]
    final_summary: Optional[Dict[str, Any]]
    
    # Error handling
    errors: Annotated[List[str], operator.add]
    
    # Metadata
    processing_status: str  # 'initialized', 'core_complete', 'overview_complete', 'parallel_complete', 'complete'


class DiagramState(TypedDict):
    """
    State for the diagram generation subgraph with self-correction.
    """
    dependency_analysis: Dict[str, Any]
    json_graph: Dict[str, Any]
    file_infos: List[Dict[str, Any]]
    architecture_markdown: str
    
    # Diagram generation attempts
    current_attempt: int
    max_attempts: int
    
    # Current diagram being processed
    diagram_mode: str  # 'balanced', 'simple', 'detailed'
    
    # Generated content
    raw_diagram: Optional[str]
    validated_diagram: Optional[str]
    
    # Validation results
    validation_errors: List[str]
    validation_warnings: List[str]
    is_valid: bool
    
    # Final results
    diagrams: Dict[str, str]


class ComponentExtractionState(BaseModel):
    """
    State for component extraction processing.
    """
    top_files: List[str]
    excerpts: List[Tuple[str, str]]
    extracted_components: Optional[List[Dict[str, Any]]] = None
    extraction_errors: List[str] = []


class DependencyEnhancementState(BaseModel):
    """
    State for optional dependency analysis enhancement.
    """
    dependency_analysis: Dict[str, Any]
    language_stats: Dict[str, float]
    file_count: int
    top_files: List[str]
    enhanced_dependencies: Optional[Dict[str, Any]] = None
    enhancement_successful: bool = False


# Configuration for different analysis modes
class CorrectionState(TypedDict):
    """
    State for the dedicated diagram correction subgraph.
    
    This agent focuses solely on correcting diagram syntax errors through:
    1. Validation (error detection)
    2. Manual fixes (regex-based rule corrections)
    3. LLM correction (intelligent fixes for complex errors)
    4. Final validation (verification)
    """
    
    # Input
    raw_diagram: str                    # The diagram to be corrected
    analysis_id: str                    # For context and logging
    diagram_mode: str                   # simple, balanced, detailed
    
    # Correction process state
    current_attempt: int                # Current correction attempt (1-based)
    max_attempts: int                   # Maximum correction attempts allowed
    
    # Validation results
    validation_errors: List[str]        # Current validation errors
    validation_warnings: List[str]      # Non-blocking warnings
    is_valid: bool                      # Whether diagram is valid
    
    # Correction stages
    manual_fixes_applied: Annotated[List[str], operator.add]     # Manual fixes that were applied
    llm_correction_applied: bool        # Whether LLM correction was used
    
    # Output
    corrected_diagram: Optional[str]    # Final corrected diagram
    correction_success: bool            # Whether correction was successful
    correction_summary: Annotated[List[str], operator.add]       # Summary of corrections applied


class AnalysisConfig(BaseModel):
    """
    Configuration for the analysis workflow.
    """
    top_files_count: int = 50
    component_count: int = 12
    use_llm_for_diagrams: bool = True
    use_llm_for_dependency_analysis: bool = False
    max_diagram_attempts: int = 3
    
    # Diagram modes to generate during initial analysis
    initial_diagram_modes: List[str] = ["balanced"]
    
    # Diagram modes generated on-demand
    on_demand_diagram_modes: List[str] = ["simple", "detailed"]
