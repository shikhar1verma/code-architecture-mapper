import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database.connection import SessionLocal
from backend.database.models import Example

logger = logging.getLogger(__name__)

class FixtureLoader:
    """Service to load example fixtures from JSON files into database"""
    
    def __init__(self, fixtures_dir: str = None):
        if fixtures_dir is None:
            # Default to fixtures directory relative to this file
            current_dir = Path(__file__).parent.parent
            fixtures_dir = current_dir / "fixtures" / "examples"
        
        self.fixtures_dir = Path(fixtures_dir)
        logger.info(f"Fixture loader initialized with directory: {self.fixtures_dir}")

    def load_all_fixtures(self) -> Dict[str, bool]:
        """
        Load all fixture files from the fixtures directory
        Returns: Dict with filename as key and success status as value
        """
        results = {}
        
        if not self.fixtures_dir.exists():
            logger.warning(f"Fixtures directory does not exist: {self.fixtures_dir}")
            return results
        
        # Find all JSON files in fixtures directory
        json_files = list(self.fixtures_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} fixture files")
        
        for json_file in json_files:
            try:
                results[json_file.name] = self.load_fixture_file(json_file)
            except Exception as e:
                logger.error(f"Failed to load fixture {json_file.name}: {e}")
                results[json_file.name] = False
        
        return results

    def load_fixture_file(self, file_path: Path) -> bool:
        """
        Load a single fixture file into the database
        Returns: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading fixture: {file_path.name}")
            
            # Read and parse JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate fixture structure
            if not self._validate_fixture_data(data):
                logger.error(f"Invalid fixture structure in {file_path.name}")
                return False
            
            # Load into database
            session = SessionLocal()
            try:
                success = self._load_example_to_db(session, data)
                if success:
                    session.commit()
                    logger.info(f"Successfully loaded fixture: {file_path.name}")
                else:
                    session.rollback()
                    logger.error(f"Failed to load fixture: {file_path.name}")
                
                return success
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error loading fixture {file_path.name}: {e}")
            return False

    def _validate_fixture_data(self, data: Dict[str, Any]) -> bool:
        """Validate that fixture data has required structure"""
        try:
            # Check required top-level keys
            if 'example' not in data:
                return False
            
            example_data = data['example']
            
            # Check required example fields
            required_fields = ['name', 'repo_url', 'status']
            for field in required_fields:
                if field not in example_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Files are no longer stored separately, skip file validation
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def _load_example_to_db(self, session: Session, data: Dict[str, Any]) -> bool:
        """
        Load example data into database - Uses simple storage functions
        
        Session parameter is kept for backward compatibility but we use
        the simple storage functions which manage their own sessions.
        """
        try:
            example_data = data['example']
            
            # Use the simple storage function
            from backend.storage.dao import save_example_from_fixture
            
            success = save_example_from_fixture(example_data)
            
            if success:
                logger.info(f"Successfully loaded example '{example_data.get('name', 'Unknown')}'")
            else:
                logger.error(f"Failed to load example '{example_data.get('name', 'Unknown')}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading example to database: {e}")
            return False

    def sync_fixtures(self) -> Dict[str, Any]:
        """
        Sync all fixtures to database and return summary
        """
        logger.info("Starting fixture sync...")
        
        results = self.load_all_fixtures()
        
        total_files = len(results)
        successful_loads = sum(1 for success in results.values() if success)
        failed_loads = total_files - successful_loads
        
        summary = {
            "total_files": total_files,
            "successful_loads": successful_loads,
            "failed_loads": failed_loads,
            "details": results
        }
        
        logger.info(f"Fixture sync complete: {successful_loads}/{total_files} successful")
        
        return summary

def load_fixtures() -> Dict[str, Any]:
    """
    Convenience function to load all fixtures
    Can be called from other modules or command line
    """
    loader = FixtureLoader()
    return loader.sync_fixtures()

if __name__ == "__main__":
    # Allow running this script directly for testing
    logging.basicConfig(level=logging.INFO)
    result = load_fixtures()
    print(f"Fixture loading result: {result}") 