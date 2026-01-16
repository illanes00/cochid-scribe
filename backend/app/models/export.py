"""Export job model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class ExportJob(Base):
    """Export job for document conversions."""

    __tablename__ = "export_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    format = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    output_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
