"""Add project type, metadata_json, evidence_dashboard_url, visibility on projects.

Enables the multi-user thesis ecosystem on top of the existing Project model:
- project_type (general|thesis|paper|policy|report)
- metadata_json: JSON blob for type-specific extra fields (advisor, university, ...)
- evidence_dashboard_url: external dashboard link (e.g. https://thesis.cochid.cl)
- visibility (private|shared|public), same enum as Document.visibility

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-05-13 23:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "project_type",
            sa.String(length=20),
            nullable=False,
            server_default="general",
        ),
    )
    op.create_index("ix_projects_project_type", "projects", ["project_type"])

    op.add_column(
        "projects",
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )

    op.add_column(
        "projects",
        sa.Column("evidence_dashboard_url", sa.String(length=500), nullable=True),
    )

    op.add_column(
        "projects",
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="private",
        ),
    )
    op.create_index("ix_projects_visibility", "projects", ["visibility"])


def downgrade() -> None:
    op.drop_index("ix_projects_visibility", table_name="projects")
    op.drop_column("projects", "visibility")
    op.drop_column("projects", "evidence_dashboard_url")
    op.drop_column("projects", "metadata_json")
    op.drop_index("ix_projects_project_type", table_name="projects")
    op.drop_column("projects", "project_type")
