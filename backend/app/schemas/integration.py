"""Integration schemas."""

from datetime import datetime

from pydantic import BaseModel


class IntegrationStatus(BaseModel):
    """Integration status response."""

    provider: str
    connected: bool
    expires_at: datetime | None = None


class IntegrationTokenUpdate(BaseModel):
    """Manual token update for integrations."""

    provider: str
    access_token: str
    refresh_token: str | None = None
    token_type: str | None = None
    scope: str | None = None
    expires_at: datetime | None = None
