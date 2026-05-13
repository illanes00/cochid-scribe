"""Main FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import (
    assets,
    auth,
    bibliography,
    charts,
    chat,
    claims,
    comments,
    datasets,
    dictation,
    documents,
    exports,
    google,
    google_sync,
    graph,
    health,
    integrations,
    llm,
    notes,
    projects,
    review,
    track_changes,
    workspaces,
)
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.db.session import init_db

settings = get_settings()

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("app.startup", environment=settings.environment)
    init_db()
    logger.info("app.ready", docs_url="/api/docs")
    yield
    # Shutdown
    logger.info("app.shutdown")


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

# Session middleware (required for OIDC and /api/v1/auth/me)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=settings.environment == "production",
    max_age=60 * 60 * 8,
)

# OIDC setup (Authentik SSO). Loads if client_id is set; logs and skips otherwise.
if settings.auth_enabled and settings.oidc_client_id:
    from fastapi import Request as _FastapiRequest

    from illanes_auth import OIDCHandler

    oidc = OIDCHandler(
        issuer=settings.oidc_issuer,
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret,
        redirect_uri=settings.oidc_redirect_uri,
    )
    oidc.setup_fastapi()

    # Wrap OIDCHandler bound methods so FastAPI sees explicit `Request` typing
    # (the bound method signature `(self, request: Any)` confuses pydantic and
    # results in 422 Unprocessable Entity instead of a 302 redirect).
    @app.get("/api/auth/login")
    async def _auth_login(request: _FastapiRequest):
        return await oidc.fastapi_login(request)

    @app.get("/api/auth/callback")
    async def _auth_callback(request: _FastapiRequest):
        return await oidc.fastapi_callback(request)

    @app.get("/api/auth/logout")
    async def _auth_logout(request: _FastapiRequest):
        return await oidc.fastapi_logout(request)

    logger.info("auth.oidc.enabled", issuer=settings.oidc_issuer)
else:
    logger.warning("auth.oidc.disabled", reason="OIDC_CLIENT_ID not set")

# Request logging (logs all HTTP requests with timing)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
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
app.include_router(google_sync.router, prefix="/api/v1/google-sync", tags=["google-sync"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(review.router, prefix="/api/v1/review", tags=["review"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(track_changes.router, prefix="/api/v1/documents", tags=["track-changes"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(dictation.router, prefix="/api/v1/dictation", tags=["dictation"])

# Static uploads
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/health")
async def health_check():
    """Simple health check for load balancers."""
    import socket

    return {
        "status": "healthy",
        "service": settings.app_name,
        "host": socket.gethostname(),
        "routes": len(app.routes),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Scribe API", "docs": "/api/docs"}
