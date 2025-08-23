from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import analyze, analysis
from backend.database.connection import init_db

app = FastAPI(
    title="Repo Architect (No-Embeddings MVP)",
    debug=True  # Enable debug mode for development
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(analyze.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")

@app.get("/")
def root():
    return {"ok": True, "service": "repo-architect-mvp"}

@app.get("/health")
def health_check():
    return {"status": "healthy"} 