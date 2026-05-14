"""Project and membership models for multi-tenant document organization."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text

from app.db.session import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Project(Base):
    """Project model grouping documents under an organization or team.

    Project supports a small typology — `project_type` distinguishes between
    a generic project bucket and structured kinds (`thesis`, `paper`,
    `policy`, `report`). Type-specific extras live in `metadata_json`
    (NB: not named `metadata` because SQLAlchemy reserves that on Base).
    Visibility mirrors Document.visibility (`private` | `shared` | `public`).
    """

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    org_name = Column(String(255), nullable=True)
    style_config = Column(JSON, default=dict)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Typology + structured extras
    project_type = Column(
        String(20), nullable=False, default="general", index=True
    )
    metadata_json = Column(JSON, nullable=True)
    evidence_dashboard_url = Column(String(500), nullable=True)

    # ACL — same enum as Document.visibility
    visibility = Column(
        String(20), nullable=False, default="private", index=True
    )

    def __repr__(self) -> str:
        return f"<Project(slug={self.slug}, name={self.name}, type={self.project_type})>"


class ProjectMember(Base):
    """Membership linking users to projects with a role."""

    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), default="editor")
    added_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProjectMember(project={self.project_id}, user={self.user_id}, role={self.role})>"
