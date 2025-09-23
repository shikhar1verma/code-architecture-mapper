"""
Diagram Generation Operations

Handles Mermaid diagram generation and correction for analysis results.
Supports on-demand generation and LLM-powered error correction.
"""

from fastapi import APIRouter, HTTPException

from backend.workflows import generate_diagram_on_demand as langgraph_generate_diagram
from backend.storage.dao import get_analysis, update_analysis_artifact
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError
from backend.utils.logger import get_logger

from .models import MermaidRetryRequest

logger = get_logger(__name__)

router = APIRouter()


@router.post("/analysis/{analysis_id}/diagram/{mode}")
def generate_diagram_on_demand(analysis_id: str, mode: str):
    """Generate a specific diagram mode on-demand and save it to the database"""
    try:
        # Validate mode
        if mode not in ["simple", "balanced", "detailed"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid diagram mode. Only 'simple', 'balanced', and 'detailed' are supported for on-demand generation."
            )
        
        # Get existing analysis
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        dependency_analysis = result.get("metrics", {}).get("dependency_analysis", {})
        if not dependency_analysis:
            raise HTTPException(status_code=404, detail="No dependency analysis available")
        
        # Generate the specific diagram mode
        file_infos = [{"path": f"dummy"} for _ in range(result.get("file_count", 0))]  # Minimal file_infos for LLM context
        json_graph = result.get("metrics", {}).get("graph", {"edges": []})
        architecture_md = result.get("artifacts", {}).get("architecture_md", "")
        
        diagram_content = langgraph_generate_diagram(
            analysis_id,
            mode,
            dependency_analysis, 
            json_graph, 
            file_infos, 
            architecture_md
        )
        
        if not diagram_content:
            raise HTTPException(status_code=500, detail=f"Failed to generate diagram for mode: {mode}")
        
        # Update the database with the new diagram
        diagram_key = f"mermaid_modules_{mode}"
        update_analysis_artifact(analysis_id, diagram_key, diagram_content)
        
        return {
            "mode": mode,
            "diagram": diagram_content,
            "status": "generated"
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        logger.warning(f"🚫 Diagram generation failed due to quota exhaustion: {e}")
        raise HTTPException(status_code=429, detail="quota_exhausted")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/{analysis_id}/diagram/{mode}/retry")
def retry_mermaid_diagram(analysis_id: str, mode: str, request: MermaidRetryRequest):
    """Retry correcting a broken Mermaid diagram using direct LLM correction and save the corrected version to the database"""
    try:
        logger.info(f"🔄 Starting simple LLM Mermaid correction - Analysis: {analysis_id}, Mode: {mode}")
        logger.debug(f"   Concise error: {request.error_message[:100]}{'...' if len(request.error_message) > 100 else ''}")
        logger.debug(f"   Broken code length: {len(request.broken_mermaid_code)}")
        
        # Validate mode
        valid_modes = ["simple", "balanced", "detailed", "folders"]
        if mode not in valid_modes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid diagram mode. Supported modes: {', '.join(valid_modes)}"
            )
        
        # Get existing analysis to verify it exists
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        logger.info(f"🤖 Using dedicated correction subgraph for diagram...")
        
        # Use the specialized correction subgraph
        from backend.workflows.correction_subgraph import correct_diagram
        
        correction_result = correct_diagram(
            raw_diagram=request.broken_mermaid_code,
            analysis_id=analysis_id,
            diagram_mode=mode,
            max_attempts=3
        )
        
        corrected_diagram = correction_result["corrected_diagram"]
        
        if not corrected_diagram or corrected_diagram.strip() == "":
            logger.error(f"❌ LLM correction failed to generate corrected diagram")
            raise HTTPException(status_code=500, detail="Failed to generate corrected diagram")
        
        logger.info(f"✅ Correction subgraph completed - Success: {correction_result['correction_success']}")
        logger.info(f"   - Corrections applied: {len(correction_result['correction_summary'])}")
        logger.info(f"   - Final diagram length: {len(corrected_diagram)}")
        
        # Update the database with the corrected diagram
        diagram_key_mapping = {
            "simple": "mermaid_modules_simple",
            "balanced": "mermaid_modules_balanced", 
            "detailed": "mermaid_modules_detailed",
            "folders": "mermaid_folders"
        }
        
        diagram_key = diagram_key_mapping[mode]
        update_analysis_artifact(analysis_id, diagram_key, corrected_diagram)
        
        logger.info(f"💾 Saved corrected diagram to database with key: {diagram_key}")
        
        return {
            "mode": mode,
            "original_diagram": request.broken_mermaid_code,
            "corrected_diagram": corrected_diagram,
            "status": "corrected_with_subgraph",
            "correction_success": correction_result["correction_success"],
            "corrections_applied": correction_result["correction_summary"],
            "attempts_used": correction_result["current_attempt"]
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        logger.warning(f"🚫 Mermaid correction failed due to LLM error: {e}")
        raise HTTPException(status_code=429, detail="quota_exhausted")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in retry_mermaid_diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))
