"""
Simple data transformation helpers for storage operations

This module contains utilities for converting between database models 
and dictionary representations, extracted from the repeated logic in dao.py
"""

from typing import Dict, Any, Optional, Tuple
import uuid
from backend.database.models import Analysis, Example


class DataTransformer:
    """Simple data transformation utilities for models and dictionaries"""
    
    @staticmethod
    def analysis_to_dict(analysis: Analysis) -> Dict[str, Any]:
        """
        Convert Analysis model to dictionary format expected by frontend
        
        This replaces the repeated transformation logic in get_analysis()
        """
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
                "architecture_md": analysis.architecture_md,
                "mermaid_modules": analysis.mermaid_modules,
                "mermaid_folders": analysis.mermaid_folders,
                "mermaid_modules_simple": analysis.mermaid_modules_simple,
                "mermaid_modules_balanced": analysis.mermaid_modules_balanced,
                "mermaid_modules_detailed": analysis.mermaid_modules_detailed,
            }
        }
    
    @staticmethod
    def dict_to_analysis_data(payload: Dict[str, Any], analysis_id: str = None) -> Dict[str, Any]:
        """
        Convert analysis dictionary to model field data
        
        This replaces the repeated transformation logic in save_analysis_summary()
        """
        # Extract repo info
        repo_info = payload.get("repo", {})
        repo_url = repo_info.get("url", "")
        commit_sha = repo_info.get("commit_sha", "")
        
        # Parse repo URL for owner/name
        repo_owner, repo_name, default_branch = DataTransformer._parse_repo_url(repo_url)
        
        # Extract artifacts and flatten to individual fields
        artifacts = payload.get("artifacts", {})
        
        # Prepare model data
        model_data = {
            "repo_url": repo_url,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "default_branch": default_branch,
            "commit_sha": commit_sha,
            "status": payload.get("status", "complete"),
            "language_stats": payload.get("language_stats", {}),
            "loc_total": payload.get("loc_total", 0),
            "file_count": payload.get("file_count", 0),
            "metrics": payload.get("metrics", {}),
            "components": payload.get("components", []),
            "architecture_md": artifacts.get("architecture_md"),
            "mermaid_modules": artifacts.get("mermaid_modules"),
            "mermaid_folders": artifacts.get("mermaid_folders"),
            "mermaid_modules_simple": artifacts.get("mermaid_modules_simple"),
            "mermaid_modules_balanced": artifacts.get("mermaid_modules_balanced"),
            "mermaid_modules_detailed": artifacts.get("mermaid_modules_detailed"),
            "token_budget": payload.get("token_budget", {"embed_calls": 0, "gen_calls": 0, "chunks": 0})
        }
        
        # Add specific ID if provided
        if analysis_id:
            try:
                model_data["id"] = uuid.UUID(analysis_id)
            except ValueError:
                pass  # Let database generate ID
        
        return model_data
    
    @staticmethod
    def update_analysis_from_dict(analysis: Analysis, update_data: Dict[str, Any]) -> Analysis:
        """
        Update Analysis model with data from dictionary
        
        This replaces the repeated logic in update_existing_analysis_data()
        """
        # Extract artifacts and flatten
        artifacts = update_data.get("artifacts", {})
        
        # Update basic fields
        if "status" in update_data:
            analysis.status = update_data["status"]
        if "language_stats" in update_data:
            analysis.language_stats = update_data["language_stats"]
        if "loc_total" in update_data:
            analysis.loc_total = update_data["loc_total"]
        if "file_count" in update_data:
            analysis.file_count = update_data["file_count"]
        if "metrics" in update_data:
            analysis.metrics = update_data["metrics"]
        if "components" in update_data:
            analysis.components = update_data["components"]
        
        # Update artifacts
        if artifacts:
            if "architecture_md" in artifacts:
                analysis.architecture_md = artifacts["architecture_md"]
            if "mermaid_modules" in artifacts:
                analysis.mermaid_modules = artifacts["mermaid_modules"]
            if "mermaid_folders" in artifacts:
                analysis.mermaid_folders = artifacts["mermaid_folders"]
            if "mermaid_modules_simple" in artifacts:
                analysis.mermaid_modules_simple = artifacts["mermaid_modules_simple"]
            if "mermaid_modules_balanced" in artifacts:
                analysis.mermaid_modules_balanced = artifacts["mermaid_modules_balanced"]
            if "mermaid_modules_detailed" in artifacts:
                analysis.mermaid_modules_detailed = artifacts["mermaid_modules_detailed"]
        
        return analysis
    
    @staticmethod
    def example_to_dict(example: Example) -> Dict[str, Any]:
        """
        Convert Example model to dictionary format
        
        Used for example listing and retrieval
        """
        return {
            "id": str(example.id),
            "name": example.name,
            "description": example.description,
            "repo_url": example.repo_url,
            "status": example.status,
            "language_stats": example.language_stats or {},
            "loc_total": example.loc_total or 0,
            "file_count": example.file_count or 0,
            "metrics": example.metrics or {},
            "components": example.components or [],
            "artifacts": {
                "architecture_md": example.architecture_md,
                "mermaid_modules": example.mermaid_modules,
                "mermaid_folders": example.mermaid_folders,
                "mermaid_modules_simple": example.mermaid_modules_simple,
                "mermaid_modules_balanced": example.mermaid_modules_balanced,
                "mermaid_modules_detailed": example.mermaid_modules_detailed,
            }
        }
    
    @staticmethod
    def _parse_repo_url(repo_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse repository URL to extract owner, name, and default branch"""
        try:
            # Remove .git suffix and normalize
            clean_url = repo_url.rstrip("/").replace(".git", "")
            parts = clean_url.split("/")
            
            if len(parts) >= 2:
                repo_owner = parts[-2]
                repo_name = parts[-1]
                default_branch = "main"  # Default assumption
                return repo_owner, repo_name, default_branch
            
        except Exception:
            pass
        
        return None, None, None 