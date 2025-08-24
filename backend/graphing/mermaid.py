import re
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
import json

# ---------- Public API ----------

def mermaid_architecture(
    components: List[Dict[str, str]],
    edges: List[Tuple[str, str, Optional[str]]],
    direction: str = "LR",
    title: Optional[str] = None,
) -> str:
    """
    Build a polished Mermaid architecture diagram.

    components: list of dicts with fields:
        - id (required): unique identifier
        - label (optional): display label (defaults to id)
        - cls (optional): 'module' | 'component' | 'config' | 'test' | 'service' | 'db' | 'cache' | 'queue' | 'ext' | custom
        - group (optional): subgraph name (e.g., 'Frontend', 'Backend', 'Services', 'Config', 'Tests', 'External')

    edges: list of tuples (src_id, dst_id, label) where label can be None/''

    direction: 'LR' or 'TD'
    title: optional diagram title (rendered as a comment in the graph)
    """
    init = _init_block()
    header = f"flowchart {direction}"
    lines = [init, header]
    if title:
        lines.append(f"%% {title}")

    # Group components into subgraphs
    group_map = defaultdict(list)
    by_id = {}
    for c in components:
        cid = _safe(c["id"])
        by_id[cid] = c
        group_map[c.get("group", "Ungrouped")].append(c)

    # Render groups/subgraphs
    for group_name, items in group_map.items():
        if group_name == "Ungrouped" and len(group_map) > 1:
            # Skip ungrouped if we have other groups, render them separately
            continue
        gid = _safe(group_name)
        lines.append(f"subgraph {gid}[{group_name}]")
        lines.append("direction TB")
        for c in items:
            cid = _safe(c["id"])
            label = c.get("label", c["id"])
            cls = c.get("cls", "module")
            # Square-ish node with readable label
            lines.append(f'{cid}["{label}"]:::{_safe(cls)}')
        lines.append("end")

    # Render ungrouped items separately if there are groups
    if "Ungrouped" in group_map and len(group_map) > 1:
        for c in group_map["Ungrouped"]:
            cid = _safe(c["id"])
            label = c.get("label", c["id"])
            cls = c.get("cls", "module")
            lines.append(f'{cid}["{label}"]:::{_safe(cls)}')

    # Render edges with optional labels; de-dup exactly
    seen = set()
    for src, dst, lbl in edges:
        key = (src, dst, lbl or "")
        if key in seen:
            continue
        seen.add(key)
        src_id, dst_id = _safe(src), _safe(dst)
        if lbl:
            lines.append(f'{src_id} -- "{_escape(lbl)}" --> {dst_id}')
        else:
            lines.append(f"{src_id} --> {dst_id}")

    # Class definitions (code-architecture optimized palette)
    lines += _class_defs()
    # Global link style
    lines.append("linkStyle default stroke:#64748b,stroke-width:1.5px;")

    return "\n".join(lines)


def intelligent_modules_mermaid(
    dependency_analysis: Dict[str, Any],
    mode: str = "balanced",
    focus_module: Optional[str] = None,
    direction: str = "LR",
    title: Optional[str] = None
) -> str:
    """
    Create intelligent dependency diagrams based on analysis
    
    mode: 'simple' | 'balanced' | 'detailed'
    focus_module: Optional module to focus visualization on
    """
    
    if mode == "simple":
        return _create_simple_overview(dependency_analysis, direction, title)
    elif mode == "detailed":
        return _create_detailed_view(dependency_analysis, direction, title)
    elif mode == "focused" and focus_module:
        return _create_focused_view(dependency_analysis, focus_module, direction, title)
    else:  # balanced
        return _create_balanced_view(dependency_analysis, direction, title)


def _create_simple_overview(analysis: Dict[str, Any], direction: str, title: Optional[str]) -> str:
    """Create a high-level overview showing only major groups"""
    components = []
    edges = []
    
    # Create components for major external categories
    external_groups = analysis.get("external_groups", {})
    for category, deps in external_groups.items():
        if len(deps) >= 2:  # Only show categories with multiple dependencies
            components.append({
                "id": category.replace("/", "_").replace(" ", "_"),
                "label": category,
                "cls": "ext",
                "group": "External Dependencies"
            })
    
    # Add internal project group
    internal_count = analysis["summary"]["internal_count"]
    if internal_count > 0:
        components.append({
            "id": "ProjectModules",
            "label": f"Project Modules ({internal_count})",
            "cls": "module",
            "group": "Internal"
        })
        
        # Connect project to external groups
        for category in external_groups.keys():
            if len(external_groups[category]) >= 2:
                edges.append(("ProjectModules", category.replace("/", "_").replace(" ", "_"), None))
    
    return mermaid_architecture(components, edges, direction, title or "Architecture Overview")


