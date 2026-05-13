"""Add document.visibility column + dictation_sessions table.

- documents.visibility (string, default 'private', not null, indexed).
- dictation_sessions table (was previously created by SQLAlchemy
  create_all in SQLite but never had a migration; this brings Postgres
  to parity).

Revision ID: a1b2c3d4e5f6
Revises: 6f0b578c3e54
Create Date: 2026-05-13 22:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6f0b578c3e54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # documents.visibility
    op.add_column(
        "documents",
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="private",
        ),
    )
    op.create_index("ix_documents_visibility", "documents", ["visibility"])

    # dictation_sessions — must match app.models.dictation_session.DictationSession
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "dictation_sessions" not in inspector.get_table_names():
        op.create_table(
            "dictation_sessions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("workspace_slug", sa.String(length=255), nullable=False, server_default="cif-medicamentos"),
            sa.Column("document_slug", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
            sa.Column("transcript", sa.Text(), nullable=False, server_default=""),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("chunk_log", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("slug"),
        )
        op.create_index("ix_dictation_sessions_slug", "dictation_sessions", ["slug"], unique=True)
        op.create_index("ix_dictation_sessions_document_slug", "dictation_sessions", ["document_slug"])
        op.create_index("ix_dictation_sessions_created_at", "dictation_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_table("dictation_sessions")
    op.drop_index("ix_documents_visibility", table_name="documents")
    op.drop_column("documents", "visibility")
