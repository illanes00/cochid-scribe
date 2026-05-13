"""Dictation session model for chunked audio transcription workflows."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class DictationSession(Base):
    """Stores a dictation workspace with transcript and chunk audit trail."""

    __tablename__ = "dictation_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    workspace_slug = Column(String(255), nullable=False, default="cif-medicamentos")
    document_slug = Column(String(255), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="idle")
    transcript = Column(Text, nullable=False, default="")
    notes = Column(Text, nullable=False, default="")
    chunk_count = Column(Integer, nullable=False, default=0)
    chunk_log = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
