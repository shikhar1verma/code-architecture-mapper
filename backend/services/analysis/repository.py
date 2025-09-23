"""
Repository Analysis Service

This service handles repository operations including:
- Git cloning and checkout
- File system scanning  
- Basic file information collection
- Language detection

Extracted from pipeline.py to improve separation of concerns.
"""

import os
from typing import Dict, Any, List, Tuple
from collections import Counter

from backend.config import TOP_FILES
from backend.utils.git_tools import shallow_clone, walk_repo
from backend.utils.text import read_text

# Supported file extensions for analysis
SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


class RepositoryService:
    """Service for repository operations and file scanning"""
    
    def __init__(self):
        self.supported_extensions = SUPPORTED_EXTS
    
    def clone_and_scan_repository(self, repo_url: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Clone repository and scan for supported files
        
        Args:
            repo_url: URL of the repository to clone
            
        Returns:
            Tuple of (repo_root_path, commit_sha, file_infos)
        """
        # Clone repository
        root, sha = shallow_clone(repo_url)
        
        # Scan files
        file_infos = self.scan_repository_files(root)
        
        return root, sha, file_infos
    
    def scan_repository_files(self, repo_root: str) -> List[Dict[str, Any]]:
        """
        Scan repository for supported files and collect basic information
        
        Args:
            repo_root: Path to the repository root
            
        Returns:
            List of file information dictionaries
            [{
                "path": rel_path,
                "language": language,
                "loc": loc,
                "content": code
            }, ...]
        """
        file_infos = []
        
        for abs_path in walk_repo(repo_root):
            rel_path = os.path.relpath(abs_path, repo_root)
            _, ext = os.path.splitext(rel_path)
            
            # Skip unsupported file types
            if ext not in self.supported_extensions:
                continue
            
            # Read file content and get basic metrics
            code = read_text(abs_path, max_bytes=200_000)
            loc = code.count("\n") + 1
            language = self.detect_language(ext)
            
            file_infos.append({
                "path": rel_path,
                "language": language,
                "loc": loc,
                "content": code
            })
        
        return file_infos
    
    def detect_language(self, extension: str) -> str:
        """
        Detect programming language from file extension
        
        Args:
            extension: File extension (e.g., '.py', '.js')
            
        Returns:
            Language name string
        """
        language_map = {
            ".py": "python",
            ".ts": "ts", 
            ".tsx": "tsx",
            ".js": "js",
            ".jsx": "jsx",
        }
        return language_map.get(extension, "other")
    
    def calculate_language_stats(self, file_infos: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate language distribution statistics
        
        Args:
            file_infos: List of file information dictionaries
            
        Returns:
            Dictionary mapping language names to percentage values
        """
        lang_counter = Counter([fi["language"] for fi in file_infos])
        total = sum(lang_counter.values()) or 1
        return {k: round(v * 100 / total, 1) for k, v in lang_counter.items()}
    
    def get_repository_metrics(self, file_infos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate basic repository metrics
        
        Args:
            file_infos: List of file information dictionaries
            
        Returns:
            Dictionary containing basic repository metrics
        """
        return {
            "file_count": len(file_infos),
            "loc_total": sum(fi["loc"] for fi in file_infos),
            "language_stats": self.calculate_language_stats(file_infos),
            "supported_extensions": list(self.supported_extensions)
        }
    
    def extract_file_excerpts(self, file_infos: List[Dict[str, Any]], top_files: List[str], 
                             max_chars: int = 1200) -> List[Tuple[str, str]]:
        """
        Extract code excerpts from top files for LLM analysis
        
        Args:
            file_infos: List of file information dictionaries
            top_files: List of top file paths to extract excerpts from
            max_chars: Maximum characters to extract per file
            
        Returns:
            List of tuples (file_path, excerpt)
        """
        # Create a lookup for file content
        content_lookup = {fi["path"]: fi["content"] for fi in file_infos}
        
        excerpts = []
        for file_path in top_files:
            if file_path in content_lookup:
                content = content_lookup[file_path]
                excerpt = content[:max_chars]
                excerpts.append((file_path, excerpt))
        
        return excerpts 