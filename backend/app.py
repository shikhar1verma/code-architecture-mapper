from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import analysis, examples
from backend.database.connection import init_db
from backend.utils.logger import setup_logging, get_logger
from backend.config import ALLOWED_HOSTS, DEBUG

app = FastAPI(
    title="Repo Architect (No-Embeddings MVP)",
    debug=DEBUG  # Use debug mode from environment configuration
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Initialize application on startup
@app.on_event("startup")
def startup_event():
    # Setup logging first
    setup_logging("INFO")
    logger = get_logger(__name__)
    logger.info("🚀 Starting Code Architecture Mapper backend...")
    
    # Initialize database
    init_db()
    logger.info("✅ Application startup completed")

# Include consolidated routes
app.include_router(analysis.router, prefix="/api")
app.include_router(examples.router, prefix="/api")

@app.get("/")
def root():
    return {"ok": True, "service": "repo-architect-mvp"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
