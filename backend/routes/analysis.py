from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional, Any
import uuid

from backend.services.pipeline import run_analysis, generate_single_diagram_mode
from backend.storage.dao import (
    AnalysisDAO, save_analysis_summary, get_analysis, update_analysis_artifact,
    get_existing_analysis_by_url, update_existing_analysis_data
)
from backend.graphing.mermaid import intelligent_modules_mermaid
from backend.llm.gemini import GeminiQuotaExhaustedError, GeminiAPIError, generate_mermaid_correction
from backend.llm.prompts import MERMAID_CORRECTION_SYSTEM, MERMAID_CORRECTION_USER_TMPL

router = APIRouter()
dao = AnalysisDAO()

class StartAnalysisRequest(BaseModel):
    repo_url: HttpUrl
    force_refresh: bool = False

class StartAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    cached: bool = False
    cached_at: Optional[str] = None

class MermaidRetryRequest(BaseModel):
    broken_mermaid_code: str
    error_message: str

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

@router.post("/analysis/start", response_model=StartAnalysisResponse)
def start_analysis_endpoint(req: StartAnalysisRequest):
    """Start a new repository analysis or return cached results"""
    try:
        # Check if analysis already exists (unless force_refresh is requested)
        if not req.force_refresh:
            existing = get_existing_analysis_by_url(str(req.repo_url))
            if existing and existing["status"] == "complete":
                return StartAnalysisResponse(
                    analysis_id=existing["analysis_id"],
                    status="complete",
                    cached=True,
                    cached_at=existing["updated_at"] or existing["created_at"]
                )
        
        # Generate a simple analysis ID
        analysis_id = f"analysis_{hash(str(req.repo_url)) % 100000}"
        
        # Check if we're refreshing an existing analysis
        existing = get_existing_analysis_by_url(str(req.repo_url))
        if existing and req.force_refresh:
            # Use the existing analysis ID for refresh
            analysis_id = existing["analysis_id"]
        
        # Run the analysis
        result = run_analysis(analysis_id, str(req.repo_url), req.force_refresh)
        
        # Store or update the result
        if existing and req.force_refresh:
            # Update existing analysis
            update_existing_analysis_data(analysis_id, result)
        else:
            # Save as new analysis
            save_analysis_summary(analysis_id, result)
        
        return StartAnalysisResponse(
            analysis_id=analysis_id,
            status="complete",
            cached=False
        )
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Analysis failed due to quota exhaustion: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/refresh", response_model=StartAnalysisResponse)
def refresh_analysis_endpoint(req: StartAnalysisRequest):
    """Refresh an existing repository analysis"""
    try:
        # Check if analysis exists
        existing = get_existing_analysis_by_url(str(req.repo_url))
        if not existing:
            raise HTTPException(
                status_code=404, 
                detail="No previous analysis found for this repository. Please run a new analysis first."
            )
        
        # Use existing analysis ID
        analysis_id = existing["analysis_id"]
        
        # Run fresh analysis
        result = run_analysis(analysis_id, str(req.repo_url), force_refresh=True)
        
        # Update existing analysis
        update_existing_analysis_data(analysis_id, result)
        
        return StartAnalysisResponse(
            analysis_id=analysis_id,
            status="complete",
            cached=False
        )
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Refresh failed due to quota exhaustion: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}")
def get_analysis_endpoint(analysis_id: str):
    """Get analysis results by ID"""
    try:
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}/focus/{module_path:path}", response_model=FocusedAnalysisResponse)
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

