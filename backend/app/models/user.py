"""User model for multi-user authentication."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model synced from Authentik SSO."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    role = Column(String(20), default="editor")
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User(email={self.email}, role={self.role})>"
