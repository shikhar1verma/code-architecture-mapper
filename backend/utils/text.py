from typing import Iterable

def read_text(path: str, max_bytes: int = 200_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def chunk_text(s: str, size: int = 1400, overlap: int = 100) -> Iterable[str]:
    if not s:
        return []
    out = []
    i = 0
    n = len(s)
    while i < n:
        out.append(s[i:i+size])
        i += size - overlap
    return out 