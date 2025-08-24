from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from sqlalchemy import func

from backend.database.connection import get_db
from backend.database.models import Analysis, Example

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
            "components": analysis_data.get("components", []),
            "architecture_md": analysis_data.get("architecture_md"),
            "mermaid_modules": analysis_data.get("mermaid_modules"),
            "mermaid_folders": analysis_data.get("mermaid_folders"),
            # Intelligent diagram variants
            "mermaid_modules_simple": analysis_data.get("mermaid_modules_simple"),
            "mermaid_modules_balanced": analysis_data.get("mermaid_modules_balanced"),
            "mermaid_modules_detailed": analysis_data.get("mermaid_modules_detailed"),
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
    def update_analysis_artifact(db: Session, analysis_id: str, artifact_key: str, content: str) -> Optional[Analysis]:
        """Update a specific artifact in an analysis record"""
        try:
            analysis_uuid = uuid.UUID(analysis_id)
            analysis = db.query(Analysis).filter(Analysis.id == analysis_uuid).first()
            if analysis and hasattr(analysis, artifact_key):
                setattr(analysis, artifact_key, content)
                db.commit()
                db.refresh(analysis)
                return analysis
            return None
        except ValueError:
            return None

    @staticmethod
    def get_analysis_by_repo_url(db: Session, repo_url: str) -> Optional[Analysis]:
        """Get the most recent analysis for a given repository URL"""
        try:
            # Normalize the repo URL - remove trailing slash and .git suffix
            normalized_url = repo_url.rstrip("/").replace(".git", "")
            
            # Find the most recent analysis for this repo URL
            return db.query(Analysis).filter(
                Analysis.repo_url.like(f"%{normalized_url}%")
            ).order_by(Analysis.created_at.desc()).first()
        except Exception:
            return None

    @staticmethod
    def update_existing_analysis(db: Session, analysis: Analysis, new_data: Dict[str, Any]) -> Analysis:
        """Update an existing analysis with new data, keeping the same ID"""
        try:
            for key, value in new_data.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)
            
            # Update the updated_at timestamp
            analysis.updated_at = func.now()
            
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as e:
            db.rollback()
            raise e


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
                # New intelligent dependency diagrams
                update_data["mermaid_modules_simple"] = artifacts.get("mermaid_modules_simple")
                update_data["mermaid_modules_balanced"] = artifacts.get("mermaid_modules_balanced")
                update_data["mermaid_modules_detailed"] = artifacts.get("mermaid_modules_detailed")
            
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
                # New intelligent dependency diagrams
                analysis_data["mermaid_modules_simple"] = artifacts.get("mermaid_modules_simple")
                analysis_data["mermaid_modules_balanced"] = artifacts.get("mermaid_modules_balanced")
                analysis_data["mermaid_modules_detailed"] = artifacts.get("mermaid_modules_detailed")
            
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
            "components": analysis.components or [],
            "artifacts": {
                "architecture_md": analysis.architecture_md or "",
                "mermaid_modules": analysis.mermaid_modules or "",
                "mermaid_folders": analysis.mermaid_folders or "",
                # New intelligent dependency diagrams
                "mermaid_modules_simple": analysis.mermaid_modules_simple or "",
                "mermaid_modules_balanced": analysis.mermaid_modules_balanced or "",
                "mermaid_modules_detailed": analysis.mermaid_modules_detailed or ""
            },
            "token_budget": analysis.token_budget or {"embed_calls": 0, "gen_calls": 0, "chunks": 0}
        }
    finally:
        db.close()

def update_analysis_artifact(analysis_id: str, artifact_key: str, content: str) -> bool:
    """Update a specific artifact in an analysis record"""
    db = next(get_db())
    try:
        result = AnalysisDAO.update_analysis_artifact(db, analysis_id, artifact_key, content)
        return result is not None
    finally:
        db.close()

def get_existing_analysis_by_url(repo_url: str) -> Optional[dict]:
    """Check if analysis already exists for a given repository URL"""
    db = next(get_db())
    try:
        analysis = AnalysisDAO.get_analysis_by_repo_url(db, repo_url)
        if not analysis:
            return None
        
        # Return minimal info about existing analysis
        return {
            "analysis_id": str(analysis.id),
            "repo_url": analysis.repo_url,
            "status": analysis.status,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
        }
    finally:
        db.close()

def update_existing_analysis_data(analysis_id: str, new_data: dict) -> bool:
    """Update existing analysis with fresh data"""
    db = next(get_db())
    try:
        analysis = AnalysisDAO.get_analysis(db, analysis_id)
        if not analysis:
            return False
        
        # Flatten the data structure similar to save_analysis_summary
        update_data = new_data.copy()
        
        # Extract artifacts data and flatten to top level
        artifacts = update_data.pop("artifacts", {})
        if artifacts:
            update_data["architecture_md"] = artifacts.get("architecture_md")
            update_data["mermaid_modules"] = artifacts.get("mermaid_modules")
            update_data["mermaid_folders"] = artifacts.get("mermaid_folders")
            # New intelligent dependency diagrams
            update_data["mermaid_modules_simple"] = artifacts.get("mermaid_modules_simple")
            update_data["mermaid_modules_balanced"] = artifacts.get("mermaid_modules_balanced")
            update_data["mermaid_modules_detailed"] = artifacts.get("mermaid_modules_detailed")
        
        # Extract repo data and flatten to top level
        repo = update_data.pop("repo", {})
        if repo:
            update_data["repo_url"] = repo.get("url")
            update_data["commit_sha"] = repo.get("commit_sha")
        
        AnalysisDAO.update_existing_analysis(db, analysis, update_data)
        return True
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