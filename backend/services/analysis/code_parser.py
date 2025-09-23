"""
Code Parsing Service (Legacy Compatibility)

This service maintains compatibility with existing code that expects
the old CodeParserService interface. The actual parsing is now handled
by the EnhancedArchMapper which uses Grimp and tree-sitter by default.

This service now primarily handles dependency pattern analysis
and file complexity metrics that aren't part of the core graph analysis.
"""

from typing import Dict, Any, List


class CodeParserService:
    """Legacy service for parsing code - now simplified for compatibility"""
    
    def parse_files_for_dependencies(self, file_infos: List[Dict[str, Any]]) -> List[Dict[str, str]]:  # pylint: disable=unused-argument
        """
        Legacy method - parsing is now handled by EnhancedArchMapper
        Returns empty list as dependencies are extracted by the enhanced mapper
        """
        # This method is kept for backward compatibility but is no longer used
        # Dependencies are now extracted by EnhancedArchMapper using Grimp and tree-sitter
        return []
    
    def extract_imports_from_file(self, file_path: str, content: str) -> List[Dict[str, str]]:  # pylint: disable=unused-argument
        """
        Legacy method - kept for compatibility
        Returns empty list as imports are extracted by the enhanced mapper
        """
        # This method is kept for backward compatibility but is no longer used
        return []
    
    def analyze_dependency_patterns(self, edges: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze dependency patterns and extract insights
        
        Args:
            edges: List of dependency edges
            
        Returns:
            Dictionary containing dependency analysis insights
        """
        if not edges:
            return {
                "total_edges": 0,
                "internal_edges": [],
                "external_edges": [],
                "most_imported": [],
                "most_importing": []
            }
        
        # Separate internal vs external dependencies
        internal_edges = []
        external_edges = []
        
        for edge in edges:
            src, dst = edge["src"], edge["dst"]
            
            # Consider it internal if destination looks like a file path
            if self._is_internal_dependency(dst):
                internal_edges.append(edge)
            else:
                external_edges.append(edge)
        
        # Calculate statistics
        import_counts = {}
        export_counts = {}
        
        for edge in edges:
            src, dst = edge["src"], edge["dst"]
            
            # Count imports (what each file imports)
            if src not in export_counts:
                export_counts[src] = 0
            export_counts[src] += 1
            
            # Count what gets imported (popularity)
            if dst not in import_counts:
                import_counts[dst] = 0
            import_counts[dst] += 1
        
        # Get top imported and importing
        most_imported = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_importing = sorted(export_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_edges": len(edges),
            "internal_edges": internal_edges,
            "external_edges": external_edges,
            "internal_count": len(internal_edges),
            "external_count": len(external_edges),
            "most_imported": most_imported,
            "most_importing": most_importing,
            "unique_dependencies": len(set(edge["dst"] for edge in edges)),
            "files_with_dependencies": len(set(edge["src"] for edge in edges))
        }
    
    def _is_internal_dependency(self, dependency: str) -> bool:
        """
        Determine if a dependency is internal to the project
        
        Args:
            dependency: Dependency name/path
            
        Returns:
            True if dependency appears to be internal, False if external
        """
        # Internal dependencies typically:
        # - Start with ./ or ../  (relative imports)
        # - Contain file separators
        # - End with common file extensions
        
        if dependency.startswith("./") or dependency.startswith("../"):
            return True
        
        if "/" in dependency and not dependency.startswith("@"):
            # Looks like a path but not a scoped npm package
            return True
        
        # Common file extensions indicate internal files
        if any(dependency.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".jsx"]):
            return True
        
        return False
    
    def get_file_complexity_metrics(self, file_infos: List[Dict[str, Any]], 
                                   edges: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate complexity metrics for individual files
        
        Args:
            file_infos: List of file information dictionaries
            edges: List of dependency edges
            
        Returns:
            Dictionary mapping file paths to their complexity metrics
        """
        metrics = {}
        
        # Initialize metrics for all files
        for file_info in file_infos:
            file_path = file_info["path"]
            metrics[file_path] = {
                "loc": file_info["loc"],
                "language": file_info["language"],
                "imports": 0,  # How many things this file imports
                "imported_by": 0,  # How many files import this
                "complexity_score": 0
            }
        
        # Count imports and dependencies
        for edge in edges:
            src, dst = edge["src"], edge["dst"]
            
            if src in metrics:
                metrics[src]["imports"] += 1
            
            if dst in metrics:
                metrics[dst]["imported_by"] += 1
        
        # Calculate complexity score
        for file_path, file_metrics in metrics.items():
            # Simple complexity heuristic: LOC + import count + popularity
            complexity = (
                file_metrics["loc"] * 0.1 +  # Lines of code factor
                file_metrics["imports"] * 2 +  # Import complexity
                file_metrics["imported_by"] * 5  # Popularity/centrality factor
            )
            file_metrics["complexity_score"] = round(complexity, 2)
        
        return metrics