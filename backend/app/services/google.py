"""Google integration helpers."""

from __future__ import annotations

from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.integration import Integration

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def get_client_config():
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uris": [settings.google_redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def ensure_integration(db: Session, provider: str) -> Integration:
    integration = db.query(Integration).filter(Integration.provider == provider).first()
    if integration:
        return integration
    integration = Integration(provider=provider)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def build_oauth_flow(state: str | None = None) -> Flow:
    settings = get_settings()
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )
    return flow


def get_auth_url(state: str | None = None) -> str:
    flow = build_oauth_flow(state=state)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> Credentials:
    flow = build_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def save_credentials(db: Session, provider: str, credentials: Credentials) -> Integration:
    integration = ensure_integration(db, provider)
    integration.access_token = credentials.token
    integration.refresh_token = credentials.refresh_token or integration.refresh_token
    integration.token_type = "Bearer"
    integration.scope = " ".join(credentials.scopes or [])
    integration.expires_at = credentials.expiry
    db.commit()
    db.refresh(integration)
    return integration


def get_google_credentials(db: Session) -> Credentials | None:
    integration = db.query(Integration).filter(Integration.provider == "google").first()
    if not integration or not integration.access_token:
        return None

    creds = Credentials(
        token=integration.access_token,
        refresh_token=integration.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().google_client_id,
        client_secret=get_settings().google_client_secret,
        scopes=SCOPES,
        expiry=integration.expires_at,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        integration.access_token = creds.token
        integration.expires_at = creds.expiry
        db.commit()

    return creds


def build_drive_service(db: Session):
    creds = get_google_credentials(db)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds)


def build_docs_service(db: Session):
    creds = get_google_credentials(db)
    if not creds:
        return None
    return build("docs", "v1", credentials=creds)