def _create_balanced_view(analysis: Dict[str, Any], direction: str, title: Optional[str]) -> str:
    """Create a balanced view with grouped internal modules and categorized externals"""
    components = []
    edges = []
    
    # Group internal modules by directory/component
    internal_edges = analysis.get("internal_edges", [])
    internal_modules = set()
    
    for edge in internal_edges:
        internal_modules.add(edge["src"])
        internal_modules.add(edge["dst"])
    
    # Group internal modules
    module_groups = _group_internal_modules(list(internal_modules))
    
    # Add internal module groups as components
    for group_name, modules in module_groups.items():
        if len(modules) > 0:
            components.append({
                "id": group_name.replace("/", "_").replace(" ", "_"),
                "label": f"{group_name} ({len(modules)})",
                "cls": _infer_group_class(group_name),
                "group": "Internal Modules"
            })
    
    # Add internal edges between groups
    group_connections = set()
    for edge in internal_edges:
        src_group = _find_module_group(edge["src"], module_groups)
        dst_group = _find_module_group(edge["dst"], module_groups)
        if src_group != dst_group and (src_group, dst_group) not in group_connections:
            group_connections.add((src_group, dst_group))
            edges.append((
                src_group.replace("/", "_").replace(" ", "_"),
                dst_group.replace("/", "_").replace(" ", "_"),
                None
            ))
    
    # Add significant external dependencies
    external_groups = analysis.get("external_groups", {})
    for category, deps in external_groups.items():
        if category != "Standard Library" and len(deps) >= 1:
            components.append({
                "id": category.replace("/", "_").replace(" ", "_"),
                "label": f"{category} ({len(deps)})",
                "cls": "ext",
                "group": "External Dependencies"
            })
            
            # Connect internal groups to external dependencies
            connected_groups = set()
            for src, dst in deps:
                src_group = _find_module_group(src, module_groups)
                if src_group and src_group not in connected_groups:
                    connected_groups.add(src_group)
                    edges.append((
                        src_group.replace("/", "_").replace(" ", "_"),
                        category.replace("/", "_").replace(" ", "_"),
                        None
                    ))
    
    return mermaid_architecture(components, edges, direction, title or "Module Dependencies (Balanced)")


def _create_detailed_view(analysis: Dict[str, Any], direction: str, title: Optional[str]) -> str:
    """Create detailed view with individual modules and their relationships"""
    components = []
    edges = []
    
    internal_edges = analysis.get("internal_edges", [])
    internal_modules = set()
    
    for edge in internal_edges:
        internal_modules.add(edge["src"])
        internal_modules.add(edge["dst"])
    
    # Add individual internal modules
    for module in internal_modules:
        group = _infer_group(module)
        components.append({
            "id": module,
            "label": _clean_label(module),
            "cls": _infer_class(module),
            "group": group
        })
    
    # Add internal edges
    for edge in internal_edges:
        edges.append((edge["src"], edge["dst"], None))
    
    # Add top external dependencies individually
    external_groups = analysis.get("external_groups", {})
    for category, deps in external_groups.items():
        if category == "Standard Library":
            continue
        
        # Show top 5 deps from each category
        top_deps = list(set(dst for src, dst in deps))[:5]
        for dep in top_deps:
            components.append({
                "id": dep,
                "label": dep.split('/')[-1],  # Just the package name
                "cls": "ext",
                "group": f"External: {category}"
            })
        
        # Connect internal modules to external deps
        for src, dst in deps:
            if dst in top_deps:
                edges.append((src, dst, None))
    
    return mermaid_architecture(components, edges, direction, title or "Module Dependencies (Detailed)")


def _create_focused_view(analysis: Dict[str, Any], focus_module: str, direction: str, title: Optional[str]) -> str:
    """Create a focused view around a specific module"""
    components = []
    edges = []
    
    internal_edges = analysis.get("internal_edges", [])
    
    # Find modules connected to focus module
    connected_modules = set([focus_module])
    
    for edge in internal_edges:
        if edge["src"] == focus_module:
            connected_modules.add(edge["dst"])
        elif edge["dst"] == focus_module:
            connected_modules.add(edge["src"])
    
    # Add connected modules
    for module in connected_modules:
        group = _infer_group(module)
        components.append({
            "id": module,
            "label": _clean_label(module),
            "cls": "component" if module == focus_module else _infer_class(module),
            "group": group
        })
    
    # Add edges between connected modules
    for edge in internal_edges:
        if edge["src"] in connected_modules and edge["dst"] in connected_modules:
            edges.append((edge["src"], edge["dst"], None))
    
    # Add relevant external dependencies
    external_groups = analysis.get("external_groups", {})
    for category, deps in external_groups.items():
        relevant_deps = [(src, dst) for src, dst in deps if src == focus_module]
        for src, dst in relevant_deps:
            components.append({
                "id": dst,
                "label": dst.split('/')[-1],
                "cls": "ext",
                "group": f"External: {category}"
            })
            edges.append((src, dst, None))
    
    return mermaid_architecture(components, edges, direction, title or f"Dependencies: {focus_module}")


