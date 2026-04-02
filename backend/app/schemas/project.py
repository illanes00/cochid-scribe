"""Project schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    org_name: str | None = None
    style_config: dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    slug: str | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None
    org_name: str | None = None
    style_config: dict[str, Any] | None = None


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

    class Config:
        from_attributes = True


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
