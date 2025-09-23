"""
Dependency Analysis Operations

Handles focused dependency analysis and insights for specific modules.
Provides detailed connection metrics and architectural recommendations.
"""

from fastapi import APIRouter, HTTPException

from backend.storage.dao import get_analysis
from backend.graphing import intelligent_modules_mermaid
from backend.routes.utils.dependency_helpers import (
    generate_dependency_recommendations,
    calculate_module_connection_stats,
    get_most_connected_modules,
    calculate_external_dependency_stats
)

from .models import FocusedAnalysisResponse, DependencyInsightsResponse

router = APIRouter()


@router.get(
    "/analysis/{analysis_id}/focus/{module_path:path}",
    response_model=FocusedAnalysisResponse)
def get_focused_dependency_analysis(analysis_id: str, module_path: str):
    """Get a focused dependency analysis for a specific module"""
    try:
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")

        dependency_analysis = result.get("metrics", {}).get("dependency_analysis", {})

        if not dependency_analysis:
            raise HTTPException(status_code=404, detail="No dependency analysis available")

        # Create focused diagram
        focused_diagram = intelligent_modules_mermaid(
            dependency_analysis,
            mode="focused",
            focus_module=module_path,
            title=f"Dependencies: {module_path}"
        )

        # Find connected modules and their details
        internal_edges = dependency_analysis.get("internal_edges", [])
        connected_modules = set([module_path])
        dependencies = []
        dependents = []

        for edge in internal_edges:
            if edge["src"] == module_path:
                connected_modules.add(edge["dst"])
                dependencies.append(edge["dst"])
            elif edge["dst"] == module_path:
                connected_modules.add(edge["src"])
                dependents.append(edge["src"])

        # Find external dependencies for this module
        external_deps = {}
        external_groups = dependency_analysis.get("external_groups", {})
        for category, deps in external_groups.items():
            relevant_deps = [dst for src, dst in deps if src == module_path]
            if relevant_deps:
                external_deps[category] = relevant_deps

        return FocusedAnalysisResponse(
            module=module_path,
            focused_diagram=focused_diagram,
            connected_modules=list(connected_modules),
            dependencies=dependencies,
            dependents=dependents,
            external_dependencies=external_deps,
            metrics={
                "total_connections": len(connected_modules) - 1,
                "incoming": len(dependents),
                "outgoing": len(dependencies),
                "external_count": sum(len(deps) for deps in external_deps.values())
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/{analysis_id}/dependency-insights",
    response_model=DependencyInsightsResponse)
def get_dependency_insights(analysis_id: str):
    """Get enhanced dependency insights and statistics"""
    try:
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")

        dependency_analysis = result.get("metrics", {}).get("dependency_analysis", {})

        if not dependency_analysis:
            raise HTTPException(status_code=404, detail="No dependency analysis available")

        # Calculate additional insights using utility functions
        internal_edges = dependency_analysis.get("internal_edges", [])
        external_groups = dependency_analysis.get("external_groups", {})

        # Module connection statistics
        module_stats = calculate_module_connection_stats(internal_edges)

        # Find most connected modules
        most_connected = get_most_connected_modules(module_stats, limit=10)

        # External dependency statistics
        external_stats = calculate_external_dependency_stats(external_groups)

        return DependencyInsightsResponse(
            summary=dependency_analysis.get("summary", {}),
            most_connected_modules=[
                {"module": mod, "connections": conn} for mod, conn in most_connected],
            external_category_stats=external_stats,
            module_statistics={
                "total_modules": len(module_stats),
                "average_connections": (
                    sum(stats["outgoing"] + stats["incoming"]
                        for stats in module_stats.values()) / len(module_stats)
                    if module_stats else 0
                ),
                "most_dependencies": max(
                    (stats["outgoing"] for stats in module_stats.values()), default=0),
                "most_dependents": max(
                    (stats["incoming"] for stats in module_stats.values()), default=0)
            },
            recommendations=generate_dependency_recommendations(dependency_analysis)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
