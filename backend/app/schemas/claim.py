"""Claim schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence supporting a claim."""

    kind: Literal["SQL", "BIB", "DATA", "INTERVIEW", "OBSERVATION"]
    ref: str
    output: str | None = None
    locator: str | None = None
    quote: str | None = None
    notes: str | None = None


class ClaimBase(BaseModel):
    """Base claim schema."""

    claim_text: str = Field(..., min_length=1)
    claim_type: Literal["DATA", "LITERATURE", "MIXED", "HYPOTHESIS"]
    section: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class ClaimCreate(ClaimBase):
    """Schema for creating a claim."""

    document_slug: str


class ClaimUpdate(BaseModel):
    """Schema for updating a claim."""

    claim_text: str | None = None
    claim_type: Literal["DATA", "LITERATURE", "MIXED", "HYPOTHESIS"] | None = None
    status: Literal["draft", "verified", "rejected", "needs_revision"] | None = None
    section: str | None = None
    evidence: list[Evidence] | None = None


class ClaimResponse(ClaimBase):
    """Schema for claim response."""

    id: UUID
    claim_id: str
    document_id: UUID
    status: str
    source_sentences: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
