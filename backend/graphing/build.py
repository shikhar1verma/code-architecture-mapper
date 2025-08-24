import os
import networkx as nx
from typing import Dict, List, Any, Set
from collections import defaultdict
import re


def normalize_internal_edge(root: str, edge: Dict[str, str]) -> Dict[str, str]:
    src = edge["src"]  # Don't re-normalize; it's already relative from pipeline
    dst = edge["dst"]
    # if dst is a path-like import (./x or ../x), resolve to a file stem
    if dst.startswith("./") or dst.startswith("../"):
        dst_path = os.path.normpath(os.path.join(os.path.dirname(src), dst))
        return {"src": src, "dst": dst_path}
    # else it's likely a package/module; keep as module label
    return {"src": src, "dst": dst}


def is_external_dependency(node: str) -> bool:
    """Check if a node is an external dependency (not a project file)"""
    return not ("/" in node or node.endswith((".py", ".js", ".ts", ".tsx", ".jsx")))


def is_standard_library(dep: str) -> bool:
    """Check if dependency is a standard library (should be de-prioritized)"""
    python_stdlib = {
        'os', 'sys', 'json', 'time', 'datetime', 'collections', 'itertools',
        'functools', 're', 'math', 'random', 'urllib', 'http', 'pathlib',
        'typing', 'dataclasses', 'enum', 'abc', 'asyncio', 'concurrent',
        'logging', 'unittest', 'pytest', 'sqlite3', 'csv', 'xml', 'html'
    }
    
    js_stdlib = {
        'react', 'react-dom', 'next', 'express', 'lodash', 'axios', 'fs',
        'path', 'crypto', 'util', 'events', 'stream', 'buffer', 'url',
        'http', 'https', 'querystring', 'zlib'
    }
    
    dep_lower = dep.lower().split('/')[0].split('.')[0]
    return dep_lower in python_stdlib or dep_lower in js_stdlib


def categorize_dependency(dep: str) -> str:
    """Categorize dependencies into logical groups"""
    dep_lower = dep.lower()
    
    # UI/Frontend
    if any(x in dep_lower for x in ['react', 'vue', 'angular', 'svelte', 'next', 'gatsby', 'ui', 'component', 'style', 'css', 'tailwind']):
        return "Frontend/UI"
    
    # Backend/API
    elif any(x in dep_lower for x in ['express', 'fastapi', 'flask', 'django', 'koa', 'hapi', 'api', 'server', 'middleware']):
        return "Backend/API"
    
    # Database
    elif any(x in dep_lower for x in ['sql', 'mongo', 'redis', 'postgres', 'mysql', 'sqlite', 'db', 'database', 'orm', 'prisma', 'typeorm']):
        return "Database"
    
    # Testing
    elif any(x in dep_lower for x in ['test', 'spec', 'jest', 'mocha', 'pytest', 'unittest', 'cypress', 'selenium']):
        return "Testing"
    
    # Build/Config
    elif any(x in dep_lower for x in ['webpack', 'babel', 'eslint', 'prettier', 'rollup', 'vite', 'config', 'env', 'dotenv']):
        return "Build/Config"
    
    # Utilities
    elif any(x in dep_lower for x in ['util', 'helper', 'tool', 'lodash', 'moment', 'date-fns', 'uuid', 'crypto']):
        return "Utilities"
    
    # Standard Library
    elif is_standard_library(dep):
        return "Standard Library"
    
    else:
        return "External Libraries"


def filter_and_group_dependencies(edges: List[Dict[str, str]], complexity_level: str = "balanced") -> Dict[str, Any]:
    """
    Intelligently filter and group dependencies based on complexity level
    
    complexity_level:
    - "simple": Show only key internal dependencies + major external groups
    - "balanced": Show internal + categorized external dependencies  
    - "detailed": Show most dependencies with smart grouping
    """
    
    # Separate internal vs external edges
    internal_edges = []
    external_deps = defaultdict(list)
    
    for edge in edges:
        src, dst = edge["src"], edge["dst"]
        
        if is_external_dependency(dst):
            category = categorize_dependency(dst)
            external_deps[category].append((src, dst))
        else:
            internal_edges.append(edge)
    
    result = {
        "internal_edges": internal_edges,
        "external_groups": dict(external_deps),
        "summary": {
            "internal_count": len(internal_edges),
            "external_count": sum(len(deps) for deps in external_deps.values()),
            "categories": list(external_deps.keys())
        }
    }
    
    # Apply complexity filtering
    if complexity_level == "simple":
        # Only keep major categories and limit external deps
        major_categories = ["Frontend/UI", "Backend/API", "Database", "Testing"]
        filtered_external = {cat: deps for cat, deps in external_deps.items() 
                           if cat in major_categories and len(deps) >= 2}
        result["external_groups"] = filtered_external
        
    elif complexity_level == "balanced":
        # Remove standard library, limit per category
        filtered_external = {}
        for cat, deps in external_deps.items():
            if cat != "Standard Library":
                # Limit to top dependencies per category
                filtered_external[cat] = deps[:10]
        result["external_groups"] = filtered_external
    
    return result


def build_graph(root: str, file_infos: List[Dict[str, Any]], edges: List[Dict[str, str]]):
    G = nx.DiGraph()
    for fi in file_infos:
        G.add_node(fi["path"], **{k: fi[k] for k in ("language", "loc")})

    # normalize edges, keep internal ones preferentially
    norm_edges = [normalize_internal_edge(root, e) for e in edges]
    for e in norm_edges:
        if e["src"] not in G:
            G.add_node(e["src"])  # tolerate missing
        G.add_edge(e["src"], e["dst"])

    metrics = {}
    fan_in = {n: G.in_degree(n) for n in G.nodes}
    fan_out = {n: G.out_degree(n) for n in G.nodes}
    deg_cent = nx.degree_centrality(G) if len(G) > 0 else {}

    metrics["fan_in"] = fan_in
    metrics["fan_out"] = fan_out
    metrics["degree_centrality"] = deg_cent

    # rank top files among those that are real files
    real_nodes = [n for n in G.nodes if "/" in n or \
                  n.endswith(".py") or n.endswith(".ts") or n.endswith(".js")]
    top = sorted(real_nodes, key=lambda n: deg_cent.get(n, 0.0), reverse=True)
    metrics["top_files"] = top[:50]

    # Add intelligent dependency analysis
    dependency_analysis = filter_and_group_dependencies(norm_edges)
    metrics["dependency_analysis"] = dependency_analysis

    # lightweight json graph
    json_graph = {
        "nodes": [{"id": n, "fan_in": fan_in.get(n, 0), "fan_out": fan_out.get(n, 0)} for n in G.nodes],
        "edges": [{"source": u, "target": v} for u, v in G.edges]
    }
    return metrics, json_graph 