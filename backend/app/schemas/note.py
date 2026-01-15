"""Pydantic schemas for notes."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base note schema."""

    title: str = Field(..., min_length=1, max_length=500)
    note_type: str = Field(default="idea")
    tags: list[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    """Schema for creating a note."""

    slug: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)
    markdown: str = ""


class NoteUpdate(BaseModel):
    """Schema for updating a note."""

    title: str | None = None
    content: dict[str, Any] | None = None
    markdown: str | None = None
    note_type: str | None = None
    tags: list[str] | None = None


class NoteResponse(NoteBase):
    """Schema for note response."""

    id: str
    slug: str
    content: dict[str, Any]
    markdown: str
    created_at: datetime
    updated_at: datetime
    backlink_count: int = 0

    class Config:
        from_attributes = True


class NoteList(BaseModel):
    """Schema for paginated note list."""

    notes: list[NoteResponse]
    total: int
    page: int
    per_page: int


# Link schemas

class LinkBase(BaseModel):
    """Base link schema."""

    source_type: str
    source_id: str
    target_type: str
    target_id: str
    link_type: str = "reference"
    context: str = ""


class LinkCreate(LinkBase):
    """Schema for creating a link."""

    pass


class LinkResponse(LinkBase):
    """Schema for link response."""

    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Graph schemas

class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str
    type: str  # note, document, claim, bib
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""

    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    """Knowledge graph data for visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
