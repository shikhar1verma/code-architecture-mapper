"""
LangGraph Workflows Package

This package contains the LangGraph-based workflow implementation for 
code architecture analysis. It provides a structured, node-based approach
to replace the existing linear pipeline.
"""

from .graph import (
    AnalysisWorkflow,
    run_analysis_with_langgraph,
    generate_diagram_on_demand,
    fix_diagram_with_subgraph
)
from .state import AnalysisState, DiagramState, AnalysisConfig

__all__ = [
    "AnalysisWorkflow",
    "run_analysis_with_langgraph", 
    "generate_diagram_on_demand",
    "fix_diagram_with_subgraph",
    "AnalysisState",
    "DiagramState", 
    "AnalysisConfig"
]
