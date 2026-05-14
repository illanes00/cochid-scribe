"""Projects API endpoints.

Projects group documents and now also model structured kinds (thesis, paper,
policy, report). Visibility (`private` / `shared` / `public`) mirrors
Document.visibility semantics:

- private: only the owner (creator) sees / writes
- shared:  any authenticated user can read; only owner can write
- public:  anyone (incl. anonymous) can read; only owner can write
"""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import _maybe_user, is_authenticated, require_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectChapter,
    ProjectCreate,
    ProjectDetailResponse,
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


# ─── ACL helpers ───────────────────────────────────────────────────────────


def _can_read_project(project: Project, user: User | None) -> bool:
    visibility = getattr(project, "visibility", "private") or "private"
    if visibility == "public":
        return True
    if user is None:
        return False
    if visibility == "shared":
        return True
    # private — owner only
    owner_id = getattr(project, "created_by", None)
    return bool(owner_id and owner_id == user.id)


def _require_owner(project: Project, user: User) -> None:
    if project.created_by and project.created_by != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not project.created_by:
        raise HTTPException(
            status_code=403, detail="Project has no owner; cannot write"
        )


def _chapter_order(doc: Document) -> int | None:
    fm = doc.front_matter or {}
    if isinstance(fm, dict):
        order = fm.get("order")
        if isinstance(order, (int, float)):
            return int(order)
    return None


def _chapter_view(doc: Document, db: Session) -> ProjectChapter:
    claims = db.query(Claim).filter(Claim.document_id == doc.id).all()
    verified = sum(1 for c in claims if c.status == "verified")
    return ProjectChapter(
        id=doc.id,
        slug=doc.slug,
        title=doc.title,
        doc_type=doc.doc_type,
        status=doc.status,
        order=_chapter_order(doc),
        updated_at=doc.updated_at,
        claim_count=len(claims),
        verified_count=verified,
    )


# ─── Endpoints ─────────────────────────────────────────────────────────────


@router.get("", response_model=list[ProjectResponse])
@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    request: Request,
    type: str | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
) -> list[Project]:
    """List projects the caller can read, optionally filtered by `type`.

    - Anonymous callers see only public projects.
    - Authenticated callers see: own (private) + shared + public.
    """
    user = _maybe_user(request, db)
    query = db.query(Project)
    if type:
        query = query.filter(Project.project_type == type)

    projects = query.order_by(Project.created_at.desc()).all()
    return [p for p in projects if _can_read_project(p, user)]


@router.post("", response_model=ProjectResponse, status_code=201)
@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> Project:
    """Create a new project owned by the current user."""
    user = require_user(request, db)
    slug = data.slug or _slugify(data.name)

    existing = db.query(Project).filter(Project.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Project slug '{slug}' already exists"
        )

    project = Project(
        slug=slug,
        name=data.name,
        description=data.description,
        org_name=data.org_name,
        style_config=data.style_config or {},
        project_type=data.project_type,
        metadata_json=data.metadata_json,
        evidence_dashboard_url=data.evidence_dashboard_url,
        visibility=data.visibility,
        created_by=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(
        "project.created",
        slug=slug,
        name=data.name,
        type=data.project_type,
        owner=user.email,
    )
    return project


@router.get("/{slug}", response_model=ProjectDetailResponse)
def get_project(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> ProjectDetailResponse:
    """Get a project by slug, with chapters + aggregate counts."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = _maybe_user(request, db)
    if not _can_read_project(project, user):
        # Hide existence from unauthorised callers.
        raise HTTPException(status_code=404, detail="Project not found")

    chapter_docs = (
        db.query(Document)
        .filter(Document.project_id == project.id)
        .order_by(Document.updated_at.desc())
        .all()
    )

    chapters = [_chapter_view(d, db) for d in chapter_docs]
    # Stable sort: explicit `order` first, then untouched (most recently updated).
    chapters.sort(
        key=lambda c: (c.order is None, c.order if c.order is not None else 0)
    )

    chapter_ids = [d.id for d in chapter_docs]
    claim_count = 0
    if chapter_ids:
        claim_count = (
            db.query(Claim).filter(Claim.document_id.in_(chapter_ids)).count()
        )

    # Bibliography is currently a global table (no project FK). Until it's
    # scoped per-project, surface 0 to keep the contract honest.
    bibliography_count = 0

    return ProjectDetailResponse(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        org_name=project.org_name,
        style_config=project.style_config or {},
        created_by=project.created_by,
        created_at=project.created_at,
        project_type=project.project_type,
        metadata_json=project.metadata_json,
        evidence_dashboard_url=project.evidence_dashboard_url,
        visibility=project.visibility,
        chapters=chapters,
        bibliography_count=bibliography_count,
        claim_count=claim_count,
    )


@router.put("/{slug}", response_model=ProjectResponse)
def update_project(
    slug: str,
    data: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> Project:
    """Update a project. Only the owner can write."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = require_user(request, db)
    _require_owner(project, user)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    logger.info("project.updated", slug=slug, fields=list(update_data.keys()))
    return project


@router.delete("/{slug}", status_code=204)
def delete_project(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """Delete a project. Owner only."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = require_user(request, db)
    _require_owner(project, user)

    db.delete(project)
    db.commit()
    logger.info("project.deleted", slug=slug)


@router.post("/{slug}/members", response_model=ProjectMemberResponse, status_code=201)
def add_member(
    slug: str,
    data: ProjectMemberCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ProjectMember:
    """Add a member to a project. Owner only."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = require_user(request, db)
    _require_owner(project, user)

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="User is already a member of this project"
        )

    member = ProjectMember(
        project_id=project.id,
        user_id=data.user_id,
        role=data.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    logger.info(
        "project.member_added", slug=slug, user_id=data.user_id, role=data.role
    )
    return member


@router.delete("/{slug}/members/{user_id}", status_code=204)
def remove_member(
    slug: str,
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """Remove a member from a project. Owner only."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = require_user(request, db)
    _require_owner(project, user)

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
