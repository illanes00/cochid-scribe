"""Document version snapshot model."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class DocumentVersion(Base):
    """Snapshot of a document version."""

    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    label = Column(String(50), nullable=True)
    content = Column(JSON, nullable=False, default=dict)
    markdown = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", backref="versions")

    def __repr__(self) -> str:
        return f"<DocumentVersion(document_id={self.document_id}, label={self.label})>"
