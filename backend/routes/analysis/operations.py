"""
Core Analysis Operations

Handles analysis lifecycle: start, refresh, and retrieve operations.
Includes both backward compatibility endpoints and new API endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from backend.workflows import run_analysis_with_langgraph
from backend.storage.dao import (
    save_analysis_summary, get_analysis, 
    get_existing_analysis_by_url, update_existing_analysis_data,
    generate_unique_analysis_id, AnalysisDAO
)
from backend.database.connection import get_db
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError
from backend.utils.logger import get_logger

from .models import StartAnalysisRequest, StartAnalysisResponse, AnalysisStatusResponse

logger = get_logger(__name__)

router = APIRouter()


def create_pending_analysis(repo_url: str, analysis_id: str) -> Dict[str, Any]:
    """Create a new analysis record with pending status"""
    db = next(get_db())
    try:
        analysis_data = {
            "repo_url": repo_url,
            "status": "pending",
            "progress_status": "Analysis request received, preparing to start..."
        }
        
        analysis = AnalysisDAO.create_analysis(db, analysis_data, analysis_id)
        return {
            "analysis_id": str(analysis.id),
            "status": analysis.status,
            "progress_status": analysis.progress_status
        }
    finally:
        db.close()


def update_analysis_status(analysis_id: str, status: str, progress_status: str = None):
    """Update analysis status and progress"""
    db = next(get_db())
    try:
        updates = {"status": status}
        if progress_status:
            updates["progress_status"] = progress_status
        
        AnalysisDAO.update_analysis(db, analysis_id, updates)
        logger.info(f"📊 Updated analysis {analysis_id}: {status} - {progress_status}")
    except Exception as e:
        logger.error(f"❌ Failed to update analysis status {analysis_id}: {e}")
    finally:
        db.close()


def run_analysis_background_task(analysis_id: str, repo_url: str, force_refresh: bool = False):
    """Background task to run analysis with progress tracking"""
    try:
        logger.info(f"🚀 Starting background analysis for {analysis_id}")
        
        # Update status to started
        update_analysis_status(analysis_id, "started", "Analysis started, cloning repository...")
        
        # Run the actual analysis
        result = run_analysis_with_langgraph(analysis_id, repo_url, force_refresh)
        
        # Update with completion status
        update_analysis_status(analysis_id, "completed", "Analysis completed successfully!")
        
        # Save the full analysis results
        save_analysis_summary(analysis_id, result)
        
        logger.info(f"✅ Background analysis completed for {analysis_id}")
        
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        logger.warning(f"🚫 Background analysis failed due to quota exhaustion: {e}")
        update_analysis_status(analysis_id, "failed", "Analysis failed: AI service quota exhausted")
        
    except Exception as e:
        logger.error(f"❌ Background analysis failed for {analysis_id}: {e}")
        update_analysis_status(analysis_id, "failed", f"Analysis failed: {str(e)}")


@router.post("/analysis/start", response_model=StartAnalysisResponse)
def start_analysis_endpoint(req: StartAnalysisRequest, background_tasks: BackgroundTasks):
    """
    ASYNC API: Start a new repository analysis with polling support
    - If completed analysis exists for the repo URL, returns it immediately
    - If pending/started analysis exists, returns the request ID for polling
    - If no analysis exists, creates new request and starts background analysis
    """
    try:
        # Check if analysis already exists for this repo URL
        existing = get_existing_analysis_by_url(str(req.repo_url))
        
        if existing:
            status = existing["status"]
            
            # If completed, return immediately with cached result
            if status == "completed":
                logger.info(f"📋 Found existing completed analysis for {req.repo_url}: {existing['analysis_id']}")
                return StartAnalysisResponse(
                    analysis_id=existing["analysis_id"],
                    status="completed",
                    cached=True,
                    cached_at=existing["updated_at"] or existing["created_at"]
                )
            
            # If pending or started, return the existing request ID
            elif status in ["pending", "started"]:
                logger.info(f"🔄 Found existing {status} analysis for {req.repo_url}: {existing['analysis_id']}")
                return StartAnalysisResponse(
                    analysis_id=existing["analysis_id"],
                    status=status,
                    cached=False
                )
            
            # If failed, create a new analysis (retry)
            elif status == "failed":
                logger.info(f"🔄 Previous analysis failed for {req.repo_url}, creating new one")
        
        # No existing analysis found or previous failed - create new analysis
        analysis_id = generate_unique_analysis_id()
        logger.info(f"🆕 Creating new async analysis for {req.repo_url} with ID: {analysis_id}")
        
        # Create pending analysis record
        create_pending_analysis(str(req.repo_url), analysis_id)
        
        # Start background analysis task
        background_tasks.add_task(
            run_analysis_background_task, 
            analysis_id, 
            str(req.repo_url), 
            force_refresh=False
        )
        
        return StartAnalysisResponse(
            analysis_id=analysis_id,
            status="pending",
            cached=False
        )
    
    except Exception as e:
        logger.error(f"❌ Analysis start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/refresh", response_model=StartAnalysisResponse)
def refresh_analysis_endpoint(req: StartAnalysisRequest):
    """
    NEW API: Enhanced refresh endpoint that takes repo_url
    Refresh an existing repository analysis
    """
    try:
        # Check if analysis exists
        existing = get_existing_analysis_by_url(str(req.repo_url))
        if not existing:
            raise HTTPException(
                status_code=404, 
                detail="No previous analysis found for this repository. Please run a new analysis first."
            )
        
        # Use existing analysis ID
        analysis_id = existing["analysis_id"]
        
        # Run fresh analysis using LangGraph workflow
        result = run_analysis_with_langgraph(analysis_id, str(req.repo_url), force_refresh=True)
        
        # Update existing analysis
        update_existing_analysis_data(analysis_id, result)
        
        return StartAnalysisResponse(
            analysis_id=analysis_id,
            status="complete",
            cached=False
        )
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        logger.warning(f"🚫 Refresh failed due to quota exhaustion: {e}")
        raise HTTPException(status_code=429, detail="quota_exhausted")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status_endpoint(analysis_id: str):
    """
    POLLING API: Get current status of analysis request
    Returns status and progress information for polling
    """
    try:
        db = next(get_db())
        try:
            analysis = AnalysisDAO.get_analysis(db, analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            return AnalysisStatusResponse(
                analysis_id=analysis_id,
                status=analysis.status,
                progress_status=analysis.progress_status,
                message=analysis.message
            )
        finally:
            db.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check failed for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}")
def get_analysis_endpoint(analysis_id: str):
    """
    RETRIEVE API: Get complete analysis results by ID
    Only returns data when analysis is completed
    """
    try:
        # First check status
        db = next(get_db())
        try:
            analysis = AnalysisDAO.get_analysis(db, analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            # Only allow retrieval if completed
            if analysis.status != "completed":
                raise HTTPException(
                    status_code=425,  # Too Early
                    detail=f"Analysis not yet completed. Current status: {analysis.status}"
                )
        finally:
            db.close()
        
        # Get full analysis data
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis data not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis retrieval failed for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
