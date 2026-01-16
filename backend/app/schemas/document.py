"""Document schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema."""

    title: str = Field(..., min_length=1, max_length=500)
    doc_type: Literal["paper", "thesis", "policy", "presentation"] = "paper"
    content: dict[str, Any] = Field(default_factory=dict)
    markdown: str | None = None
    front_matter: dict[str, Any] = Field(default_factory=dict)
    source_provider: str | None = None
    source_id: str | None = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    slug: str | None = None  # Auto-generated if not provided


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    title: str | None = None
    doc_type: Literal["paper", "thesis", "policy", "presentation"] | None = None
    content: dict[str, Any] | None = None
    markdown: str | None = None
    front_matter: dict[str, Any] | None = None
    status: Literal["draft", "review", "final"] | None = None
    source_provider: str | None = None
    source_id: str | None = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: UUID
    slug: str
    status: str
    version: str
    created_at: datetime
    updated_at: datetime
    claim_count: int = 0
    verified_count: int = 0

    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Schema for document list response."""

    documents: list[DocumentResponse]
    total: int
    page: int
    per_page: int
