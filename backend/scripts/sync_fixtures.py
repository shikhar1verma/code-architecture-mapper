#!/usr/bin/env python3
"""
Fixture sync script for Code Architecture Mapper
Loads example data from JSON fixtures into the database
"""

import sys
import logging
import os
from pathlib import Path

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent.parent.parent  # Go up to /app
sys.path.insert(0, str(app_dir))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to sync fixtures"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting fixture sync process...")
    
    try:
        # Import after path setup
        from backend.services.fixtures import load_fixtures
        
        # Run fixture sync
        result = load_fixtures()
        
        # Log results
        total = result.get('total_files', 0)
        successful = result.get('successful_loads', 0)
        failed = result.get('failed_loads', 0)
        
        logger.info(f"Fixture sync completed:")
        logger.info(f"  Total files: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        
        if failed > 0:
            logger.warning(f"Some fixtures failed to load. Details: {result.get('details', {})}")
            sys.exit(1)
        else:
            logger.info("All fixtures loaded successfully!")
            sys.exit(0)
            
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure the backend modules are properly installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during fixture sync: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 