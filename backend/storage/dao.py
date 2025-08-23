from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from backend.database.connection import get_db
from backend.database.models import Analysis, File, Example

class AnalysisDAO:
    """Data Access Object for Analysis operations"""

    @staticmethod
    def create_analysis(db: Session, analysis_data: Dict[str, Any], analysis_id: str = None) -> Analysis:
        """Create a new analysis record"""
        # Extract repo info from URL
        repo_url = analysis_data.get("repo_url", "")
        repo_parts = repo_url.rstrip("/").split("/")
        repo_owner = repo_parts[-2] if len(repo_parts) >= 2 else None
        repo_name = repo_parts[-1].replace(".git", "") if len(repo_parts) >= 1 else None

        # Use provided analysis_id or let database generate one
        analysis_kwargs = {
            "repo_url": repo_url,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "commit_sha": analysis_data.get("commit_sha"),
            "status": analysis_data.get("status", "queued"),
            "message": analysis_data.get("message"),
            "language_stats": analysis_data.get("language_stats"),
            "loc_total": analysis_data.get("loc_total", 0),
            "file_count": analysis_data.get("file_count", 0),
            "metrics": analysis_data.get("metrics"),
            "architecture_md": analysis_data.get("architecture_md"),
            "mermaid_modules": analysis_data.get("mermaid_modules"),
            "mermaid_folders": analysis_data.get("mermaid_folders"),
            "token_budget": analysis_data.get("token_budget", {"embed_calls": 0, "gen_calls": 0, "chunks": 0})
        }
        
        # Add specific ID if provided
        if analysis_id:
            analysis_kwargs["id"] = uuid.UUID(analysis_id)
            
        analysis = Analysis(**analysis_kwargs)
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_analysis(db: Session, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID"""
        try:
            analysis_uuid = uuid.UUID(analysis_id)
            return db.query(Analysis).filter(Analysis.id == analysis_uuid).first()
        except ValueError:
            return None

    @staticmethod
    def update_analysis(db: Session, analysis_id: str, updates: Dict[str, Any]) -> Optional[Analysis]:
        """Update analysis record"""
        try:
            analysis_uuid = uuid.UUID(analysis_id)
            analysis = db.query(Analysis).filter(Analysis.id == analysis_uuid).first()
            if analysis:
                for key, value in updates.items():
                    if hasattr(analysis, key):
                        setattr(analysis, key, value)
                db.commit()
                db.refresh(analysis)
            return analysis
        except ValueError:
            return None

    @staticmethod
    def save_files(db: Session, analysis_id: str, files_data: List[Dict[str, Any]]) -> List[File]:
        """Save file metrics for an analysis"""
        try:
            analysis_uuid = uuid.UUID(analysis_id)
            files = []
            for file_data in files_data:
                file_obj = File(
                    analysis_id=analysis_uuid,
                    path=file_data.get("path"),
                    language=file_data.get("language"),
                    loc=file_data.get("loc", 0),
                    fan_in=file_data.get("fan_in", 0),
                    fan_out=file_data.get("fan_out", 0),
                    centrality=file_data.get("centrality", 0.0),
                    hash=file_data.get("hash"),
                    snippet=file_data.get("snippet")
                )
                files.append(file_obj)
                db.add(file_obj)
            
            db.commit()
            for file_obj in files:
                db.refresh(file_obj)
            return files
        except ValueError:
            return []

class ExampleDAO:
    """Data Access Object for Example operations"""

    @staticmethod
    def get_all_examples(db: Session) -> List[Example]:
        """Get all example repositories"""
        return db.query(Example).all()

    @staticmethod
    def create_example(db: Session, repo_url: str, label: str, description: str = None, analysis_id: str = None) -> Optional[Example]:
        """Create a new example repository"""
        try:
            example = Example(
                repo_url=repo_url,
                label=label,
                description=description,
                analysis_id=uuid.UUID(analysis_id) if analysis_id else None
            )
            db.add(example)
            db.commit()
            db.refresh(example)
            return example
        except IntegrityError:
            db.rollback()
            return None  # Duplicate repo_url

# Legacy functions for compatibility with existing code
def save_analysis_summary(analysis_id: str, payload: dict):
    """Save analysis summary to database"""
    db = next(get_db())
    try:
        existing = AnalysisDAO.get_analysis(db, analysis_id)
        if existing:
            # Update existing analysis
            update_data = payload.copy()
            
            # Extract artifacts data and flatten to top level
            artifacts = update_data.pop("artifacts", {})
            if artifacts:
                update_data["architecture_md"] = artifacts.get("architecture_md")
                update_data["mermaid_modules"] = artifacts.get("mermaid_modules")
                update_data["mermaid_folders"] = artifacts.get("mermaid_folders")
            
            # Extract repo data and flatten to top level
            repo = update_data.pop("repo", {})
            if repo:
                update_data["repo_url"] = repo.get("url")
                update_data["commit_sha"] = repo.get("commit_sha")
                
            AnalysisDAO.update_analysis(db, analysis_id, update_data)
        else:
            # Create new analysis with the given ID
            analysis_data = payload.copy()
            
            # Extract artifacts data and flatten to top level
            artifacts = analysis_data.pop("artifacts", {})
            if artifacts:
                analysis_data["architecture_md"] = artifacts.get("architecture_md")
                analysis_data["mermaid_modules"] = artifacts.get("mermaid_modules")
                analysis_data["mermaid_folders"] = artifacts.get("mermaid_folders")
            
            # Extract repo data and flatten to top level
            repo = analysis_data.pop("repo", {})
            if repo:
                analysis_data["repo_url"] = repo.get("url")
                analysis_data["commit_sha"] = repo.get("commit_sha")
            
            analysis = AnalysisDAO.create_analysis(db, analysis_data, analysis_id)
    finally:
        db.close()

def get_analysis(analysis_id: str) -> Optional[dict]:
    """Get analysis by ID and return as dict"""
    db = next(get_db())
    try:
        analysis = AnalysisDAO.get_analysis(db, analysis_id)
        if not analysis:
            return None
        
        # Convert SQLAlchemy model to dict format expected by frontend
        return {
            "status": analysis.status,
            "repo": {
                "url": analysis.repo_url,
                "commit_sha": analysis.commit_sha or ""
            },
            "language_stats": analysis.language_stats or {},
            "loc_total": analysis.loc_total or 0,
            "file_count": analysis.file_count or 0,
            "metrics": analysis.metrics or {"central_files": [], "graph": {"nodes": [], "edges": []}},
            "components": [],  # Empty for MVP
            "artifacts": {
                "architecture_md": analysis.architecture_md or "",
                "mermaid_modules": analysis.mermaid_modules or "",
                "mermaid_folders": analysis.mermaid_folders or ""
            },
            "token_budget": analysis.token_budget or {"embed_calls": 0, "gen_calls": 0, "chunks": 0}
        }
    finally:
        db.close()

def list_examples():
    """List all example repositories"""
    db = next(get_db())
    try:
        examples = ExampleDAO.get_all_examples(db)
        return [
            {
                "id": str(example.id),
                "repo_url": example.repo_url,
                "label": example.label,
                "description": example.description,
                "analysis_id": str(example.analysis_id) if example.analysis_id else None
            }
            for example in examples
        ]
    finally:
        db.close() 