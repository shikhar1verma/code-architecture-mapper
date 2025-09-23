"""
Simple Diagram Generation Subgraph

This module implements focused diagram generation for the main analysis workflow.
Correction is handled separately by correction_subgraph.py.
"""

import re
from typing import List
from langgraph.graph import StateGraph, END, START
from backend.config import USE_LLM_FOR_DIAGRAMS
from backend.services.content_generation import ContentGenerationService
from backend.graphing import modules_mermaid, folders_mermaid
from backend.services.pipeline import _generate_rule_based_diagram_mode
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError
from backend.utils.logger import get_logger
from .state import DiagramState

# Minimal imports for generation-only functionality

logger = get_logger(__name__)
content_service = ContentGenerationService()


# Validation functions moved to correction_subgraph.py


def generate_diagram_node(state: DiagramState) -> DiagramState:
    """
    Simple diagram generation node for the main analysis workflow.
    
    This node focuses solely on generation - no correction logic.
    Correction is handled by a separate correction subgraph.
    """
    logger.info(f"🎨 Generating {state['diagram_mode']} diagram")
    
    try:
        if USE_LLM_FOR_DIAGRAMS:
            # LLM-powered generation
            raw_diagram = content_service.generate_llm_diagram(
                state["dependency_analysis"],
                state["json_graph"],
                state["file_infos"],
                state["diagram_mode"],
                state["architecture_markdown"]
            )
            state["raw_diagram"] = raw_diagram
            logger.info("✅ LLM diagram generated")
        else:
            # Rule-based generation
            raw_diagram = _generate_rule_based_diagram_mode(
                state["dependency_analysis"],
                state["diagram_mode"]
            )
            state["raw_diagram"] = raw_diagram
            logger.info("✅ Rule-based diagram generated")
            
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        logger.warning(f"🔧 LLM generation failed: {e}, falling back to rule-based")
        state["raw_diagram"] = _generate_rule_based_diagram_mode(
            state["dependency_analysis"],
            state["diagram_mode"]
        )
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        state["raw_diagram"] = _generate_basic_fallback_diagram(state)
    
    return state


# Note: Validation and correction logic moved to correction_subgraph.py
# This file now focuses only on generation


def finalize_diagram_node(state: DiagramState) -> DiagramState:
    """
    Finalize the diagram - either use validated version or best attempt.
    """
    logger.info(f"🏁 Finalizing {state['diagram_mode']} diagram")
    
    if state["is_valid"] and state["validated_diagram"]:
        final_diagram = state["validated_diagram"]
        logger.info("✅ Using validated diagram")
    else:
        # Use the best attempt we have, even if not perfect
        final_diagram = state["raw_diagram"] or _generate_basic_fallback_diagram(state)
        logger.warning("⚠️ Using best attempt diagram (validation failed)")
    
    # Store in diagrams collection
    mode_key = f"mermaid_modules_{state['diagram_mode']}"
    state["diagrams"][mode_key] = final_diagram
    
    # Also generate folder structure diagram (rule-based, no validation needed)
    if state["diagram_mode"] == "balanced":  # Only once
        folder_diagram = folders_mermaid([fi["path"] for fi in state["file_infos"]])
        state["diagrams"]["mermaid_folders"] = folder_diagram
        
        # Generate backward-compatible diagram
        edges = state["json_graph"].get("edges", [])
        basic_diagram = modules_mermaid(edges)
        state["diagrams"]["mermaid_modules"] = basic_diagram
    
    return state


def create_diagram_subgraph() -> StateGraph:
    """
    Create simple diagram generation subgraph.
    
    Flow: Generate → Finalize
    Correction is handled by a separate correction_subgraph.py
    """
    # Create subgraph
    subgraph = StateGraph(DiagramState)
    
    # Add nodes - simple generation only
    subgraph.add_node("generate", generate_diagram_node)
    subgraph.add_node("finalize", finalize_diagram_node)
    
    # Define simple flow
    subgraph.add_edge(START, "generate")
    subgraph.add_edge("generate", "finalize")
    subgraph.add_edge("finalize", END)
    
    return subgraph.compile()


def _generate_basic_fallback_diagram(state: DiagramState) -> str:
    """Generate a basic fallback diagram when all else fails."""
    try:
        return modules_mermaid(state["json_graph"].get("edges", []))
    except Exception:
        return """graph LR
    A[Repository Analysis] --> B[Architecture Overview]
    B --> C[Component Analysis] 
    B --> D[Dependency Analysis]
    C --> E[Final Report]
    D --> E"""
