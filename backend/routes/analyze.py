from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import uuid
from backend.services.pipeline import run_analysis
from backend.storage.dao import save_analysis_summary, get_analysis, list_examples, get_existing_analysis_by_url, update_existing_analysis_data
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError

router = APIRouter()

class StartAnalysisRequest(BaseModel):
    repo_url: HttpUrl
    force_refresh: bool = False

class StartAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    cached: bool = False
    cached_at: str = None

class RefreshAnalysisRequest(BaseModel):
    analysis_id: str

@router.post("/analyze", response_model=StartAnalysisResponse)
def start_analyze(req: StartAnalysisRequest):
    repo_url = str(req.repo_url)
    
    # Check if analysis already exists for this repo URL
    if not req.force_refresh:
        existing_analysis = get_existing_analysis_by_url(repo_url)
        if existing_analysis and existing_analysis.get("status") == "complete":
            print(f"🎯 Found existing analysis for {repo_url}: {existing_analysis['analysis_id']}")
            return {
                "analysis_id": existing_analysis["analysis_id"],
                "status": "complete",
                "cached": True,
                "cached_at": existing_analysis.get("updated_at")
            }
    
    # Run new analysis
    analysis_id = str(uuid.uuid4())
    try:
        print(f"🚀 Running {'fresh' if req.force_refresh else 'new'} analysis for {repo_url}")
        summary = run_analysis(analysis_id=analysis_id, repo_url=repo_url, force_refresh=req.force_refresh)
        save_analysis_summary(analysis_id, summary)
        return {
            "analysis_id": analysis_id, 
            "status": "complete",
            "cached": False
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Analysis failed due to quota exhaustion: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/refresh", response_model=StartAnalysisResponse)
def refresh_analysis(req: RefreshAnalysisRequest):
    """Refresh an existing analysis with latest data"""
    try:
        # Get existing analysis to find repo URL
        existing_analysis_data = get_analysis(req.analysis_id)
        if not existing_analysis_data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        repo_url = existing_analysis_data["repo"]["url"]
        print(f"🔄 Refreshing analysis {req.analysis_id} for {repo_url}")
        
        # Run analysis with force_refresh=True
        summary = run_analysis(analysis_id=req.analysis_id, repo_url=repo_url, force_refresh=True)
        
        # Update existing analysis instead of creating new one
        success = update_existing_analysis_data(req.analysis_id, summary)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update analysis")
        
        return {
            "analysis_id": req.analysis_id,
            "status": "complete",
            "cached": False
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Refresh failed due to quota exhaustion: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
def get_examples():
    """Get list of example repositories"""
    try:
        return list_examples()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
