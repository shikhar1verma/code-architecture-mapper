from fastapi import APIRouter, HTTPException
from backend.storage.dao import get_analysis, list_examples

router = APIRouter()

@router.get("/analysis/{analysis_id}")
def get_analysis_handler(analysis_id: str):
    data = get_analysis(analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="analysis not found")
    return data

@router.get("/examples")
def examples():
    return list_examples() 