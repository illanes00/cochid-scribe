"""Project schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProjectType = Literal["general", "thesis", "paper", "policy", "report"]
Visibility = Literal["private", "shared", "public"]


class ProjectChapter(BaseModel):
    """Lightweight document-as-chapter view for project detail responses."""

    id: str
    slug: str
    title: str
    doc_type: str
    status: str
    order: int | None = None
    updated_at: datetime
    claim_count: int = 0
    verified_count: int = 0

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    org_name: str | None = None
    style_config: dict[str, Any] = Field(default_factory=dict)
    project_type: ProjectType = "general"
    metadata_json: dict[str, Any] | None = None
    evidence_dashboard_url: str | None = None
    visibility: Visibility = "private"


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    slug: str | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None
    org_name: str | None = None
    style_config: dict[str, Any] | None = None
    project_type: ProjectType | None = None
    metadata_json: dict[str, Any] | None = None
    evidence_dashboard_url: str | None = None
    visibility: Visibility | None = None


class ProjectResponse(BaseModel):
    """Schema for project responses."""

    id: str
    slug: str
    name: str
    description: str | None = None
    org_name: str | None = None
    style_config: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime
    project_type: ProjectType = "general"
    metadata_json: dict[str, Any] | None = None
    evidence_dashboard_url: str | None = None
    visibility: Visibility = "private"

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Project detail with embedded chapters + aggregate counts."""

    chapters: list[ProjectChapter] = Field(default_factory=list)
    bibliography_count: int = 0
    claim_count: int = 0


class ProjectMemberCreate(BaseModel):
    """Schema for adding a member to a project."""

    user_id: str
    role: str = "editor"


class ProjectMemberResponse(BaseModel):
    """Schema for project member responses."""

    id: str
    project_id: str
    user_id: str
    role: str
    added_at: datetime

    class Config:
        from_attributes = True
