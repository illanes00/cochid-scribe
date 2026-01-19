"""Main FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import (
    assets,
    bibliography,
    charts,
    claims,
    comments,
    datasets,
    documents,
    exports,
    google,
    graph,
    integrations,
    llm,
    notes,
)
from app.config import get_settings
from app.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title=settings.app_name,
    description="Academic Writing Platform API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["claims"])
app.include_router(bibliography.router, prefix="/api/v1/bibliography", tags=["bibliography"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(charts.router, prefix="/api/v1/charts", tags=["charts"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["exports"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(google.router, prefix="/api/v1/google", tags=["google"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

# Static uploads
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint for infrastructure monitoring."""
    import socket

    return {"status": "healthy", "service": settings.app_name, "host": socket.gethostname()}


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Scribe API", "docs": "/api/docs"}
