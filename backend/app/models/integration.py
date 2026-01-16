"""Integration model for external providers like Google."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Integration(Base):
    """Stored integration credentials."""

    __tablename__ = "integrations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(50), nullable=False, unique=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(40), nullable=True)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
