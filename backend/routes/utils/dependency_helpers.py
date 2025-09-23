"""
Dependency Analysis Helper Functions

This module contains utility functions for analyzing and processing
dependency data in the analysis routes.
"""

from typing import Dict, List, Any


def generate_dependency_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """
    Generate recommendations based on dependency analysis
    
    Args:
        analysis: Dictionary containing dependency analysis data with
                 external_groups and summary information
                 
    Returns:
        List of recommendation strings based on dependency patterns
    """
    recommendations = []
    
    external_groups = analysis.get("external_groups", {})
    internal_count = analysis.get("summary", {}).get("internal_count", 0)
    external_count = analysis.get("summary", {}).get("external_count", 0)
    
    # High external dependency ratio
    if external_count > internal_count * 3:
        recommendations.append(
            "Consider consolidating external dependencies - high external/internal ratio detected"
        )
    
    # Too many categories
    if len(external_groups) > 8:
        recommendations.append(
            "Consider grouping similar dependencies - many categories detected"
        )
    
    # Standard library usage
    stdlib_count = len(external_groups.get("Standard Library", []))
    if stdlib_count > external_count * 0.4:
        recommendations.append(
            "High standard library usage - consider if all imports are necessary"
        )
    
    # Development dependencies in production
    dev_deps = external_groups.get("Testing", []) + external_groups.get("Build/Config", [])
    if len(dev_deps) > 10:
        recommendations.append(
            "Review development dependencies - ensure proper separation from production code"
        )
    
    if not recommendations:
        recommendations.append("Dependency structure looks well-organized")
    
    return recommendations


def calculate_module_connection_stats(internal_edges: List[Dict[str, str]]) -> Dict[str, Dict[str, int]]:
    """
    Calculate connection statistics for modules based on internal edges
    
    Args:
        internal_edges: List of internal dependency edges with 'src' and 'dst' keys
        
    Returns:
        Dictionary mapping module names to their connection statistics
    """
    module_stats = {}
    
    for edge in internal_edges:
        src, dst = edge["src"], edge["dst"]
        
        if src not in module_stats:
            module_stats[src] = {"outgoing": 0, "incoming": 0}
        if dst not in module_stats:
            module_stats[dst] = {"outgoing": 0, "incoming": 0}
            
        module_stats[src]["outgoing"] += 1
        module_stats[dst]["incoming"] += 1
    
    return module_stats


def get_most_connected_modules(module_stats: Dict[str, Dict[str, int]], limit: int = 10) -> List[tuple]:
    """
    Get the most connected modules sorted by total connections
    
    Args:
        module_stats: Module connection statistics from calculate_module_connection_stats
        limit: Maximum number of modules to return
        
    Returns:
        List of tuples (module_name, total_connections) sorted by connections descending
    """
    return sorted(
        [(mod, stats["outgoing"] + stats["incoming"]) for mod, stats in module_stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:limit]


def calculate_external_dependency_stats(external_groups: Dict[str, List[tuple]]) -> Dict[str, Dict[str, int]]:
    """
    Calculate statistics for external dependency groups
    
    Args:
        external_groups: Dictionary mapping category names to lists of (src, dst) dependency tuples
        
    Returns:
        Dictionary mapping category names to their statistics
    """
    external_stats = {}
    
    for category, deps in external_groups.items():
        unique_deps = set(dst for src, dst in deps)
        modules_using = set(src for src, dst in deps)
        external_stats[category] = {
            "unique_packages": len(unique_deps),
            "modules_using": len(modules_using),
            "total_imports": len(deps)
        }
    
    return external_stats 