"""Document model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base

if TYPE_CHECKING:
    pass


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Document(Base):
    """Document model for academic papers, thesis, policy briefs."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    doc_type = Column(String(20), nullable=False, default="paper")
    content = Column(JSON, nullable=False, default=dict)
    markdown = Column(Text)
    front_matter = Column(JSON, default=dict)
    version = Column(String(20), default="1.0.0")
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_provider = Column(String(50), nullable=True)
    source_id = Column(String(200), nullable=True)

    # Relationships
    claims = relationship("Claim", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(slug={self.slug}, title={self.title})>"
