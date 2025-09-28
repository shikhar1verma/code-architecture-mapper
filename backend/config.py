import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model Fallback Configuration (in order of preference)
# From highest capability to most available (lower quotas but higher RPM/RPD)
GEMINI_MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash-lite", # Tier 2: Good model, better quotas (15 RPM, 250K TPM, 1000 RPD)
    "gemini-2.5-flash",      # Tier 1: Best model, lowest quotas (10 RPM, 250K TPM, 250 RPD)
    "gemini-2.0-flash",      # Tier 3: Good model, better quotas (15 RPM, 1M TPM, 200 RPD)
    "gemini-2.0-flash-lite", # Tier 4: Fastest model, highest quotas (30 RPM, 1M TPM, 200 RPD)
]

# Retry Configuration
RETRY_MIN_DELAY_SECONDS = 1
RETRY_MAX_DELAY_SECONDS = 2
MAX_RETRIES_PER_MODEL = 1  # How many times to retry each model before moving to next

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/repo_architect")

# Analysis Configuration
TOP_FILES = int(os.getenv("TOP_FILES", "50"))
COMPONENT_COUNT = int(os.getenv("COMPONENT_COUNT", "8"))

# New: LLM Feature Toggles
USE_LLM_FOR_DIAGRAMS = os.getenv("USE_LLM_FOR_DIAGRAMS", "true").lower() == "true"
USE_LLM_FOR_DEPENDENCY_ANALYSIS = os.getenv("USE_LLM_FOR_DEPENDENCY_ANALYSIS", "false").lower() == "true"


# Git and temporary storage paths
WORK_DIR = os.getenv("WORK_DIR", "/tmp/repo-architect")
TMP_DIR = os.path.join(WORK_DIR, "tmp")

# Create temp directory for git operations with proper permissions
os.makedirs(TMP_DIR, exist_ok=True, mode=0o755) 

# Environment Configuration
ENV_TYPE = os.getenv("ENV_TYPE", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Allowed hosts to backend
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Log environment info in development
if ENV_TYPE == "development":
    print("🔧 Backend Environment:", {
        "ENV_TYPE": ENV_TYPE,
        "DEBUG": DEBUG,
        "FRONTEND_URL": FRONTEND_URL,
        "DATABASE_URL": DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL,
        "ALLOWED_HOSTS": ALLOWED_HOSTS
    })
