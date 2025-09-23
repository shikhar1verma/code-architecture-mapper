"""
Core Mermaid diagram building functionality

This module contains the foundational diagram building functions,
themes, and basic utilities extracted from mermaid.py for better organization.
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


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
    init = get_theme_block()
    header = f"flowchart {direction}"
    lines = [init, header]
    if title:
        lines.append(f"%% {title}")

    # Group components into subgraphs
    group_map = defaultdict(list)
    by_id = {}
    for c in components:
        cid = safe_node_id(c["id"])
        by_id[cid] = c
        group_map[c.get("group", "Ungrouped")].append(c)

    # Render groups/subgraphs
    for group_name, items in group_map.items():
        if group_name == "Ungrouped" and len(group_map) > 1:
            # Skip ungrouped if we have other groups, render them separately
            continue
        gid = safe_node_id(group_name)
        lines.append(f"subgraph {gid}[{group_name}]")
        lines.append("direction TB")
        for c in items:
            cid = safe_node_id(c["id"])
            label = c.get("label", c["id"])
            cls = c.get("cls", "module")
            # Square-ish node with readable label
            lines.append(f'{cid}["{label}"]:::{safe_node_id(cls)}')
        lines.append("end")

    # Render ungrouped items separately if there are groups
    if "Ungrouped" in group_map and len(group_map) > 1:
        for c in group_map["Ungrouped"]:
            cid = safe_node_id(c["id"])
            label = c.get("label", c["id"])
            cls = c.get("cls", "module")
            lines.append(f'{cid}["{label}"]:::{safe_node_id(cls)}')

    # Render edges with optional labels; de-dup exactly
    seen = set()
    for src, dst, lbl in edges:
        key = (src, dst, lbl or "")
        if key in seen:
            continue
        seen.add(key)
        src_id, dst_id = safe_node_id(src), safe_node_id(dst)
        if lbl:
            lines.append(f'{src_id} -- "{escape_label(lbl)}" --> {dst_id}')
        else:
            lines.append(f"{src_id} --> {dst_id}")

    # Class definitions (code-architecture optimized palette)
    lines += get_class_definitions()
    # Global link style
    lines.append("linkStyle default stroke:#64748b,stroke-width:1.5px;")

    return "\n".join(lines)


def get_theme_block() -> str:
    """Professional theme optimized for code architecture diagrams"""
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


def get_class_definitions() -> List[str]:
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


def safe_node_id(s: str) -> str:
    """Make string safe for Mermaid node IDs: keep alnum and underscores only"""
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def escape_label(s: str) -> str:
    """Escape special characters in edge labels to prevent Mermaid parsing issues"""
    # Replace double quotes with escaped quotes
    escaped = s.replace('"', '\\"')
    
    # Handle markdown-like syntax that Mermaid might misinterpret
    # Escape numbered lists (e.g., "1. " -> "1\\. ")
    escaped = re.sub(r'(\d+)\.(\s)', r'\1\\.\2', escaped)
    
    # Escape bullet points (e.g., "- " -> "\\- ")
    escaped = re.sub(r'^[\s]*[-*+](\s)', r'\\-\1', escaped)
    
    # Escape hash symbols that might be interpreted as headers
    escaped = escaped.replace('#', '\\#')
    
    return escaped


def clean_label(name: str) -> str:
    """Clean up node labels for better readability"""
    # Remove common prefixes/suffixes and clean up
    cleaned = name.replace("_", " ").replace("-", " ")
    # For file paths, just show the filename
    if "/" in name:
        cleaned = name.split("/")[-1]
    # Capitalize words
    return " ".join(word.capitalize() for word in cleaned.split()) 