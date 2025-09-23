"""
Enhanced Architecture Mapper
Streamlined architecture mapper for Python and JS/TS with Grimp and tree-sitter by default.

This service provides:
- Directed import graph across Python, JS, and TS files
- Resolution of edges to real in-repo files
- Fan in, fan out, and degree centralities per file
- High accuracy Python analysis using Grimp
- JS/TS resolution with tree-sitter and tsconfig paths
- Separation of external vendor packages from internal architecture
"""

from __future__ import annotations
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import grimp
try:
    from tree_sitter_languages import get_parser, get_language
    # Test tree-sitter functionality on import
    try:
        test_parser = get_parser('javascript')
        test_language = get_language('javascript')
        # Test a simple query to ensure compatibility
        test_tree = test_parser.parse(b'import test from "test";')
        test_query = test_language.query('(import_statement)')
        test_captures = test_query.captures(test_tree.root_node)
        TREE_SITTER_AVAILABLE = True
    except Exception as test_error:
        TREE_SITTER_AVAILABLE = False
        print(f"⚠️ tree-sitter compatibility test failed: {test_error}")
        print("⚠️ Falling back to regex parsing for JS/TS")
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️ tree-sitter-languages not available, falling back to regex parsing for JS/TS")

SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


class EnhancedArchMapper:
    """Enhanced architecture mapper with Grimp and tree-sitter by default"""
    
    def __init__(self, repo_root: str):
        self.repo_root = repo_root
    
    # ---------------- repo scan ----------------
    
    def scan_repo(self) -> List[Dict[str, Any]]:
        """Scan repository for supported files"""
        files: List[Dict[str, Any]] = []
        
        for root, _, names in os.walk(self.repo_root):
            for name in names:
                ext = os.path.splitext(name)[1].lower()
                if ext not in SUPPORTED_EXTS:
                    continue
                    
                abs_path = os.path.join(root, name)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        code = f.read()
                except Exception:
                    continue
                    
                rel_path = os.path.relpath(abs_path, self.repo_root).replace("\\", "/")
                files.append({
                    "path": rel_path,
                    "ext": ext,
                    "language": self._infer_lang(ext),
                    "loc": code.count("\n") + 1,
                    "content": code,
                })
        
        return files
    
    def _infer_lang(self, ext: str) -> str:
        """Infer language from file extension"""
        return {
            ".py": "python",
            ".js": "javascript", 
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
        }.get(ext, "other")
    
    # ---------------- tsconfig support ----------------
    
    def load_tsconfig(self) -> Dict[str, Any]:
        """Load tsconfig.json for path resolution"""
        path = Path(self.repo_root) / "tsconfig.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    
    def resolve_ts_import(self, spec: str, src_file: str, tsconf: Dict[str, Any]) -> Optional[str]:
        """Resolve TS import to repo relative path if internal"""
        if spec.startswith(".") or spec.startswith("/"):
            return self._normalize_rel(spec, src_file)
        
        co = (tsconf.get("compilerOptions") or {}) if tsconf else {}
        base_url = co.get("baseUrl", "")
        base_dir = (Path(self.repo_root) / base_url).resolve() if base_url else Path(self.repo_root)
        paths = co.get("paths") or {}
        
        # exact alias
        if spec in paths:
            repls = paths[spec] if isinstance(paths[spec], list) else [paths[spec]]
            for repl in repls:
                candidate = (base_dir / repl).resolve()
                hit = self._pick_existing_js_ts(candidate)
                if hit:
                    return os.path.relpath(hit, self.repo_root).replace("\\", "/")
        
        # wildcard alias: one star only
        for pat, repls in paths.items():
            if "*" not in pat:
                continue
            prefix, suffix = pat.split("*", 1)
            if spec.startswith(prefix) and spec.endswith(suffix):
                mid = spec[len(prefix):len(spec)-len(suffix)] or ""
                repl_list = repls if isinstance(repls, list) else [repls]
                for repl in repl_list:
                    candidate = (base_dir / repl.replace("*", mid)).resolve()
                    hit = self._pick_existing_js_ts(candidate)
                    if hit:
                        return os.path.relpath(hit, self.repo_root).replace("\\", "/")
        
        # bare spec likely external
        return None
    
    def _pick_existing_js_ts(self, base: Path) -> Optional[str]:
        """Find existing JS/TS file with common extensions and index patterns"""
        exts = [".ts", ".tsx", ".js", ".jsx"]
        cands: List[Path] = []
        
        if base.suffix:
            cands.append(base)
        else:
            cands += [base.with_suffix(e) for e in exts]
            cands += [(base / "index").with_suffix(e) for e in exts]
            
        for c in cands:
            if c.exists():
                return str(c)
        return None
    
    def _normalize_rel(self, spec: str, src_file: str) -> Optional[str]:
        """Normalize relative import to repo-relative path"""
        src_dir = Path(self.repo_root) / os.path.dirname(src_file)
        abs_path = (src_dir / spec).resolve()
        hit = self._pick_existing_js_ts(abs_path)
        if hit:
            return os.path.relpath(hit, self.repo_root).replace("\\", "/")
        return None
    
    # ---------------- python resolution with grimp ----------------
    
    def detect_python_packages(self) -> List[str]:
        """Detect Python packages in repository"""
        pkgs = []
        for p in Path(self.repo_root).iterdir():
            if p.is_dir() and (p / "__init__.py").exists():
                pkgs.append(p.name)
        return pkgs
    
    def _module_name_from_path(self, rel_path: str) -> str:
        """Convert file path to Python module name"""
        p = Path(rel_path)
        parts = list(p.with_suffix("").parts)
        return ".".join(parts)
    
    def resolve_python_import_ast(self, src_rel: str, imported_mod: str, level: int) -> Optional[str]:
        """Map Python import to repo file path if internal (for AST fallback)"""
        src_mod = self._module_name_from_path(src_rel)
        
        if level and src_mod:
            base_parts = src_mod.split(".")
            base = ".".join(base_parts[:-level]) if level <= len(base_parts) else ""
            fq = f"{base}.{imported_mod}" if imported_mod else base
        else:
            fq = imported_mod
            
        fq = fq.strip(".")
        if not fq:
            return None
            
        cand = Path(self.repo_root) / Path(*fq.split("."))
        for c in [cand.with_suffix(".py"), cand / "__init__.py"]:
            if c.exists():
                return os.path.relpath(str(c), self.repo_root).replace("\\", "/")
        return None
    
    def py_imports_ast(self, file_path: str, code: str) -> List[Dict[str, Any]]:
        """Extract Python imports using AST parsing (fallback for loose Python files)"""
        import ast
        
        out: List[Dict[str, Any]] = []
        try:
            tree = ast.parse(code)
        except Exception:
            return out
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    dst_rel = self.resolve_python_import_ast(file_path, mod, level=0)
                    out.append(self._edge(file_path, dst_rel or mod, bool(dst_rel), "py-import"))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                dst_rel = self.resolve_python_import_ast(file_path, mod, level=node.level or 0)
                out.append(self._edge(file_path, dst_rel or mod or ".", bool(dst_rel), "py-from"))
        
        return out

    def py_edges_grimp(self) -> List[Dict[str, Any]]:
        """Build edges using Grimp for enhanced Python analysis"""
        try:
            sys.path.insert(0, self.repo_root)
            packages = self.detect_python_packages()
            if not packages:
                return []
                
            edges: List[Dict[str, Any]] = []
            import importlib.util
            
            for pkg in packages:
                try:
                    graph = grimp.build_graph(pkg, include_external_packages=True)
                except Exception:
                    # Skip packages that can't be analyzed (missing dependencies, syntax errors, etc.)
                    continue
                
                # Map module names to repo files
                mod_to_file: Dict[str, str] = {}
                for mod in graph.modules:
                    try:
                        spec = importlib.util.find_spec(mod)
                        origin = getattr(spec, "origin", None) if spec else None
                        if origin and origin.endswith((".py", ".pyc")):
                            # prefer .py if .pyc
                            path = origin[:-1] if origin.endswith(".pyc") and Path(origin[:-1]).exists() else origin
                            if path.startswith(str(Path(self.repo_root).resolve())):
                                rel = os.path.relpath(path, self.repo_root).replace("\\", "/")
                                mod_to_file[mod] = rel
                    except Exception:
                        # Skip modules that can't be resolved
                        continue
                
                # Build edges
                try:
                    for importer in graph.modules:
                        for imported in graph.find_modules_directly_imported_by(importer):
                            src = mod_to_file.get(importer)
                            dst = mod_to_file.get(imported)
                            if src and dst:
                                edges.append(self._edge(src, dst, True, "grimp"))
                            elif src and not dst:
                                edges.append(self._edge(src, imported, False, "grimp-ext"))
                except Exception:
                    # Skip if graph traversal fails
                    continue
            
            # Remove duplicates
            uniq = {(e["src"], e["dst"], e["internal"], e["via"]) for e in edges}
            return [{"src": s, "dst": d, "internal": i, "via": v} for (s, d, i, v) in uniq]
        
        except Exception as e:
            # If Grimp analysis fails completely, return empty list
            print(f"⚠️ Grimp analysis failed: {e}")
            return []

    def py_edges_ast_all_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Python imports using AST parsing for all Python files"""
        edges: List[Dict[str, Any]] = []
        
        for file_info in files:
            if file_info["language"] == "python":
                try:
                    ast_edges = self.py_imports_ast(file_info["path"], file_info["content"])
                    edges.extend(ast_edges)
                except Exception as e:
                    print(f"⚠️ AST parsing failed for {file_info['path']}: {e}")
                    continue
        
        # Remove duplicates
        uniq = {(e["src"], e["dst"], e["internal"], e["via"]) for e in edges}
        return [{"src": s, "dst": d, "internal": i, "via": v} for (s, d, i, v) in uniq]

    def py_edges_hybrid(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hybrid Python analysis: combines Grimp and AST with preference to Grimp
        
        Args:
            files: List of file information dictionaries
            
        Returns:
            List of edges from both Grimp and AST analysis
        """
        print("🔍 Running hybrid Python analysis (Grimp + AST)...")
        
        # Run both analyses
        grimp_edges = self.py_edges_grimp()
        ast_edges = self.py_edges_ast_all_files(files)
        
        print(f"   Grimp edges: {len(grimp_edges)}")
        print(f"   AST edges: {len(ast_edges)}")
        
        # Merge edges with preference to Grimp
        # Key is (src, dst) for deduplication
        edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        
        # First add AST edges
        for edge in ast_edges:
            key = (edge["src"], edge["dst"])
            edge_map[key] = edge.copy()
            edge_map[key]["via"] = "ast"
        
        # Then add Grimp edges, overriding AST edges
        for edge in grimp_edges:
            key = (edge["src"], edge["dst"])
            if key in edge_map:
                # Grimp takes preference - update metadata
                edge_map[key]["via"] = "grimp-preferred"
                edge_map[key]["internal"] = edge["internal"]
            else:
                # New edge from Grimp
                edge_map[key] = edge.copy()
        
        # Convert back to list
        merged_edges = list(edge_map.values())
        
        print(f"   Merged edges: {len(merged_edges)}")
        print(f"   AST-only: {len([e for e in merged_edges if e['via'] == 'ast'])}")
        print(f"   Grimp-only: {len([e for e in merged_edges if e['via'] == 'grimp'])}")
        print(f"   Grimp-preferred: {len([e for e in merged_edges if e['via'] == 'grimp-preferred'])}")
        
        return merged_edges
    
    # ---------------- js/ts imports with tree-sitter ----------------
    
    def js_ts_imports_treesitter(self, file_path: str, code: str, tsconf: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract JS/TS imports using tree-sitter"""
        if not TREE_SITTER_AVAILABLE:
            return []
            
        try:
            lang = "typescript" if file_path.endswith((".ts", ".tsx")) else "javascript"
            
            # Initialize parser and language with error handling
            parser = get_parser(lang)
            language = get_language(lang)
            
            # Parse the code
            tree = parser.parse(code.encode("utf-8"))
            root = tree.root_node
            
            # Create query with improved error handling
            query_str = """
              (import_statement source: (string) @spec)
              (import_statement (string) @spec)
              (export_statement source: (string) @spec)
              (call_expression
                 function: (identifier) @fn
                 arguments: (arguments (string) @spec))
              (call_expression
                 function: (import)
                 arguments: (arguments (string) @spec))
            """
            
            query = language.query(query_str)
            
            out: List[Dict[str, Any]] = []
            
            # Get captures with better error handling
            try:
                captures = query.captures(root)
            except Exception as capture_error:
                print(f"⚠️ Query capture failed for {file_path}: {capture_error}")
                return []
            
            # Process captures
            for node, cap in captures:
                try:
                    if cap == "fn":
                        node_text = node.text.decode("utf-8")
                        if node_text != "require":
                            continue
                        continue
                    elif cap == "spec":
                        lit = node.text.decode("utf-8")
                        if len(lit) >= 2 and lit[0] in "\"'" and lit[-1] == lit[0]:
                            spec = lit[1:-1]
                            dst_rel = self.resolve_ts_import(spec, file_path, tsconf)
                            out.append(self._edge(file_path, dst_rel or spec, bool(dst_rel), "tree-sitter"))
                except Exception as node_error:
                    print(f"⚠️ Node processing failed for {file_path}: {node_error}")
                    continue
                    
            return out
        
        except Exception as e:
            # If tree-sitter parsing fails, return empty list
            print(f"⚠️ Tree-sitter parsing failed for {file_path}: {e}")
            return []

    def js_ts_imports_ast(self, file_path: str, code: str, tsconf: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract JS/TS imports using AST parsing (fallback method)"""
        import re
        
        out: List[Dict[str, Any]] = []
        
        try:
            # Basic regex patterns for imports and requires
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',  # import ... from "module"
                r'import\s+[\'"]([^\'"]+)[\'"]',                # import "module"
                r'export\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',   # export ... from "module"
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',    # require("module")
                r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',     # import("module") - dynamic imports
            ]
            
            for pattern in import_patterns:
                matches = re.finditer(pattern, code)
                for match in matches:
                    spec = match.group(1)
                    if spec:
                        dst_rel = self.resolve_ts_import(spec, file_path, tsconf)
                        out.append(self._edge(file_path, dst_rel or spec, bool(dst_rel), "ast-regex"))
            
            return out
            
        except Exception as e:
            print(f"⚠️ AST regex parsing failed for {file_path}: {e}")
            return []

    def js_ts_imports_hybrid(self, file_path: str, code: str, tsconf: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Hybrid JS/TS analysis: combines tree-sitter and AST with preference to tree-sitter
        
        Args:
            file_path: Path to the file being analyzed
            code: File content
            tsconf: TypeScript configuration
            
        Returns:
            List of edges from both tree-sitter and AST analysis
        """
        # Run both analyses with error handling
        treesitter_edges = []
        ast_edges = []
        
        # Try tree-sitter first
        try:
            treesitter_edges = self.js_ts_imports_treesitter(file_path, code, tsconf)
        except Exception as e:
            print(f"⚠️ Tree-sitter analysis failed for {file_path}, using AST fallback: {e}")
        
        # Always run AST as backup
        try:
            ast_edges = self.js_ts_imports_ast(file_path, code, tsconf)
        except Exception as e:
            print(f"⚠️ AST analysis also failed for {file_path}: {e}")
        
        # If tree-sitter failed completely, rely on AST
        if not treesitter_edges and ast_edges:
            print(f"ℹ️ Using AST-only analysis for {file_path}")
            return ast_edges
        
        # Merge edges with preference to tree-sitter
        # Key is (src, dst) for deduplication
        edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        
        # First add AST edges
        for edge in ast_edges:
            key = (edge["src"], edge["dst"])
            edge_map[key] = edge.copy()
            edge_map[key]["via"] = "ast-regex"
        
        # Then add tree-sitter edges, overriding AST edges
        for edge in treesitter_edges:
            key = (edge["src"], edge["dst"])
            if key in edge_map:
                # Tree-sitter takes preference - update metadata
                edge_map[key]["via"] = "tree-sitter-preferred"
                edge_map[key]["internal"] = edge["internal"]
            else:
                # New edge from tree-sitter
                edge_map[key] = edge.copy()
        
        # Convert back to list
        merged_edges = list(edge_map.values())
        
        return merged_edges
    
    # ---------------- orchestration ----------------
    
    def extract_imports(self, file_info: Dict[str, Any], tsconf: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract imports from a file based on its language using hybrid approach"""
        path = file_info["path"]
        lang = file_info["language"] 
        code = file_info["content"]
        
        if lang == "python":
            # Python files will be handled by hybrid analysis at the repository level
            return []
        elif lang in {"javascript", "jsx", "typescript", "tsx"}:
            return self.js_ts_imports_hybrid(path, code, tsconf)
        
        return []
    
    def _edge(self, src: str, dst: str, internal: bool, via: str) -> Dict[str, Any]:
        """Create an edge dictionary"""
        return {"src": src, "dst": dst, "internal": internal, "via": via}
    
    def _categorize_external_dependency(self, dependency: str) -> str:
        """
        Categorize external dependencies for better organization
        
        Args:
            dependency: External dependency name
            
        Returns:
            Category string for the dependency
        """
        # Common framework and library patterns
        if any(framework in dependency.lower() for framework in ['react', 'vue', 'angular', 'svelte']):
            return "Frontend Frameworks"
        elif any(web in dependency.lower() for web in ['express', 'fastapi', 'flask', 'django', 'koa']):
            return "Web Frameworks"
        elif any(db in dependency.lower() for db in ['postgres', 'mysql', 'mongodb', 'redis', 'sqlite']):
            return "Databases"
        elif any(test in dependency.lower() for test in ['jest', 'pytest', 'mocha', 'chai', 'cypress']):
            return "Testing"
        elif any(build in dependency.lower() for build in ['webpack', 'vite', 'rollup', 'babel', 'typescript']):
            return "Build Tools"
        elif any(ui in dependency.lower() for ui in ['tailwind', 'bootstrap', 'material', 'antd', 'chakra']):
            return "UI Libraries"
        elif any(util in dependency.lower() for util in ['lodash', 'axios', 'moment', 'uuid', 'crypto']):
            return "Utilities"
        elif dependency.startswith('@types/'):
            return "Type Definitions"
        elif dependency.startswith('@'):
            return "Scoped Packages"
        elif '.' in dependency and len(dependency.split('.')) > 2:
            return "Standard Library"
        else:
            return "External Libraries"
    
    def build_graph(self, file_infos: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Build NetworkX graph and calculate metrics"""
        G = nx.DiGraph()
        internal_files = {fi["path"] for fi in file_infos}
        lang_by_file = {fi["path"]: fi["language"] for fi in file_infos}
        loc_by_file = {fi["path"]: fi["loc"] for fi in file_infos}
        
        # Add nodes for all internal files
        for f in internal_files:
            G.add_node(f, language=lang_by_file[f], loc=loc_by_file[f])
        
        # Add edges for internal dependencies only
        for e in edges:
            if e["internal"] and e["dst"] in internal_files:
                G.add_edge(e["src"], e["dst"], via=e["via"])
        
        # Calculate metrics
        fan_out = {n: G.out_degree(n) for n in G.nodes}
        fan_in = {n: G.in_degree(n) for n in G.nodes}
        
        # Calculate centrality metrics
        in_cent = nx.in_degree_centrality(G) if len(G) > 0 else {}
        out_cent = nx.out_degree_centrality(G) if len(G) > 0 else {}
        degree_cent = nx.degree_centrality(G) if len(G) > 0 else {}
        
        # Find top files by combined degree
        top = sorted(G.nodes, key=lambda n: (fan_in[n] + fan_out[n]), reverse=True)[:100]
        
        # Create JSON graph representation
        json_graph = {
            "nodes": [
                {
                    "id": n, 
                    "fan_in": fan_in[n], 
                    "fan_out": fan_out[n], 
                    "language": G.nodes[n]["language"],
                    "loc": G.nodes[n]["loc"]
                } for n in G.nodes
            ],
            "edges": [
                {
                    "source": u, 
                    "target": v, 
                    "via": G.edges[u, v]["via"]
                } for u, v in G.edges
            ],
        }
        
        metrics = {
            "fan_in": fan_in,
            "fan_out": fan_out,
            "in_degree_centrality": in_cent,
            "out_degree_centrality": out_cent,
            "degree_centrality": degree_cent,
            "top_files": top,
        }
        
        return G, {"graph_metrics": metrics, "json_graph": json_graph}
    
    def lang_stats(self, files: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate language distribution statistics"""
        from collections import Counter
        c = Counter(fi["language"] for fi in files)
        tot = sum(c.values()) or 1
        return {k: round(v * 100 / tot, 1) for k, v in c.items()}
    
    def analyze_repository(self) -> Dict[str, Any]:
        """Main analysis function - returns comprehensive architecture data using hybrid approach"""
        files = self.scan_repo()
        tsconf = self.load_tsconfig()
        
        edges: List[Dict[str, Any]] = []
        
        # Python analysis using hybrid approach (Grimp + AST)
        py_edges = self.py_edges_hybrid(files)
        edges.extend(py_edges)
        
        # Per file extraction for JS/TS using hybrid approach (tree-sitter + AST)
        print("🔍 Running hybrid JS/TS analysis (tree-sitter + AST)...")
        js_ts_edges = []
        for fi in files:
            if fi["language"] in {"javascript", "jsx", "typescript", "tsx"}:
                file_edges = self.extract_imports(fi, tsconf)
                js_ts_edges.extend(file_edges)
        
        edges.extend(js_ts_edges)
        print(f"   JS/TS edges: {len(js_ts_edges)}")
        
        # Build graph and calculate metrics
        _, packed = self.build_graph(files, edges)
        
        # Repository metrics
        repo_metrics = {
            "file_count": len(files),
            "loc_total": sum(fi["loc"] for fi in files),
            "language_stats": self.lang_stats(files),
        }
        
        # Dependency analysis with edge type breakdown
        internal_edges = [e for e in edges if e["internal"]]
        external_edges = [e for e in edges if not e["internal"]]
        
        # Edge type statistics
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("via", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        # Group external dependencies by category for frontend compatibility
        external_categories = {}
        for edge in external_edges:
            category = self._categorize_external_dependency(edge["dst"])
            if category not in external_categories:
                external_categories[category] = []
            external_categories[category].append(edge)
        
        dependency_analysis = {
            "total_edges": len(edges),
            "internal_edges": internal_edges,
            "external_edges": external_edges,
            "edge_types": edge_types,
            "summary": {
                "internal_count": len(internal_edges),
                "external_count": len(external_edges),
                "categories": list(external_categories.keys()),
                "total_files": len(files),
                "edge_type_breakdown": edge_types
            },
            "external_groups": external_categories
        }
        
        print("🎯 Hybrid analysis complete:")
        print(f"   Total edges: {len(edges)}")
        print(f"   Internal: {len(internal_edges)}, External: {len(external_edges)}")
        print(f"   Edge types: {edge_types}")
        
        return {
            "repository": {"root_path": self.repo_root},
            "files": {"file_infos": files, "repository_metrics": repo_metrics},
            "dependencies": {
                "edges": edges,
                "dependency_analysis": dependency_analysis,
            },
            "metrics": {
                "graph_metrics": packed["graph_metrics"],
                "top_files": packed["graph_metrics"]["top_files"],
                "json_graph": packed["json_graph"],
            },
        }