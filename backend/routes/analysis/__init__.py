"""
Analysis Routes Module

Combines all analysis-related endpoints into a single router.
Clean separation of concerns while maintaining a unified API.
"""

from fastapi import APIRouter

from . import operations, diagrams, dependencies

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(operations.router)
router.include_router(diagrams.router)
router.include_router(dependencies.router)
