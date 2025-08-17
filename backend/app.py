from fastapi import FastAPI
from backend.routes import analyze, analysis
from backend.database.connection import init_db

app = FastAPI(title="Repo Architect (No-Embeddings MVP)")

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