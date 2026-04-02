"""Comment model for document annotations."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Comment(Base):
    """External or local comment tied to a document."""

    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    parent_id = Column(String(36), ForeignKey("comments.id", ondelete="SET NULL"), nullable=True)
    anchor_id = Column(String(36), nullable=True)
    provider = Column(String(50), default="local")  # local, google
    external_id = Column(String(100), nullable=True)
    author = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    quote = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    # Classification: general (whole doc), section (specific section), inline (specific text)
    comment_scope = Column(String(20), default="general")  # general | section | inline
    section = Column(String(255), nullable=True)  # section name/heading reference
    # Multi-user: link comment to authenticated user (nullable for migration safety)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