def modules_mermaid(
    edges: List[Dict[str, str]],
    direction: str = "LR",
    title: Optional[str] = "Module Dependencies"
) -> str:
    """
    Backward-compatible: accept your old edge dicts (source/target),
    but produce a prettier LR flow with styling and smart grouping.
    """
    # Infer nodes and categorize them
    nodes = set()
    tuples = []
    for e in edges:
        s, t = e["source"], e["target"]
        nodes.add(s); nodes.add(t)
        tuples.append((s, t, None))

    # Smart grouping based on file paths/names
    components = []
    for n in sorted(nodes):
        group = _infer_group(n)
        cls = _infer_class(n)
        label = _clean_label(n)
        components.append({
            "id": n, 
            "label": label, 
            "cls": cls, 
            "group": group
        })
    
    return mermaid_architecture(components, tuples, direction=direction, title=title)


def folders_mermaid(
    file_paths: List[str],
    max_depth: int = 3,
    direction: str = "LR",
    title: Optional[str] = "Project Structure"
) -> str:
    """
    Render a folder tree as nested subgraphs with folder-styled nodes.
    Enhanced for code project structures.
    """
    # Build folder hierarchy
    folders = set()
    files = set()
    
    for path in file_paths:
        parts = [part for part in path.split("/") if part]
        # Add all folder levels up to max_depth
        for i in range(1, min(len(parts), max_depth) + 1):
            folder_path = "/".join(parts[:i])
            if i < len(parts):  # It's a folder
                folders.add(folder_path)
            else:  # It's a file
                files.add(folder_path)

    # Create components for folders and files
    components = []
    edges = []
    
    # Add folder components
    for folder in sorted(folders):
        parts = folder.split("/")
        label = parts[-1]
        group = _infer_folder_group(folder)
        components.append({
            "id": folder,
            "label": label,
            "cls": "folder",
            "group": group
        })
    
    # Add file components
    for file in sorted(files):
        parts = file.split("/")
        label = parts[-1]
        group = _infer_folder_group(file)
        cls = _infer_file_class(file)
        components.append({
            "id": file,
            "label": label,
            "cls": cls,
            "group": group
        })
    
    # Create hierarchy edges
    all_paths = folders | files
    for path in all_paths:
        parts = path.split("/")
        if len(parts) > 1:
            parent = "/".join(parts[:-1])
            if parent in all_paths:
                edges.append((parent, path, None))

    return mermaid_architecture(components, edges, direction=direction, title=title)


# ---------- New Helper Functions ----------

def _group_internal_modules(modules: List[str]) -> Dict[str, List[str]]:
    """Group internal modules by logical components"""
    groups = defaultdict(list)
    
    for module in modules:
        # Determine group based on path
        parts = module.split('/')
        
        if len(parts) >= 2:
            # Use directory structure
            if parts[0] in ['src', 'app', 'lib']:
                group_name = parts[1] if len(parts) > 1 else parts[0]
            else:
                group_name = parts[0]
        else:
            group_name = "Root"
        
        # Clean group name
        group_name = group_name.replace('_', ' ').replace('-', ' ').title()
        groups[group_name].append(module)
    
    return dict(groups)


def _find_module_group(module: str, module_groups: Dict[str, List[str]]) -> Optional[str]:
    """Find which group a module belongs to"""
    for group_name, modules in module_groups.items():
        if module in modules:
            return group_name
    return "Unknown"


def _infer_group_class(group_name: str) -> str:
    """Infer CSS class for module group"""
    name_lower = group_name.lower()
    
    if any(x in name_lower for x in ['component', 'ui', 'frontend']):
        return "component"
    elif any(x in name_lower for x in ['service', 'api', 'backend']):
        return "service"
    elif any(x in name_lower for x in ['test', 'spec']):
        return "test"
    elif any(x in name_lower for x in ['config', 'settings']):
        return "config"
    else:
        return "module"


# ---------- Existing Helper Functions ----------

