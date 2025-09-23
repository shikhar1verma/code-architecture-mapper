"""
Request and Response Models for Analysis API

All Pydantic models used across the analysis endpoints.
Simple, focused data structures without business logic.
"""

from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional, Any


# ===== Analysis Operation Models =====

class StartAnalysisRequest(BaseModel):
    repo_url: HttpUrl


class StartAnalysisResponse(BaseModel):
    analysis_id: str
    status: str  # pending, started, completed, failed
    cached: bool = False
    cached_at: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str  # pending, started, completed, failed  
    progress_status: Optional[str] = None  # Human-readable progress description
    message: Optional[str] = None


class RefreshAnalysisRequest(BaseModel):
    analysis_id: str


# ===== Diagram Operation Models =====

class MermaidRetryRequest(BaseModel):
    broken_mermaid_code: str
    error_message: str


# ===== Dependency Operation Models =====

class FocusedAnalysisResponse(BaseModel):
    module: str
    focused_diagram: str
    connected_modules: List[str]
    dependencies: List[str]
    dependents: List[str]
    external_dependencies: Dict[str, List[str]]
    metrics: Dict[str, int]


class DependencyInsightsResponse(BaseModel):
    summary: Dict[str, Any]
    most_connected_modules: List[Dict[str, Any]]
    external_category_stats: Dict[str, Dict[str, int]]
    module_statistics: Dict[str, float]
    recommendations: List[str]
