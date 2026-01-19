"""Claim model."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Claim(Base):
    """Claim model for verifiable assertions in documents."""

    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(50), unique=True, nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(20), nullable=False, default="MIXED")
    status = Column(String(20), default="draft")
    section = Column(String(100))
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    evidence = Column(JSON, default=list)
    source_sentences = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="claims")

    def __repr__(self) -> str:
        return f"<Claim(claim_id={self.claim_id}, status={self.status})>"
