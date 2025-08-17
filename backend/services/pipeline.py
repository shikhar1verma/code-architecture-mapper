import os
from typing import Dict, Any, List
from collections import Counter

from backend.config import TOP_FILES, COMPONENT_COUNT, CHUNK_SIZE_CHARS
from backend.utils.git_tools import shallow_clone, walk_repo
from backend.utils.text import read_text, chunk_text
from backend.parsing.py_ast import is_python, py_import_edges
from backend.parsing.ts_imports import is_ts, ts_import_edges
from backend.graphing.build import build_graph
from backend.graphing.mermaid import modules_mermaid, folders_mermaid
from backend.llm.gemini import generate_markdown
from backend.llm.prompts import OVERVIEW_SYSTEM, OVERVIEW_USER_TMPL


SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def run_analysis(analysis_id: str, repo_url: str, force_refresh: bool = False) -> Dict[str, Any]:
    root, sha = shallow_clone(repo_url)

    file_infos: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []

    # scan & parse
    for abs_path in walk_repo(root):
        rel = os.path.relpath(abs_path, root)
        _, ext = os.path.splitext(rel)
        if ext not in SUPPORTED_EXTS:
            continue
        code = read_text(abs_path, max_bytes=200_000)
        loc = code.count("\n") + 1
        lang = lang_of_ext(ext)
        file_infos.append({"path": rel, "language": lang, "loc": loc})

        if is_python(rel):
            edges += py_import_edges(rel, code)
        elif is_ts(rel):
            edges += ts_import_edges(rel, code)

    # graph & ranking
    metrics, json_graph = build_graph(root, file_infos, edges)
    top_files = metrics.get("top_files", [])[:TOP_FILES]

    # collect short excerpts for top files
    excerpts = []
    for rel in top_files:
        abs_path = os.path.join(root, rel)
        text = read_text(abs_path, max_bytes=4000)
        # tiny chunk: first ~1200 chars
        snippet = text[:1200]
        excerpts.append((rel, snippet))

    # language stats
    lang_counter = Counter([fi["language"] for fi in file_infos])
    total = sum(lang_counter.values()) or 1
    language_stats = {k: round(v*100/total, 1) for k, v in lang_counter.items()}

    # overview via LLM (one call)
    top_lines = "\n".join([f"- {p}" for p in top_files[:30]])
    ex_str = "\n\n".join([f"<file name=\"{p}\">\n{t}\n</file>" for p, t in excerpts[:12]])
    user_prompt = OVERVIEW_USER_TMPL.format(language_stats=language_stats, top_files=top_lines) + "\n\n" + ex_str
    architecture_md = generate_markdown(OVERVIEW_SYSTEM, user_prompt)

    # diagrams
    mermaid_modules = modules_mermaid(json_graph["edges"])
    mermaid_folders = folders_mermaid([fi["path"] for fi in file_infos])

    # trim metrics for response
    central = []
    for p in top_files[:50]:
        central.append({
            "path": p,
            "fan_in": metrics["fan_in"].get(p, 0),
            "fan_out": metrics["fan_out"].get(p, 0),
            "degree_centrality": round(metrics["degree_centrality"].get(p, 0.0), 4),
        })

    summary = {
        "status": "complete",
        "repo": {"url": repo_url, "commit_sha": sha},
        "language_stats": language_stats,
        "loc_total": sum(fi["loc"] for fi in file_infos),
        "file_count": len(file_infos),
        "metrics": {
            "central_files": central,
            "graph": json_graph,
        },
        "components": [],  # kept empty in MVP (optional future)
        "artifacts": {
            "architecture_md": architecture_md,
            "mermaid_modules": mermaid_modules,
            "mermaid_folders": mermaid_folders,
        },
        "token_budget": {"embed_calls": 0, "gen_calls": 1, "chunks": 0},
    }
    return summary


def lang_of_ext(ext: str) -> str:
    return {
        ".py": "python",
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
    }.get(ext, "other") 