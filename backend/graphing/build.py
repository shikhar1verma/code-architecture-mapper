import os
import networkx as nx
from typing import Dict, List, Any


def normalize_internal_edge(root: str, edge: Dict[str, str]) -> Dict[str, str]:
    src = os.path.relpath(edge["src"], root)
    dst = edge["dst"]
    # if dst is a path-like import (./x or ../x), resolve to a file stem
    if dst.startswith("./") or dst.startswith("../"):
        dst_path = os.path.normpath(os.path.join(os.path.dirname(src), dst))
        return {"src": src, "dst": dst_path}
    # else it's likely a package/module; keep as module label
    return {"src": src, "dst": dst}


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

    # lightweight json graph
    json_graph = {
        "nodes": [{"id": n, "fan_in": fan_in.get(n, 0), "fan_out": fan_out.get(n, 0)} for n in G.nodes],
        "edges": [{"source": u, "target": v} for u, v in G.edges]
    }
    return metrics, json_graph 