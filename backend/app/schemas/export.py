"""Export schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ExportFormat = Literal["markdown", "html", "docx", "pptx", "latex", "pdf"]


class ExportRequest(BaseModel):
    """Request to export a document."""

    format: ExportFormat


class ExportJobResponse(BaseModel):
    """Export job response."""

    id: str
    document_id: str
    format: str
    status: str
    output_path: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