def _init_block() -> str:
    # Professional theme optimized for code architecture diagrams
    return (
        "%%{init: { 'theme': 'base', 'themeVariables': {"
        " 'primaryColor': '#f8fafc',"
        " 'primaryTextColor': '#0f172a',"
        " 'lineColor': '#64748b',"
        " 'textColor': '#1e293b',"
        " 'background': '#ffffff',"
        " 'secondaryColor': '#f1f5f9',"
        " 'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif',"
        " 'fontSize': '14px'"
        " }}}%%"
    )

def _class_defs() -> List[str]:
    """Code-architecture optimized class definitions"""
    return [
        "classDef module fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e40af;",
        "classDef component fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#15803d;",
        "classDef config fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;",
        "classDef test fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#7c3aed;",
        "classDef service fill:#e0f2fe,stroke:#0369a1,stroke-width:2px,color:#0c4a6e;",
        "classDef db fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12;",
        "classDef cache fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#064e3b;",
        "classDef queue fill:#fae8ff,stroke:#a855f7,stroke-width:2px,color:#6b21a8;",
        "classDef ext fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;",
        "classDef folder fill:#f1f5f9,stroke:#64748b,stroke-width:1.5px,color:#334155;",
        "classDef utility fill:#f0f9ff,stroke:#0284c7,stroke-width:2px,color:#0369a1;",
    ]

def _infer_group(node_name: str) -> str:
    """Infer logical group from node name"""
    name_lower = node_name.lower()
    
    if any(x in name_lower for x in ['frontend', 'client', 'ui', 'web', 'react', 'vue', 'angular']):
        return "Frontend"
    elif any(x in name_lower for x in ['backend', 'server', 'api', 'service']):
        return "Backend"
    elif any(x in name_lower for x in ['config', 'settings', 'env']):
        return "Configuration"
    elif any(x in name_lower for x in ['test', 'spec', '__tests__']):
        return "Tests"
    elif any(x in name_lower for x in ['util', 'helper', 'lib', 'common']):
        return "Utilities"
    elif any(x in name_lower for x in ['db', 'database', 'model', 'schema']):
        return "Data"
    else:
        return "Core"

def _infer_class(node_name: str) -> str:
    """Infer node class from name"""
    name_lower = node_name.lower()
    
    if any(x in name_lower for x in ['test', 'spec']):
        return "test"
    elif any(x in name_lower for x in ['config', 'settings', '.env', 'package.json', 'tsconfig']):
        return "config"
    elif any(x in name_lower for x in ['util', 'helper', 'lib']):
        return "utility"
    elif any(x in name_lower for x in ['service', 'api']):
        return "service"
    elif any(x in name_lower for x in ['component', 'widget']):
        return "component"
    elif any(x in name_lower for x in ['db', 'database', 'model']):
        return "db"
    else:
        return "module"

def _infer_folder_group(path: str) -> str:
    """Infer group for folder structure"""
    path_lower = path.lower()
    
    if path_lower.startswith('frontend') or any(x in path_lower for x in ['src/components', 'src/pages', 'public']):
        return "Frontend"
    elif path_lower.startswith('backend') or any(x in path_lower for x in ['api', 'server', 'services']):
        return "Backend"
    elif any(x in path_lower for x in ['test', 'spec', '__tests__']):
        return "Tests"
    elif any(x in path_lower for x in ['config', 'settings', 'env']):
        return "Configuration"
    elif any(x in path_lower for x in ['docs', 'documentation']):
        return "Documentation"
    else:
        return "Project Root"

def _infer_file_class(file_path: str) -> str:
    """Infer class for individual files"""
    file_lower = file_path.lower()
    
    if file_lower.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts', '_test.py')):
        return "test"
    elif file_lower.endswith(('.config.js', '.config.ts', 'package.json', 'tsconfig.json', '.env')):
        return "config"
    elif any(x in file_lower for x in ['component', 'widget']) and file_lower.endswith(('.tsx', '.jsx')):
        return "component"
    elif file_lower.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
        return "module"
    else:
        return "utility"

def _clean_label(name: str) -> str:
    """Clean up node labels for better readability"""
    # Remove common prefixes/suffixes and clean up
    cleaned = name.replace("_", " ").replace("-", " ")
    # For file paths, just show the filename
    if "/" in name:
        cleaned = name.split("/")[-1]
    # Capitalize words
    return " ".join(word.capitalize() for word in cleaned.split())

def _safe(s: str) -> str:
    """Mermaid node IDs: keep alnum and underscores only"""
    return re.sub(r"[^A-Za-z0-9_]", "_", s)

def _escape(s: str) -> str:
    """Escape double quotes inside edge labels"""
    return s.replace('"', '\\"') 