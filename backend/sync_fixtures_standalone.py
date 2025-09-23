#!/usr/bin/env python3
"""
Standalone Fixture Sync Script for Code Architecture Mapper

This script loads example fixtures into the database independently of the main application.
It reads database configuration from environment variables or .env file.

Usage:
    python sync_fixtures_standalone.py [--check-only] [--verbose]

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
    
Example:
    DATABASE_URL="postgresql://user:pass@localhost:5432/dbname" python sync_fixtures_standalone.py
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

import psycopg2

# Try to load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set manually
    pass

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.fixtures import FixtureLoader


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def get_database_config() -> str:
    """Get database configuration from environment"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required.\n"
            "Example: DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'"
        )
    
    return database_url


def wait_for_database(database_url: str, max_attempts: int = 30, logger: logging.Logger = None) -> bool:
    """Wait for database to be ready"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("⏳ Waiting for database to be ready...")
    
    for attempt in range(max_attempts):
        try:
            conn = psycopg2.connect(database_url)
            conn.close()
            logger.info("✅ Database is ready!")
            return True
        except psycopg2.OperationalError as e:
            logger.debug(f"Database connection attempt {attempt + 1}/{max_attempts} failed: {e}")
            logger.info(f"⏳ Database not ready yet (attempt {attempt + 1}/{max_attempts}), waiting...")
            time.sleep(2)
    
    logger.error(f"❌ Database connection failed after {max_attempts} attempts")
    return False


def check_fixtures_only(fixtures_dir: str, logger: logging.Logger) -> Dict[str, Any]:
    """Check fixture files without loading to database"""
    logger.info("🔍 Checking fixture files (validation only)...")
    
    loader = FixtureLoader(fixtures_dir)
    fixtures_path = Path(fixtures_dir)
    
    if not fixtures_path.exists():
        logger.error(f"❌ Fixtures directory not found: {fixtures_dir}")
        return {"error": "Fixtures directory not found"}
    
    json_files = list(fixtures_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} fixture files")
    
    results = {}
    valid_count = 0
    
    for json_file in json_files:
        try:
            import json
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            is_valid = loader._validate_fixture_data(data)
            results[json_file.name] = is_valid
            
            if is_valid:
                valid_count += 1
                logger.info(f"✅ {json_file.name} - Valid structure")
            else:
                logger.error(f"❌ {json_file.name} - Invalid structure")
                
        except Exception as e:
            logger.error(f"❌ {json_file.name} - Error reading file: {e}")
            results[json_file.name] = False
    
    summary = {
        "total_files": len(json_files),
        "valid_files": valid_count,
        "invalid_files": len(json_files) - valid_count,
        "details": results
    }
    
    logger.info(f"📊 Validation Summary: {valid_count}/{len(json_files)} files are valid")
    return summary


def sync_fixtures(fixtures_dir: str, database_url: str, logger: logging.Logger) -> Dict[str, Any]:
    """Sync fixtures to database"""
    logger.info("📦 Starting fixture sync to database...")
    
    # Wait for database
    if not wait_for_database(database_url, logger=logger):
        return {"error": "Database connection failed"}
    
    # Load fixtures
    loader = FixtureLoader(fixtures_dir)
    result = loader.sync_fixtures()
    
    # Log results
    total = result.get('total_files', 0)
    successful = result.get('successful_loads', 0)
    failed = result.get('failed_loads', 0)
    
    logger.info("📊 Fixture Sync Results:")
    logger.info(f"  Total files: {total}")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    
    if failed > 0:
        logger.warning("⚠️  Some fixtures failed to load:")
        for filename, success in result.get('details', {}).items():
            if not success:
                logger.warning(f"    ❌ {filename}")
    
    if successful > 0:
        logger.info(f"✅ {successful} fixtures loaded successfully!")
    
    return result


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Sync Code Architecture Mapper fixtures to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Sync fixtures to database
    python sync_fixtures_standalone.py
    
    # Check fixture validity only (no database required)
    python sync_fixtures_standalone.py --check-only
    
    # Verbose output
    python sync_fixtures_standalone.py --verbose
    
    # Custom database URL
    DATABASE_URL="postgresql://user:pass@host:port/db" python sync_fixtures_standalone.py
        """
    )
    
    parser.add_argument(
        '--check-only', 
        action='store_true',
        help='Only validate fixture files without loading to database'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--fixtures-dir',
        default=None,
        help='Path to fixtures directory (default: backend/fixtures/examples)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    logger.info("🚀 Code Architecture Mapper - Fixture Sync")
    
    try:
        # Determine fixtures directory
        if args.fixtures_dir:
            fixtures_dir = args.fixtures_dir
        else:
            # Default to fixtures directory relative to this script
            script_dir = Path(__file__).parent
            fixtures_dir = script_dir / "fixtures" / "examples"
        
        logger.info(f"📁 Fixtures directory: {fixtures_dir}")
        
        if args.check_only:
            # Validation only mode
            result = check_fixtures_only(str(fixtures_dir), logger)
            
            if "error" in result:
                logger.error(f"❌ {result['error']}")
                sys.exit(1)
            
            if result['invalid_files'] > 0:
                logger.error(f"❌ {result['invalid_files']} fixture files have invalid structure")
                sys.exit(1)
            else:
                logger.info("✅ All fixture files are valid!")
                sys.exit(0)
        
        else:
            # Full sync mode
            database_url = get_database_config()
            logger.info(f"🗄️  Database: {database_url.split('@')[-1] if '@' in database_url else 'localhost'}")
            
            result = sync_fixtures(str(fixtures_dir), database_url, logger)
            
            if "error" in result:
                logger.error(f"❌ {result['error']}")
                sys.exit(1)
            
            if result.get('failed_loads', 0) > 0:
                logger.error(f"❌ {result['failed_loads']} fixtures failed to load")
                sys.exit(1)
            else:
                logger.info("✅ All fixtures loaded successfully!")
                sys.exit(0)
    
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 