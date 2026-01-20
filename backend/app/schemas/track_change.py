"""Pydantic schemas for Track Changes."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of tracked change."""
    INSERT = "insert"
    DELETE = "delete"


class ChangeStatus(str, Enum):
    """Status of a tracked change."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TrackChangeBase(BaseModel):
    """Base schema for track changes."""
    change_id: str = Field(..., description="Unique change identifier")
    change_type: ChangeType
    content: Optional[str] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class TrackChangeCreate(TrackChangeBase):
    """Schema for creating a track change."""
    pass


class TrackChangeUpdate(BaseModel):
    """Schema for updating a track change."""
    status: Optional[ChangeStatus] = None
    resolution_comment: Optional[str] = None


class TrackChangeResponse(TrackChangeBase):
    """Schema for track change response."""
    id: int
    document_id: str
    status: ChangeStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_comment: Optional[str] = None

    class Config:
        from_attributes = True


class TrackChangesListResponse(BaseModel):
    """Response containing list of track changes."""
    changes: list[TrackChangeResponse]
    total: int
    pending_count: int
    accepted_count: int
    rejected_count: int


class ResolveChangeRequest(BaseModel):
    """Request to accept or reject a change."""
    action: str = Field(..., pattern="^(accept|reject)$", description="Action: 'accept' or 'reject'")
    comment: Optional[str] = None
    resolved_by: Optional[str] = None


class ResolveChangeResponse(BaseModel):
    """Response after resolving a change."""
    success: bool
    change: TrackChangeResponse
    message: str


class BulkResolveRequest(BaseModel):
    """Request to resolve multiple changes at once."""
    change_ids: list[str]
    action: str = Field(..., pattern="^(accept|reject)$")
    comment: Optional[str] = None
    resolved_by: Optional[str] = None


class BulkResolveResponse(BaseModel):
    """Response after bulk resolving changes."""
    success: bool
    resolved_count: int
    message: str


class ExtractChangesRequest(BaseModel):
    """Request to extract changes from TipTap content."""
    content: dict = Field(..., description="TipTap JSON content with change marks")
    author_name: Optional[str] = None
    author_email: Optional[str] = None
