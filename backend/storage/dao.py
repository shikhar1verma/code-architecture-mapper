"""
Simple Data Access Objects for storage operations

This module contains clean DAO classes and legacy functions for backward compatibility.
All transformation logic has been moved to helpers.py for better separation of concerns.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime

from backend.database.connection import get_db
from backend.database.models import Analysis, Example
from backend.storage.helpers import DataTransformer


class AnalysisDAO:
    """Clean Data Access Object for Analysis operations"""

    @staticmethod
    def create_analysis(db: Session, analysis_data: Dict[str, Any], analysis_id: str = None) -> Analysis:
        """Create a new analysis record"""
        analysis_kwargs = analysis_data.copy()
        
        # Add specific ID if provided
        if analysis_id:
            try:
                analysis_kwargs["id"] = uuid.UUID(analysis_id)
            except ValueError:
                pass  # Let database generate ID
        
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
            # Use helper to update the analysis
            DataTransformer.update_analysis_from_dict(analysis, new_data)
            
            # Update the timestamp manually (fixing the func.now() issue)
            analysis.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def generate_unique_analysis_id(db: Session) -> str:
        """Generate a unique UUID for analysis, checking for collisions"""
        max_attempts = 10
        for _ in range(max_attempts):
            new_uuid = uuid.uuid4()
            # Check if this UUID already exists
            existing = db.query(Analysis).filter(Analysis.id == new_uuid).first()
            if not existing:
                return str(new_uuid)
        
        # If we get here, we've had 10 collisions (extremely unlikely)
        raise RuntimeError("Failed to generate unique analysis ID after 10 attempts")


class ExampleDAO:
    """Clean Data Access Object for Example operations"""

    @staticmethod
    def get_all_examples(db: Session) -> List[Example]:
        """Get all example repositories"""
        return db.query(Example).all()

    @staticmethod
    def get_example_by_id(db: Session, example_id: str) -> Optional[Example]:
        """Get example by ID"""
        try:
            example_uuid = uuid.UUID(example_id)
            return db.query(Example).filter(Example.id == example_uuid).first()
        except ValueError:
            return None

    @staticmethod
    def get_example_by_name(db: Session, name: str) -> Optional[Example]:
        """Get example by name"""
        return db.query(Example).filter(Example.name == name).first()

    @staticmethod
    def create_or_update_example(db: Session, example_data: Dict[str, Any]) -> Optional[Example]:
        """Create new example or update existing one by name"""
        name = example_data.get("name")
        if not name:
            return None
        
        try:
            # Check if example exists
            existing = ExampleDAO.get_example_by_name(db, name)
            
            if existing:
                # Update existing example
                for key, value in example_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                example = existing
            else:
                # Create new example
                example = Example(**example_data)
                db.add(example)
            
            db.commit()
            db.refresh(example)
            return example
            
        except IntegrityError:
            db.rollback()
            return None


# =============================================================================
# LEGACY FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================
# These functions maintain the exact same interface as before but use the
# clean DAO classes and DataTransformer helpers internally.

def save_analysis_summary(analysis_id: str, payload: dict):
    """Save analysis summary to database - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        # Check if analysis already exists
        existing = AnalysisDAO.get_analysis(db, analysis_id)
        
        if existing:
            # Update existing analysis
            DataTransformer.update_analysis_from_dict(existing, payload)
            db.commit()
        else:
            # Create new analysis using helper
            analysis_data = DataTransformer.dict_to_analysis_data(payload, analysis_id)
            AnalysisDAO.create_analysis(db, analysis_data, analysis_id)
            
    finally:
        db.close()


def get_analysis(analysis_id: str) -> Optional[dict]:
    """Get analysis by ID and return as dict - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        analysis = AnalysisDAO.get_analysis(db, analysis_id)
        if not analysis:
            return None
        
        # Convert to dict using helper
        return DataTransformer.analysis_to_dict(analysis)
        
    finally:
        db.close()


def update_analysis_artifact(analysis_id: str, artifact_key: str, content: str) -> bool:
    """Update a specific artifact in an analysis record - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        result = AnalysisDAO.update_analysis_artifact(db, analysis_id, artifact_key, content)
        return result is not None
    finally:
        db.close()


def get_existing_analysis_by_url(repo_url: str) -> Optional[dict]:
    """Check if analysis already exists for a given repository URL - LEGACY FUNCTION"""
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
    """Update existing analysis with fresh data - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        analysis = AnalysisDAO.get_analysis(db, analysis_id)
        if not analysis:
            return False
        
        # Update using DAO method (which uses DataTransformer)
        AnalysisDAO.update_existing_analysis(db, analysis, new_data)
        return True
        
    except Exception:
        return False
    finally:
        db.close()


def list_examples():
    """List all example repositories - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        examples = ExampleDAO.get_all_examples(db)
        
        # Convert to dicts using helper
        return [DataTransformer.example_to_dict(example) for example in examples]
        
    finally:
        db.close()


def get_example_by_id(example_id: str) -> Optional[dict]:
    """Get example by ID - LEGACY FUNCTION"""
    db = next(get_db())
    try:
        example = ExampleDAO.get_example_by_id(db, example_id)
        if not example:
            return None
        
        # Convert to dict using helper
        return DataTransformer.example_to_dict(example)
        
    finally:
        db.close()


def save_example_from_fixture(example_data: dict) -> bool:
    """Save example from fixture data - FOR FIXTURE LOADING"""
    db = next(get_db())
    try:
        result = ExampleDAO.create_or_update_example(db, example_data)
        return result is not None
    except Exception:
        return False
    finally:
        db.close()


def generate_unique_analysis_id() -> str:
    """Generate a unique UUID for analysis - Helper function"""
    db = next(get_db())
    try:
        return AnalysisDAO.generate_unique_analysis_id(db)
    finally:
        db.close() 