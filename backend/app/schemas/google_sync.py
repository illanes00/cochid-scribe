"""Google Docs sync schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SyncStatusType = Literal["none", "synced", "local_changed", "remote_changed", "conflict"]
ResolveStrategy = Literal["keep_local", "keep_remote"]


class LinkRequest(BaseModel):
    """Request to link a Scribe document with a Google Doc."""

    google_doc_id: str = Field(..., description="Google Doc file ID")


class LinkResponse(BaseModel):
    """Response after linking a document."""

    success: bool
    google_doc_id: str
    google_revision_id: str | None = None
    message: str | None = None


class SyncStatusResponse(BaseModel):
    """Current sync status of a document."""

    linked: bool
    google_doc_id: str | None = None
    sync_status: SyncStatusType = "none"
    last_synced_at: datetime | None = None
    google_revision_id: str | None = None
    local_version_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PushResponse(BaseModel):
    """Response after pushing to Google Docs."""

    success: bool
    new_revision_id: str | None = None
    claims_preserved: int = 0
    citations_preserved: int = 0
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class PullResponse(BaseModel):
    """Response after pulling from Google Docs."""

    success: bool
    claims_restored: int = 0
    citations_restored: int = 0
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class ResolveRequest(BaseModel):
    """Request to resolve a sync conflict."""

    strategy: ResolveStrategy = Field(..., description="Conflict resolution strategy")


class ResolveResponse(BaseModel):
    """Response after resolving a conflict."""

    success: bool
    new_sync_status: SyncStatusType
    message: str | None = None
