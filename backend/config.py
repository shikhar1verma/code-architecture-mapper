import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Analysis Configuration
TOP_FILES = int(os.getenv("TOP_FILES", 40))
COMPONENT_COUNT = int(os.getenv("COMPONENT_COUNT", 8))
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", 1400))

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/repo_architect"
)
SQL_DEBUG = os.getenv("SQL_DEBUG", "false").lower() == "true"

# Git and temporary storage paths
WORK_DIR = os.getenv("WORK_DIR", "/tmp/repo-architect")
TMP_DIR = os.path.join(WORK_DIR, "tmp")

# Create temp directory for git operations
os.makedirs(TMP_DIR, exist_ok=True) 