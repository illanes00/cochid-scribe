"""Bibliography schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BibEntryBase(BaseModel):
    """Base bibliography entry schema."""

    bib_key: str = Field(..., min_length=1, max_length=100)
    entry_type: Literal[
        "article", "book", "incollection", "inproceedings", "techreport", "thesis", "misc"
    ]
    title: str
    author: str
    year: int | None = None
    journal: str | None = None
    booktitle: str | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    publisher: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None


class BibEntryCreate(BibEntryBase):
    """Schema for creating a bibliography entry."""

    bibtex: str | None = None


class BibEntryResponse(BibEntryBase):
    """Schema for bibliography entry response."""

    id: UUID
    bibtex: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class BibSearchResult(BaseModel):
    """Schema for semantic search results."""

    entry: BibEntryResponse
    score: float