@router.get("/analysis/{analysis_id}/dependency-insights", response_model=DependencyInsightsResponse)
def get_dependency_insights(analysis_id: str):
    """Get enhanced dependency insights and statistics"""
    try:
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        dependency_analysis = result.get("metrics", {}).get("dependency_analysis", {})
        
        if not dependency_analysis:
            raise HTTPException(status_code=404, detail="No dependency analysis available")
        
        # Calculate additional insights
        internal_edges = dependency_analysis.get("internal_edges", [])
        external_groups = dependency_analysis.get("external_groups", {})
        
        # Module connection statistics
        module_stats = {}
        for edge in internal_edges:
            src, dst = edge["src"], edge["dst"]
            
            if src not in module_stats:
                module_stats[src] = {"outgoing": 0, "incoming": 0}
            if dst not in module_stats:
                module_stats[dst] = {"outgoing": 0, "incoming": 0}
                
            module_stats[src]["outgoing"] += 1
            module_stats[dst]["incoming"] += 1
        
        # Find most connected modules
        most_connected = sorted(
            [(mod, stats["outgoing"] + stats["incoming"]) for mod, stats in module_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # External dependency statistics
        external_stats = {}
        for category, deps in external_groups.items():
            unique_deps = set(dst for src, dst in deps)
            modules_using = set(src for src, dst in deps)
            external_stats[category] = {
                "unique_packages": len(unique_deps),
                "modules_using": len(modules_using),
                "total_imports": len(deps)
            }
        
        return DependencyInsightsResponse(
            summary=dependency_analysis.get("summary", {}),
            most_connected_modules=[{"module": mod, "connections": conn} for mod, conn in most_connected],
            external_category_stats=external_stats,
            module_statistics={
                "total_modules": len(module_stats),
                "average_connections": sum(stats["outgoing"] + stats["incoming"] 
                                         for stats in module_stats.values()) / len(module_stats) if module_stats else 0,
                "most_dependencies": max((stats["outgoing"] for stats in module_stats.values()), default=0),
                "most_dependents": max((stats["incoming"] for stats in module_stats.values()), default=0)
            },
            recommendations=generate_dependency_recommendations(dependency_analysis)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_dependency_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on dependency analysis"""
    recommendations = []
    
    external_groups = analysis.get("external_groups", {})
    internal_count = analysis.get("summary", {}).get("internal_count", 0)
    external_count = analysis.get("summary", {}).get("external_count", 0)
    
    # High external dependency ratio
    if external_count > internal_count * 3:
        recommendations.append("Consider consolidating external dependencies - high external/internal ratio detected")
    
    # Too many categories
    if len(external_groups) > 8:
        recommendations.append("Consider grouping similar dependencies - many categories detected")
    
    # Standard library usage
    stdlib_count = len(external_groups.get("Standard Library", []))
    if stdlib_count > external_count * 0.4:
        recommendations.append("High standard library usage - consider if all imports are necessary")
    
    # Development dependencies in production
    dev_deps = external_groups.get("Testing", []) + external_groups.get("Build/Config", [])
    if len(dev_deps) > 10:
        recommendations.append("Review development dependencies - ensure proper separation from production code")
    
    if not recommendations:
        recommendations.append("Dependency structure looks well-organized")
    
    return recommendations


@router.post("/analysis/{analysis_id}/diagram/{mode}")
def generate_diagram_on_demand(analysis_id: str, mode: str):
    """Generate a specific diagram mode on-demand and save it to the database"""
    try:
        # Validate mode
        if mode not in ["simple", "balanced", "detailed"]:
            raise HTTPException(status_code=400, detail="Invalid diagram mode. Only 'simple', 'balanced', and 'detailed' are supported for on-demand generation.")
        
        # Get existing analysis
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        dependency_analysis = result.get("metrics", {}).get("dependency_analysis", {})
        if not dependency_analysis:
            raise HTTPException(status_code=404, detail="No dependency analysis available")
        
        # Generate the specific diagram mode
        file_infos = [{"path": f"dummy"} for _ in range(result.get("file_count", 0))]  # Minimal file_infos for LLM context
        json_graph = result.get("metrics", {}).get("graph", {"edges": []})
        architecture_md = result.get("artifacts", {}).get("architecture_md", "")
        
        diagram_content = generate_single_diagram_mode(
            dependency_analysis, 
            json_graph, 
            file_infos, 
            mode,
            architecture_md
        )
        
        if not diagram_content:
            raise HTTPException(status_code=500, detail=f"Failed to generate diagram for mode: {mode}")
        
        # Update the database with the new diagram
        diagram_key = f"mermaid_modules_{mode}"
        update_analysis_artifact(analysis_id, diagram_key, diagram_content)
        
        return {
            "mode": mode,
            "diagram": diagram_content,
            "status": "generated"
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Diagram generation failed due to quota exhaustion: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/{analysis_id}/diagram/{mode}/retry")
def retry_mermaid_diagram(analysis_id: str, mode: str, request: MermaidRetryRequest):
    """Retry correcting a broken Mermaid diagram and save the corrected version to the database"""
    try:
        print(f"🔄 Starting Mermaid correction - Analysis: {analysis_id}, Mode: {mode}")
        print(f"   Concise error: {request.error_message[:100]}{'...' if len(request.error_message) > 100 else ''}")
        print(f"   Broken code length: {len(request.broken_mermaid_code)}")
        
        # Validate mode
        valid_modes = ["simple", "balanced", "detailed", "folders"]
        if mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid diagram mode. Supported modes: {', '.join(valid_modes)}")
        
        # Get existing analysis to verify it exists
        result = get_analysis(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Prepare the correction prompt
        user_prompt = MERMAID_CORRECTION_USER_TMPL.format(
            broken_mermaid_code=request.broken_mermaid_code,
            error_message=request.error_message
        )
        
        print(f"🤖 Sending correction request to LLM...")
        
        # Generate corrected Mermaid code using LLM
        corrected_diagram = generate_mermaid_correction(
            MERMAID_CORRECTION_SYSTEM,
            user_prompt
        )
        
        if not corrected_diagram or corrected_diagram.strip() == "":
            print(f"❌ LLM failed to generate corrected diagram")
            raise HTTPException(status_code=500, detail="Failed to generate corrected diagram")
        
        print(f"✅ LLM generated corrected diagram - Length: {len(corrected_diagram)}")
        
        # Update the database with the corrected diagram
        diagram_key_mapping = {
            "simple": "mermaid_modules_simple",
            "balanced": "mermaid_modules_balanced", 
            "detailed": "mermaid_modules_detailed",
            "folders": "mermaid_folders"
        }
        
        diagram_key = diagram_key_mapping[mode]
        update_analysis_artifact(analysis_id, diagram_key, corrected_diagram)
        
        print(f"💾 Saved corrected diagram to database with key: {diagram_key}")
        
        return {
            "mode": mode,
            "original_diagram": request.broken_mermaid_code,
            "corrected_diagram": corrected_diagram,
            "status": "corrected"
        }
    
    except (GeminiQuotaExhaustedError, GeminiAPIError) as e:
        print(f"🚫 Mermaid correction failed due to LLM error: {e}")
        raise HTTPException(
            status_code=429, 
            detail="quota_exhausted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in retry_mermaid_diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 