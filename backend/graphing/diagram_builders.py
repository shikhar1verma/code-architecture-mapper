"""
Specialized diagram builders

This module contains functions for building different types of diagrams:
intelligent modules, backward-compatible modules, and folder structures.
"""

from typing import List, Dict, Optional, Any
from .mermaid_core import mermaid_architecture, clean_label
from .diagram_utils import NodeClassifier, ModuleGrouper, FolderOrganizer


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
    classifier = NodeClassifier()
    for n in sorted(nodes):
        group = classifier.infer_group(n)
        cls = classifier.infer_class(n)
        label = clean_label(n)
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
    organizer = FolderOrganizer()
    classifier = NodeClassifier()
    
    folders, files = organizer.build_folder_hierarchy(file_paths, max_depth)
    
    # Create components for folders and files
    components = []
    
    # Add folder components
    for folder in sorted(folders):
        parts = folder.split("/")
        label = parts[-1]
        group = classifier.infer_folder_group(folder)
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
        group = classifier.infer_folder_group(file)
        cls = classifier.infer_file_class(file)
        components.append({
            "id": file,
            "label": label,
            "cls": cls,
            "group": group
        })
    
    # Create hierarchy edges
    all_paths = folders | files
    edges = organizer.create_hierarchy_edges(all_paths)

    return mermaid_architecture(components, edges, direction=direction, title=title)


# ========================================================================
# Mode-specific intelligent diagram builders
# ========================================================================

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
    grouper = ModuleGrouper()
    classifier = NodeClassifier()
    module_groups = grouper.group_internal_modules(list(internal_modules))
    
    # Add internal module groups as components
    for group_name, modules in module_groups.items():
        if len(modules) > 0:
            components.append({
                "id": group_name.replace("/", "_").replace(" ", "_"),
                "label": f"{group_name} ({len(modules)})",
                "cls": classifier.infer_group_class(group_name),
                "group": "Internal Modules"
            })
    
    # Add internal edges between groups
    group_connections = set()
    for edge in internal_edges:
        src_group = grouper.find_module_group(edge["src"], module_groups)
        dst_group = grouper.find_module_group(edge["dst"], module_groups)
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
                src_group = grouper.find_module_group(src, module_groups)
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
    classifier = NodeClassifier()
    for module in internal_modules:
        group = classifier.infer_group(module)
        components.append({
            "id": module,
            "label": clean_label(module),
            "cls": classifier.infer_class(module),
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
    classifier = NodeClassifier()
    for module in connected_modules:
        group = classifier.infer_group(module)
        components.append({
            "id": module,
            "label": clean_label(module),
            "cls": "component" if module == focus_module else classifier.infer_class(module),
            "group": group
        })
    
    # Add edges between connected modules
    for edge in internal_edges:
        if edge["src"] in connected_modules and edge["dst"] in connected_modules:
            edges.append((edge["src"], edge["dst"], None))
    
    # Add relevant external dependencies
    external_groups = analysis.get("external_groups", {})
    for category, deps in external_groups.items():
        # Handle both tuple format (legacy) and dict format (new hybrid approach)
        relevant_deps = []
        for dep in deps:
            if isinstance(dep, dict):
                if dep["src"] == focus_module:
                    relevant_deps.append((dep["src"], dep["dst"]))
            else:
                # Legacy tuple format (src, dst)
                if dep[0] == focus_module:
                    relevant_deps.append(dep)
        
        for src, dst in relevant_deps:
            components.append({
                "id": dst,
                "label": dst.split('/')[-1],
                "cls": "ext",
                "group": f"External: {category}"
            })
            edges.append((src, dst, None))
    
    return mermaid_architecture(components, edges, direction, title or f"Dependencies: {focus_module}") 