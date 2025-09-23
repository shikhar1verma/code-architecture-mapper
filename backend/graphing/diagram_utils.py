"""
Diagram classification and grouping utilities

This module contains utilities for classifying nodes, inferring groups,
and organizing components for diagram generation.
"""

from typing import Dict, List, Optional
from collections import defaultdict


class NodeClassifier:
    """Utilities for classifying nodes and inferring logical groups"""
    
    @staticmethod
    def infer_group(node_name: str) -> str:
        """Infer logical group from node name"""
        name_lower = node_name.lower()
        
        if any(x in name_lower for x in ['frontend', 'client', 'ui', 'web', 'react', 'vue', 'angular']):
            return "Frontend"
        elif any(x in name_lower for x in ['backend', 'server', 'api', 'service']):
            return "Backend"
        elif any(x in name_lower for x in ['config', 'settings', 'env']):
            return "Configuration"
        elif any(x in name_lower for x in ['test', 'spec', '__tests__']):
            return "Tests"
        elif any(x in name_lower for x in ['util', 'helper', 'lib', 'common']):
            return "Utilities"
        elif any(x in name_lower for x in ['db', 'database', 'model', 'schema']):
            return "Data"
        else:
            return "Core"

    @staticmethod
    def infer_class(node_name: str) -> str:
        """Infer node class from name"""
        name_lower = node_name.lower()
        
        if any(x in name_lower for x in ['test', 'spec']):
            return "test"
        elif any(x in name_lower for x in ['config', 'settings', '.env', 'package.json', 'tsconfig']):
            return "config"
        elif any(x in name_lower for x in ['util', 'helper', 'lib']):
            return "utility"
        elif any(x in name_lower for x in ['service', 'api']):
            return "service"
        elif any(x in name_lower for x in ['component', 'widget']):
            return "component"
        elif any(x in name_lower for x in ['db', 'database', 'model']):
            return "db"
        else:
            return "module"

    @staticmethod
    def infer_folder_group(path: str) -> str:
        """Infer group for folder structure"""
        path_lower = path.lower()
        
        if path_lower.startswith('frontend') or any(x in path_lower for x in ['src/components', 'src/pages', 'public']):
            return "Frontend"
        elif path_lower.startswith('backend') or any(x in path_lower for x in ['api', 'server', 'services']):
            return "Backend"
        elif any(x in path_lower for x in ['test', 'spec', '__tests__']):
            return "Tests"
        elif any(x in path_lower for x in ['config', 'settings', 'env']):
            return "Configuration"
        elif any(x in path_lower for x in ['docs', 'documentation']):
            return "Documentation"
        else:
            return "Project Root"

    @staticmethod
    def infer_file_class(file_path: str) -> str:
        """Infer class for individual files"""
        file_lower = file_path.lower()
        
        if file_lower.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts', '_test.py')):
            return "test"
        elif file_lower.endswith(('.config.js', '.config.ts', 'package.json', 'tsconfig.json', '.env')):
            return "config"
        elif any(x in file_lower for x in ['component', 'widget']) and file_lower.endswith(('.tsx', '.jsx')):
            return "component"
        elif file_lower.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
            return "module"
        else:
            return "utility"

    @staticmethod
    def infer_group_class(group_name: str) -> str:
        """Infer CSS class for module group"""
        name_lower = group_name.lower()
        
        if any(x in name_lower for x in ['component', 'ui', 'frontend']):
            return "component"
        elif any(x in name_lower for x in ['service', 'api', 'backend']):
            return "service"
        elif any(x in name_lower for x in ['test', 'spec']):
            return "test"
        elif any(x in name_lower for x in ['config', 'settings']):
            return "config"
        else:
            return "module"


class ModuleGrouper:
    """Utilities for grouping modules into logical components"""
    
    @staticmethod
    def group_internal_modules(modules: List[str]) -> Dict[str, List[str]]:
        """Group internal modules by logical components"""
        groups = defaultdict(list)
        
        for module in modules:
            # Determine group based on path
            parts = module.split('/')
            
            if len(parts) >= 2:
                # Use directory structure
                if parts[0] in ['src', 'app', 'lib']:
                    group_name = parts[1] if len(parts) > 1 else parts[0]
                else:
                    group_name = parts[0]
            else:
                group_name = "Root"
            
            # Clean group name
            group_name = group_name.replace('_', ' ').replace('-', ' ').title()
            groups[group_name].append(module)
        
        return dict(groups)

    @staticmethod
    def find_module_group(module: str, module_groups: Dict[str, List[str]]) -> Optional[str]:
        """Find which group a module belongs to"""
        for group_name, modules in module_groups.items():
            if module in modules:
                return group_name
        return "Unknown"


class FolderOrganizer:
    """Utilities for organizing folder structures"""
    
    @staticmethod
    def build_folder_hierarchy(file_paths: List[str], max_depth: int = 3) -> tuple:
        """
        Build folder hierarchy from file paths
        
        Returns:
            Tuple of (folders_set, files_set)
        """
        folders = set()
        files = set()
        
        for path in file_paths:
            parts = [part for part in path.split("/") if part]
            # Add all folder levels up to max_depth
            for i in range(1, min(len(parts), max_depth) + 1):
                folder_path = "/".join(parts[:i])
                if i < len(parts):  # It's a folder
                    folders.add(folder_path)
                else:  # It's a file
                    files.add(folder_path)
        
        return folders, files

    @staticmethod
    def create_hierarchy_edges(all_paths: set) -> List[tuple]:
        """Create parent-child edges for folder hierarchy"""
        edges = []
        for path in all_paths:
            parts = path.split("/")
            if len(parts) > 1:
                parent = "/".join(parts[:-1])
                if parent in all_paths:
                    edges.append((parent, path, None))
        return edges 