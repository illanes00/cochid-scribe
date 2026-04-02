"""Projects API endpoints."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


def _slugify(name: str) -> str:
    """Generate a URL-safe slug from a project name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or str(uuid.uuid4())[:8]


@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    """List all projects."""
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
) -> Project:
    """Create a new project."""
    slug = data.slug or _slugify(data.name)

    existing = db.query(Project).filter(Project.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Project slug '{slug}' already exists")

    project = Project(
        slug=slug,
        name=data.name,
        description=data.description,
        org_name=data.org_name,
        style_config=data.style_config,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info("project.created", slug=slug, name=data.name)
    return project


@router.get("/{slug}", response_model=ProjectResponse)
def get_project(slug: str, db: Session = Depends(get_db)) -> Project:
    """Get a project by slug."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{slug}", response_model=ProjectResponse)
def update_project(
    slug: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
) -> Project:
    """Update a project."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    logger.info("project.updated", slug=slug)
    return project


@router.delete("/{slug}", status_code=204)
def delete_project(slug: str, db: Session = Depends(get_db)) -> None:
    """Delete a project."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    logger.info("project.deleted", slug=slug)


@router.post("/{slug}/members", response_model=ProjectMemberResponse, status_code=201)
def add_member(
    slug: str,
    data: ProjectMemberCreate,
    db: Session = Depends(get_db),
) -> ProjectMember:
    """Add a member to a project."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member of this project")

    member = ProjectMember(
        project_id=project.id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    logger.info("project.member_added", slug=slug, user_id=data.user_id, role=data.role)
    return member


@router.delete("/{slug}/members/{user_id}", status_code=204)
def remove_member(
    slug: str,
    user_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Remove a member from a project."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
    logger.info("project.member_removed", slug=slug, user_id=user_id)
