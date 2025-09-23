"""
Simple Logger Utility

Provides consistent, easy-to-use logging across the application.
No over-engineering - just clean, simple logging that works.
"""

import logging
import sys
from typing import Optional


class AppLogger:
    """Simple logger utility for consistent application logging"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup(cls, level: str = "INFO", format_string: Optional[str] = None) -> None:
        """
        Setup application logging configuration
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            format_string: Custom format string (optional)
        """
        if cls._configured:
            return
            
        # Simple, readable format
        if not format_string:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_string,
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        if not cls._configured:
            cls.setup()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]


# Simple convenience functions for common patterns
def get_logger(name: str) -> logging.Logger:
    """Get logger instance - most common usage"""
    return AppLogger.get_logger(name)


def setup_logging(level: str = "INFO") -> None:
    """Setup application logging - call once at startup"""
    AppLogger.setup(level)


# Module-level logger for this utility
logger = get_logger(__name__) 