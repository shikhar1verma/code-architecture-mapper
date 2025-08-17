import ast
from typing import List, Dict

PY_EXTS = {".py"}


def is_python(path: str) -> bool:
    return any(path.endswith(ext) for ext in PY_EXTS)


def py_import_edges(path: str, code: str) -> List[Dict[str, str]]:
    edges = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod:
                        edges.append({"src": path, "dst": mod})
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    edges.append({"src": path, "dst": mod})
    except Exception:
        pass
    return edges 