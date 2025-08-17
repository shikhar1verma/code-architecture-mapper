import re
from typing import List, Dict

TS_EXTS = {".ts", ".tsx", ".js", ".jsx"}
IMPORT_RE = re.compile(r"import\s+[^\n]*?from\s+['\"]([^'\"]+)['\"]|require\(\s*['\"]([^'\"]+)['\"]\s*\)")


def is_ts(path: str) -> bool:
    return any(path.endswith(ext) for ext in TS_EXTS)


def ts_import_edges(path: str, code: str) -> List[Dict[str, str]]:
    edges = []
    for m in IMPORT_RE.finditer(code):
        pkg = m.group(1) or m.group(2)
        if not pkg:
            continue
        # only keep relative internal imports (./ or ../)
        if pkg.startswith("./") or pkg.startswith("../"):
            edges.append({"src": path, "dst": pkg})
    return edges 