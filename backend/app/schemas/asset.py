"""Asset schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AssetCreate(BaseModel):
    """Schema for creating an asset."""

    filename: str
    mime_type: str
    document_id: str | None = None


class AssetResponse(BaseModel):
    """Schema for asset response."""

    id: UUID
    document_id: UUID | None
    filename: str
    mime_type: str
    size_bytes: int
    url: str
    source_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True
