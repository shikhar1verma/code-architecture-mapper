"""
Enhanced Metrics Analysis Service

This service handles advanced graph building and metrics calculation including:
- Optimized dependency graph construction with proper import resolution
- Enhanced centrality analysis (in-degree, out-degree, degree centrality)
- File ranking and importance scoring
- Graph-based insights with fan-in/fan-out analysis
- Optional Grimp support for Python and tree-sitter for JS/TS

Extracted from pipeline.py and enhanced for better separation of concerns.
"""

from typing import Dict, Any, List
from backend.config import TOP_FILES
from .archmap_enhanced import EnhancedArchMapper


class MetricsService:
    """Service for calculating graph metrics and centrality analysis"""
    
    def __init__(self):
        self.top_files_limit = TOP_FILES
    
    def analyze_repository_metrics(self, repo_root: str, file_infos: List[Dict[str, Any]] = None, 
                                  edges: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze repository metrics using enhanced architecture mapper
        
        Args:
            repo_root: Repository root path
            file_infos: Optional list of file information dictionaries (will be scanned if not provided)
            edges: Optional list of dependency edges (will be extracted if not provided)
            
        Returns:
            Dictionary containing comprehensive metrics analysis
        """
        # Use enhanced architecture mapper for complete analysis
        arch_mapper = EnhancedArchMapper(repo_root)
        result = arch_mapper.analyze_repository()
        
        # Extract metrics from the enhanced analysis
        graph_metrics = result["metrics"]["graph_metrics"]
        
        # Get top files limited to configured amount
        top_files = graph_metrics.get("top_files", [])[:self.top_files_limit]
        
        # Enhanced metrics with new centrality measures
        enhanced_metrics = {
            "graph_metrics": {
                "fan_in": graph_metrics["fan_in"],
                "fan_out": graph_metrics["fan_out"], 
                "degree_centrality": graph_metrics["degree_centrality"],
                "in_degree_centrality": graph_metrics["in_degree_centrality"],
                "out_degree_centrality": graph_metrics["out_degree_centrality"]
            },
            "top_files": top_files,
            "dependency_analysis": result["dependencies"]["dependency_analysis"],
            "json_graph": result["metrics"]["json_graph"],
            "repository_metrics": result["files"]["repository_metrics"]
        }
        
        return enhanced_metrics
    
    def get_central_files_summary(self, metrics: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get summary of most central/important files with enhanced centrality metrics
        
        Args:
            metrics: Metrics dictionary from analyze_repository_metrics
            limit: Maximum number of files to return
            
        Returns:
            List of central files with their metrics
        """
        top_files = metrics.get("top_files", [])[:limit]
        graph_metrics = metrics.get("graph_metrics", {})
        
        fan_in = graph_metrics.get("fan_in", {})
        fan_out = graph_metrics.get("fan_out", {})
        degree_centrality = graph_metrics.get("degree_centrality", {})
        in_degree_centrality = graph_metrics.get("in_degree_centrality", {})
        out_degree_centrality = graph_metrics.get("out_degree_centrality", {})
        
        central_files = []
        for file_path in top_files:
            central_files.append({
                "path": file_path,
                "fan_in": fan_in.get(file_path, 0),
                "fan_out": fan_out.get(file_path, 0),
                "degree_centrality": round(degree_centrality.get(file_path, 0.0), 4),
                "in_degree_centrality": round(in_degree_centrality.get(file_path, 0.0), 4),
                "out_degree_centrality": round(out_degree_centrality.get(file_path, 0.0), 4),
                "total_degree": fan_in.get(file_path, 0) + fan_out.get(file_path, 0)
            })
        
        return central_files
    
    def calculate_project_complexity_score(self, file_infos: List[Dict[str, Any]] = None, 
                                         edges: List[Dict[str, str]] = None, 
                                         metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate overall project complexity metrics using enhanced analysis
        
        Args:
            file_infos: Optional list of file information dictionaries (extracted from metrics if not provided)
            edges: Optional list of dependency edges (extracted from metrics if not provided)  
            metrics: Metrics from analyze_repository_metrics
            
        Returns:
            Dictionary containing complexity analysis
        """
        if metrics is None:
            raise ValueError("Metrics dictionary is required")
            
        # Extract data from metrics if individual parameters not provided
        repo_metrics = metrics.get("repository_metrics", {})
        dependency_analysis = metrics.get("dependency_analysis", {})
        graph_metrics = metrics.get("graph_metrics", {})
        
        total_files = repo_metrics.get("file_count", 0)
        total_loc = repo_metrics.get("loc_total", 0)
        total_edges = dependency_analysis.get("total_edges", 0)
        
        # Calculate average metrics using enhanced centrality data
        centrality_values = list(graph_metrics.get("degree_centrality", {}).values())
        avg_centrality = sum(centrality_values) / len(centrality_values) if centrality_values else 0
        
        in_centrality_values = list(graph_metrics.get("in_degree_centrality", {}).values())
        avg_in_centrality = sum(in_centrality_values) / len(in_centrality_values) if in_centrality_values else 0
        
        out_centrality_values = list(graph_metrics.get("out_degree_centrality", {}).values())
        avg_out_centrality = sum(out_centrality_values) / len(out_centrality_values) if out_centrality_values else 0
        
        fan_out_values = list(graph_metrics.get("fan_out", {}).values())
        avg_fan_out = sum(fan_out_values) / len(fan_out_values) if fan_out_values else 0
        
        fan_in_values = list(graph_metrics.get("fan_in", {}).values())
        avg_fan_in = sum(fan_in_values) / len(fan_in_values) if fan_in_values else 0
        
        # Calculate complexity indicators
        dependency_ratio = total_edges / total_files if total_files > 0 else 0
        loc_per_file = total_loc / total_files if total_files > 0 else 0
        
        # Enhanced complexity score (0-100 scale) with better weighting
        complexity_factors = [
            min(dependency_ratio * 8, 25),   # Dependency complexity (max 25 points)
            min(loc_per_file / 12, 20),      # Size complexity (max 20 points)  
            min(avg_centrality * 80, 15),    # General centrality complexity (max 15 points)
            min(avg_fan_out * 4, 20),        # Fan-out complexity (max 20 points)
            min(avg_fan_in * 3, 15),         # Fan-in complexity (max 15 points)
            min((avg_in_centrality + avg_out_centrality) * 25, 5)  # Centrality balance (max 5 points)
        ]
        complexity_score = sum(complexity_factors)
        
        return {
            "complexity_score": round(complexity_score, 1),
            "complexity_level": self._classify_complexity(complexity_score),
            "metrics": {
                "total_files": total_files,
                "total_loc": total_loc,
                "total_dependencies": total_edges,
                "internal_dependencies": dependency_analysis.get("internal_count", 0),
                "external_dependencies": dependency_analysis.get("external_count", 0),
                "avg_loc_per_file": round(loc_per_file, 1),
                "dependency_ratio": round(dependency_ratio, 2),
                "avg_centrality": round(avg_centrality, 4),
                "avg_in_centrality": round(avg_in_centrality, 4),
                "avg_out_centrality": round(avg_out_centrality, 4),
                "avg_fan_out": round(avg_fan_out, 2),
                "avg_fan_in": round(avg_fan_in, 2)
            },
            "indicators": {
                "high_coupling": dependency_ratio > 3.0,
                "large_files": loc_per_file > 200,
                "complex_dependencies": avg_fan_out > 5,
                "centralized_architecture": avg_centrality > 0.3,
                "high_fan_in": avg_fan_in > 3,
                "imbalanced_centrality": abs(avg_in_centrality - avg_out_centrality) > 0.2
            }
        }
    
    def _classify_complexity(self, score: float) -> str:
        """Classify complexity score into human-readable categories"""
        if score < 20:
            return "Low"
        elif score < 40:
            return "Moderate" 
        elif score < 60:
            return "High"
        else:
            return "Very High"
    
    def identify_architectural_patterns(self, metrics: Dict[str, Any], 
                                      file_infos: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Identify common architectural patterns from enhanced metrics
        
        Args:
            metrics: Metrics from analyze_repository_metrics
            file_infos: Optional list of file information dictionaries (can be extracted from metrics)
            
        Returns:
            Dictionary describing identified patterns with enhanced analysis
        """
        graph_metrics = metrics.get("graph_metrics", {})
        fan_out = graph_metrics.get("fan_out", {})
        fan_in = graph_metrics.get("fan_in", {})
        degree_centrality = graph_metrics.get("degree_centrality", {})
        in_degree_centrality = graph_metrics.get("in_degree_centrality", {})
        out_degree_centrality = graph_metrics.get("out_degree_centrality", {})
        
        # Get all files from graph metrics if not provided
        all_files = set(fan_out.keys()).union(set(fan_in.keys()))
        
        patterns = {
            "hub_files": [],           # High fan-out (many dependencies) 
            "sink_files": [],          # High fan-in (highly depended upon)
            "bridge_files": [],        # High both fan-in and fan-out
            "isolated_files": [],      # Low fan-in and fan-out
            "central_files": [],       # High overall centrality
            "entry_points": [],        # High fan-out, low fan-in (likely entry points)
            "utilities": []            # High fan-in, low fan-out (utility modules)
        }
        
        # Dynamic thresholds based on distribution
        fan_out_values = list(fan_out.values())
        fan_in_values = list(fan_in.values())
        centrality_values = list(degree_centrality.values())
        
        fan_out_threshold = max(3, int(sum(fan_out_values) / len(fan_out_values) * 2)) if fan_out_values else 3
        fan_in_threshold = max(2, int(sum(fan_in_values) / len(fan_in_values) * 2)) if fan_in_values else 2
        centrality_threshold = max(0.1, sum(centrality_values) / len(centrality_values) * 2) if centrality_values else 0.1
        
        # Analyze each file
        for file_path in all_files:
            out_degree = fan_out.get(file_path, 0)
            in_degree = fan_in.get(file_path, 0)
            cent = degree_centrality.get(file_path, 0.0)
            in_cent = in_degree_centrality.get(file_path, 0.0)
            out_cent = out_degree_centrality.get(file_path, 0.0)
            
            file_data = {
                "path": file_path,
                "fan_out": out_degree,
                "fan_in": in_degree,
                "degree_centrality": round(cent, 4),
                "in_degree_centrality": round(in_cent, 4),
                "out_degree_centrality": round(out_cent, 4),
                "total_degree": out_degree + in_degree
            }
            
            # Hub files: High fan-out
            if out_degree >= fan_out_threshold:
                patterns["hub_files"].append(file_data.copy())
            
            # Sink files: High fan-in
            if in_degree >= fan_in_threshold:
                patterns["sink_files"].append(file_data.copy())
            
            # Bridge files: High both fan-in and fan-out
            if out_degree >= fan_out_threshold and in_degree >= fan_in_threshold:
                patterns["bridge_files"].append(file_data.copy())
            
            # Central files: High overall centrality
            if cent >= centrality_threshold:
                patterns["central_files"].append(file_data.copy())
            
            # Entry points: High fan-out, low fan-in
            if out_degree >= fan_out_threshold and in_degree <= 1:
                patterns["entry_points"].append(file_data.copy())
            
            # Utilities: High fan-in, low fan-out  
            if in_degree >= fan_in_threshold and out_degree <= 1:
                patterns["utilities"].append(file_data.copy())
            
            # Isolated files: No connections
            if out_degree == 0 and in_degree == 0:
                patterns["isolated_files"].append(file_data.copy())
        
        # Sort patterns by relevance
        patterns["hub_files"].sort(key=lambda x: x["fan_out"], reverse=True)
        patterns["sink_files"].sort(key=lambda x: x["fan_in"], reverse=True)
        patterns["bridge_files"].sort(key=lambda x: x["total_degree"], reverse=True)
        patterns["central_files"].sort(key=lambda x: x["degree_centrality"], reverse=True)
        patterns["entry_points"].sort(key=lambda x: x["fan_out"], reverse=True)
        patterns["utilities"].sort(key=lambda x: x["fan_in"], reverse=True)
        
        # Limit results and add insights
        pattern_limits = {"hub_files": 10, "sink_files": 10, "bridge_files": 8, 
                         "central_files": 10, "entry_points": 5, "utilities": 8, "isolated_files": 20}
        
        for pattern_type, limit in pattern_limits.items():
            patterns[pattern_type] = patterns[pattern_type][:limit]
        
        # Add pattern insights
        patterns["insights"] = {
            "thresholds": {
                "fan_out_threshold": fan_out_threshold,
                "fan_in_threshold": fan_in_threshold,
                "centrality_threshold": round(centrality_threshold, 4)
            },
            "summary": {
                "hub_count": len(patterns["hub_files"]),
                "sink_count": len(patterns["sink_files"]),
                "bridge_count": len(patterns["bridge_files"]),
                "isolated_count": len(patterns["isolated_files"]),
                "entry_point_count": len(patterns["entry_points"]),
                "utility_count": len(patterns["utilities"])
            }
        }
        
        return patterns 