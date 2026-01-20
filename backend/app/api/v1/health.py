"""Health check endpoints for infrastructure monitoring.

Provides two endpoints:
- /health: Simple health check for load balancers (fast, always returns 200 if app is up)
- /health/detailed: Detailed status of all subsystems for debugging
"""

import socket
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])
settings = get_settings()


class ComponentStatus(BaseModel):
    """Status of a single component."""

    status: str  # "healthy", "degraded", "unhealthy"
    message: str | None = None
    latency_ms: float | None = None


class DetailedHealthResponse(BaseModel):
    """Detailed health response with component statuses."""

    status: str  # Overall status: "healthy", "degraded", "unhealthy"
    service: str
    environment: str
    host: str
    version: str
    timestamp: str
    components: dict[str, ComponentStatus]


def check_database(db: Session) -> ComponentStatus:
    """Check database connectivity and performance."""
    try:
        import time

        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000

        return ComponentStatus(
            status="healthy",
            message="Database connection OK",
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        return ComponentStatus(
            status="unhealthy",
            message=f"Database error: {str(e)}",
        )


def check_google_integration(db: Session) -> ComponentStatus:
    """Check if Google OAuth integration is configured and has valid tokens."""
    from app.models.integration import Integration

    # Check if Google credentials are configured
    if not settings.google_client_id or not settings.google_client_secret:
        return ComponentStatus(
            status="degraded",
            message="Google OAuth not configured (optional)",
        )

    # Check if we have stored tokens
    integration = db.query(Integration).filter(Integration.provider == "google").first()
    if not integration or not integration.access_token:
        return ComponentStatus(
            status="degraded",
            message="Google not connected (no stored tokens)",
        )

    # Check if tokens are expired
    if integration.expires_at and integration.expires_at < datetime.utcnow():
        if integration.refresh_token:
            return ComponentStatus(
                status="degraded",
                message="Google tokens expired (will refresh on next use)",
            )
        return ComponentStatus(
            status="unhealthy",
            message="Google tokens expired (no refresh token)",
        )

    return ComponentStatus(
        status="healthy",
        message="Google integration connected",
    )


def check_llm_service() -> ComponentStatus:
    """Check if Anthropic API key is configured."""
    if not settings.anthropic_api_key:
        return ComponentStatus(
            status="degraded",
            message="Anthropic API key not configured (AI features disabled)",
        )

    # We don't actually call the API here to avoid cost/latency
    # Just verify the key looks valid (starts with expected prefix)
    if settings.anthropic_api_key.startswith("sk-ant-"):
        return ComponentStatus(
            status="healthy",
            message="Anthropic API key configured",
        )

    return ComponentStatus(
        status="degraded",
        message="Anthropic API key format may be invalid",
    )


@router.get("")
async def simple_health_check() -> dict[str, Any]:
    """Simple health check for load balancers.

    Always returns 200 if the application is running.
    Used by infrastructure for basic liveness checks.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "host": socket.gethostname(),
    }


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: Session = Depends(get_db)) -> DetailedHealthResponse:
    """Detailed health check with component statuses.

    Returns status of all subsystems:
    - Database connectivity
    - Google OAuth integration
    - LLM service (Anthropic)

    Overall status is:
    - "healthy": All critical components healthy
    - "degraded": Optional components degraded but app functional
    - "unhealthy": Critical components (database) unhealthy
    """
    components = {
        "database": check_database(db),
        "google_integration": check_google_integration(db),
        "llm_service": check_llm_service(),
    }

    # Determine overall status
    # Unhealthy if database is down (critical)
    # Degraded if optional services have issues
    # Healthy otherwise
    if components["database"].status == "unhealthy":
        overall_status = "unhealthy"
    elif any(c.status != "healthy" for c in components.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return DetailedHealthResponse(
        status=overall_status,
        service=settings.app_name,
        environment=settings.environment,
        host=socket.gethostname(),
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        components=components,
    )
