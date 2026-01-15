"""Pydantic schemas."""

from app.schemas.bibliography import (
    BibEntryCreate,
    BibEntryResponse,
)
from app.schemas.claim import (
    ClaimCreate,
    ClaimResponse,
    ClaimUpdate,
    Evidence,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
)

__all__ = [
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentList",
    "ClaimCreate",
    "ClaimUpdate",
    "ClaimResponse",
    "Evidence",
    "BibEntryCreate",
    "BibEntryResponse",
]
