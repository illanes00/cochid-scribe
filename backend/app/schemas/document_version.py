"""Document version schemas."""

from datetime import datetime

from pydantic import BaseModel


class DocumentVersionCreate(BaseModel):
    """Create a document version snapshot."""

    label: str | None = None


class DocumentVersionResponse(BaseModel):
    """Response schema for version snapshot."""

    id: str
    document_id: str
    label: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionDetail(DocumentVersionResponse):
    """Detailed version response including content."""

    content: dict
    markdown: str | None = None
