"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from illanes_auth import AuthSettingsMixin
from pydantic_settings import BaseSettings


class Settings(AuthSettingsMixin, BaseSettings):
    """Application settings.

    OIDC/auth fields come from AuthSettingsMixin (oidc_issuer, oidc_client_id,
    oidc_client_secret, oidc_redirect_uri, oidc_scopes, secret_key,
    auth_enabled, etc). Defaults from the mixin are intentionally generic —
    real values arrive via env vars sourced by systemd EnvironmentFile.
    """

    # App
    app_name: str = "Scribe API"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./scribe.db"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Google OAuth (separate from Authentik SSO)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/google/callback"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    workspace_docs_root: str = str(Path(__file__).resolve().parents[2] / "docs")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
