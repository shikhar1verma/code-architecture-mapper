from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from backend.database.connection import get_db
from backend.database.models import Example

router = APIRouter(prefix="/examples", tags=["examples"])
logger = logging.getLogger(__name__)

@router.get("/")
async def list_examples(session: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get list of all available examples
    Returns basic info for dropdown display
    """
    try:
        examples = session.query(Example).order_by(Example.name).all()
        
        result = []
        for example in examples:
            result.append({
                "id": str(example.id),
                "name": example.name,
                "description": example.description,
                "repo_url": example.repo_url,
                "repo_name": example.repo_name,
                "language_stats": example.language_stats,
                "loc_total": example.loc_total,
                "file_count": example.file_count
            })
        
        logger.info(f"Retrieved {len(result)} examples")
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch examples: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch examples")

@router.get("/{example_id}")
async def get_example(
    example_id: str,
    session: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete example analysis data by ID
    Returns the same format as analysis results for compatibility
    """
    try:
        # Get example with files
        example = session.query(Example).filter_by(id=example_id).first()
        
        if not example:
            raise HTTPException(status_code=404, detail="Example not found")
        
        # Files are no longer stored separately
        
        # Format response in same structure as analysis result
        result = {
            "status": example.status,
            "repo": {
                "url": example.repo_url,
                "commit_sha": example.commit_sha or "",
                "owner": example.repo_owner,
                "name": example.repo_name,
                "default_branch": example.default_branch
            },
            "language_stats": example.language_stats or {},
            "loc_total": example.loc_total,
            "file_count": example.file_count,
            "metrics": example.metrics or {},
            "components": example.components or [],
            "artifacts": {
                "architecture_md": example.architecture_md or "",
                "mermaid_modules": example.mermaid_modules or "",
                "mermaid_modules_simple": example.mermaid_modules_simple or "",
                "mermaid_modules_balanced": example.mermaid_modules_balanced or "",
                "mermaid_modules_detailed": example.mermaid_modules_detailed or "",
                "mermaid_folders": example.mermaid_folders or ""
            },
            "token_budget": example.token_budget or {
                "embed_calls": 0,
                "gen_calls": 0,
                "chunks": 0
            }
        }
        
        logger.info(f"Retrieved example '{example.name}'")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch example {example_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch example data")

 