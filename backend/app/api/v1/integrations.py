"""Integration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models.integration import Integration
from app.schemas.integration import IntegrationStatus, IntegrationTokenUpdate
from app.services.google import exchange_code_for_tokens, get_auth_url, save_credentials

router = APIRouter()


@router.get("/google/status", response_model=IntegrationStatus)
async def google_status(db: Session = Depends(get_db)):
    """Check Google integration status."""
    integration = db.query(Integration).filter(Integration.provider == "google").first()
    return IntegrationStatus(
        provider="google",
        connected=bool(integration and integration.access_token),
        expires_at=integration.expires_at if integration else None,
    )


@router.post("/google/auth-url")
async def google_auth_url():
    """Generate Google OAuth URL."""
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    return {"url": get_auth_url()}


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """OAuth callback to store Google tokens."""
    credentials = exchange_code_for_tokens(code)
    integration = save_credentials(db, "google", credentials)
    return {
        "provider": integration.provider,
        "connected": True,
        "expires_at": integration.expires_at,
    }


@router.post("/tokens")
async def update_tokens(payload: IntegrationTokenUpdate, db: Session = Depends(get_db)):
    """Manually store tokens for an integration."""
    integration = db.query(Integration).filter(Integration.provider == payload.provider).first()
    if not integration:
        integration = Integration(provider=payload.provider)
        db.add(integration)
    integration.access_token = payload.access_token
    integration.refresh_token = payload.refresh_token
    integration.token_type = payload.token_type
    integration.scope = payload.scope
    integration.expires_at = payload.expires_at
    db.commit()
    return {"provider": integration.provider, "connected": True}
