"""
Analysis Orchestrator Service

This service coordinates the various analysis services to perform
complete repository analysis. It acts as a simplified version of
the original pipeline for the core analysis workflow.

This orchestrator handles:
- Repository cloning and scanning
- Code parsing and dependency extraction  
- Metrics calculation and graph analysis
- Data coordination between services

LLM-based content generation remains in the main pipeline for now.
"""

from typing import Dict, Any, List, Tuple
from backend.services.analysis.repository import RepositoryService
from backend.services.analysis.code_parser import CodeParserService  
from backend.services.analysis.metrics import MetricsService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisOrchestrator:
    """Orchestrates the core analysis workflow using specialized services"""
    
    def __init__(self):
        self.repo_service = RepositoryService()
        self.parser_service = CodeParserService()
        self.metrics_service = MetricsService()
    
    def perform_core_analysis(self, repo_url: str) -> Dict[str, Any]:
        """
        Perform enhanced core repository analysis including cloning, parsing, and metrics
        
        Args:
            repo_url: URL of the repository to analyze
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        # Step 1: Clone repository and scan files
        repo_root, commit_sha, file_infos = self.repo_service.clone_and_scan_repository(repo_url)
        
        # Step 2: Enhanced metrics and graph analysis using the new architecture mapper
        # This now handles both file scanning and dependency extraction internally
        metrics = self.metrics_service.analyze_repository_metrics(repo_root)
        
        # Step 3: Get additional insights
        complexity_analysis = self.metrics_service.calculate_project_complexity_score(metrics=metrics)
        architectural_patterns = self.metrics_service.identify_architectural_patterns(metrics)
        
        # Step 4: Prepare enhanced analysis results
        core_results = {
            "repository": {
                "root_path": repo_root,
                "commit_sha": commit_sha,
                "url": repo_url
            },
            "files": {
                "file_infos": file_infos,  # Keep for compatibility
                "repository_metrics": metrics.get("repository_metrics", {})
            },
            "dependencies": {
                "edges": metrics.get("dependency_analysis", {}).get("edges", []),
                "dependency_analysis": metrics.get("dependency_analysis", {})
            },
            "metrics": {
                "graph_metrics": metrics.get("graph_metrics", {}),
                "top_files": metrics.get("top_files", []),
                "json_graph": metrics.get("json_graph", {}),
                "complexity_analysis": complexity_analysis,
                "architectural_patterns": architectural_patterns
            }
        }
        
        return core_results
    
    def prepare_excerpts_for_llm(self, core_results: Dict[str, Any], 
                                max_files: int = 50) -> List[Tuple[str, str]]:
        """
        Prepare file excerpts for LLM analysis
        
        Args:
            core_results: Results from perform_core_analysis
            max_files: Maximum number of files to extract excerpts from
            
        Returns:
            List of tuples (file_path, excerpt)
        """
        file_infos = core_results["files"]["file_infos"]
        top_files = core_results["metrics"]["top_files"][:max_files]
        
        return self.repo_service.extract_file_excerpts(file_infos, top_files)
    
    def get_analysis_summary_for_pipeline(self, core_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format core results for compatibility with existing pipeline structure
        
        Args:
            core_results: Results from perform_core_analysis
            
        Returns:
            Dictionary formatted for pipeline compatibility
        """
        repository_metrics = core_results["files"]["repository_metrics"]
        metrics = core_results["metrics"]
        
        # Format for pipeline compatibility
        summary = {
            "repo": core_results["repository"],
            "language_stats": repository_metrics["language_stats"],
            "loc_total": repository_metrics["loc_total"],
            "file_count": repository_metrics["file_count"],
            "metrics": {
                "central_files": self.metrics_service.get_central_files_summary(metrics),
                "graph": metrics["json_graph"],
                "dependency_analysis": core_results["dependencies"]["dependency_analysis"],
                "complexity_analysis": metrics["complexity_analysis"],
                "architectural_patterns": metrics["architectural_patterns"]
            }
        }
        
        return summary
    
    def get_enhanced_insights(self, core_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced insights from core analysis
        
        Args:
            core_results: Results from perform_core_analysis
            
        Returns:
            Dictionary containing enhanced insights
        """
        file_infos = core_results["files"]["file_infos"]
        edges = core_results["dependencies"]["edges"]
        
        # Get detailed dependency patterns
        dependency_patterns = self.parser_service.analyze_dependency_patterns(edges)
        
        # Get file complexity metrics
        file_complexity = self.parser_service.get_file_complexity_metrics(file_infos, edges)
        
        return {
            "dependency_patterns": dependency_patterns,
            "file_complexity": file_complexity,
            "analysis_metadata": {
                "services_used": ["repository", "code_parser", "metrics"],
                "analysis_timestamp": None,  # Could add timestamp
                "version": "1.0"
            }
        }
    
    def cleanup_temporary_files(self, core_results: Dict[str, Any]) -> None:
        """
        Clean up temporary files after analysis
        
        Args:
            core_results: Results from perform_core_analysis
        """
        import shutil
        import os
        
        repo_root = core_results["repository"]["root_path"]
        if os.path.exists(repo_root):
            try:
                shutil.rmtree(repo_root)
                logger.info(f"🧹 Cleaned up temporary repository: {repo_root}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup {repo_root}: {e}")
    
    def get_service_status(self) -> Dict[str, str]:
        """Get status of all services for debugging"""
        return {
            "repository_service": "active",
            "code_parser_service": "active", 
            "metrics_service": "active",
            "orchestrator": "active"
        } 