import os
from typing import List, Dict


def modules_mermaid(edges: List[Dict[str, str]]) -> str:
    lines = ["graph TD;"]
    seen = set()
    for e in edges:
        key = (e["source"], e["target"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"{_safe(e['source'])}--> {_safe(e['target'])};")
    return "\n".join(lines)


def folders_mermaid(file_paths: List[str], max_depth: int = 3) -> str:
    # simple folder tree (up to depth)
    lines = ["graph TD;"]
    for p in file_paths:
        parts = p.split("/")
        for i in range(min(len(parts)-1, max_depth)):
            a = "/".join(parts[:i+1])
            b = "/".join(parts[:i+2])
            lines.append(f"{_safe(a)}--> {_safe(b)};")
    return "\n".join(sorted(set(lines)))


def _safe(s: str) -> str:
    return s.replace("-", "_").replace(".", "_").replace("/", "_") 