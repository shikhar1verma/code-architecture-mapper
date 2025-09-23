"""
Graphing Module - Clean Entry Point

This module provides a clean, single entry point for all graphing functionality.
It directly exports the functions that are actually used by other modules.

No legacy layers, no over-engineering - just direct access to what's needed.
"""

# Direct imports from the focused modules
from backend.graphing.diagram_builders import (
    intelligent_modules_mermaid,
    modules_mermaid, 
    folders_mermaid
)

from backend.graphing.mermaid_core import (
    mermaid_architecture
)

from backend.graphing.diagram_utils import (
    NodeClassifier,
    ModuleGrouper,
    FolderOrganizer
)

# Export exactly what other modules need
__all__ = [
    # Functions used by services/pipeline.py and routes/analysis.py
    'intelligent_modules_mermaid',
    'modules_mermaid',
    'folders_mermaid',
    'mermaid_architecture',
    
    # Utility classes for advanced usage
    'NodeClassifier',
    'ModuleGrouper', 
    'FolderOrganizer'
] 