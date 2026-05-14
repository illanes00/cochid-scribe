"""Seed Martin's thesis project.

Idempotent: if the project already exists, prints its id+slug and exits.
"""

from __future__ import annotations

import sys

from app.db.session import SessionLocal
from app.models.project import Project
from app.models.user import User


MARTIN_EMAIL = "martinillanesv@gmail.com"
THESIS_SLUG = "tesis-biotech-puerto-varas"


def main() -> int:
    db = SessionLocal()
    try:
        martin = db.query(User).filter(User.email == MARTIN_EMAIL).first()
        if martin is None:
            print(
                f"[seed] ERROR: user {MARTIN_EMAIL!r} not found. "
                "Log in once at scribe.cochid.cl to provision the row, then re-run.",
                file=sys.stderr,
            )
            return 2

        existing = db.query(Project).filter(Project.slug == THESIS_SLUG).first()
        if existing:
            print(
                "[seed] Thesis project already exists — leaving as-is.\n"
                f"  id={existing.id}\n"
                f"  slug={existing.slug}\n"
                f"  owner={existing.created_by}\n"
                f"  type={existing.project_type}\n"
                f"  visibility={existing.visibility}\n"
                f"  dashboard={existing.evidence_dashboard_url}"
            )
            return 0

        project = Project(
            slug=THESIS_SLUG,
            name=(
                "Sustitución de funciones universitarias en el cluster biotech "
                "de Puerto Varas, Los Lagos"
            ),
            description=(
                "Tesis de magíster · análisis del cluster biotech de Puerto "
                "Varas con datos SII, CASEN, patentes."
            ),
            project_type="thesis",
            visibility="private",
            created_by=martin.id,
            evidence_dashboard_url="https://thesis.cochid.cl",
            metadata_json={
                "advisor": "(por definir)",
                "university": "(por definir)",
                "programme": "Magíster",
                "status": "drafting",
                "defense_date": None,
            },
            style_config={},
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        print(
            "[seed] Created thesis project:\n"
            f"  id={project.id}\n"
            f"  slug={project.slug}\n"
            f"  owner={project.created_by} ({martin.email})\n"
            f"  type={project.project_type}\n"
            f"  visibility={project.visibility}\n"
            f"  dashboard={project.evidence_dashboard_url}"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
