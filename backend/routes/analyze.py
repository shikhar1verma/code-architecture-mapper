from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import uuid
from backend.services.pipeline import run_analysis
from backend.storage.dao import save_analysis_summary, get_analysis

router = APIRouter()

class StartAnalysisRequest(BaseModel):
    repo_url: HttpUrl
    force_refresh: bool = False

class StartAnalysisResponse(BaseModel):
    analysis_id: str
    status: str

@router.post("/analyze", response_model=StartAnalysisResponse)
def start_analyze(req: StartAnalysisRequest):
    analysis_id = str(uuid.uuid4())
    try:
        # Synchronous for local MVP (simple!)
        summary = run_analysis(analysis_id=analysis_id, repo_url=str(req.repo_url), force_refresh=req.force_refresh)
        save_analysis_summary(analysis_id, summary)
        return {"analysis_id": analysis_id, "status": "complete"}
    except Exception as e:
        # raise HTTPException(status_code=500, detail=f"analysis failed: {e}")
        raise
