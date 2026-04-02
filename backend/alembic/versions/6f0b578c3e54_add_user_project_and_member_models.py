"""add user project and member models

Add FK constraints and indexes for multi-user support.
Tables (users, projects, project_members) were already created by
init_db() / create_all(). This migration adds the missing FK
constraints on documents and comments, plus indexes.

Revision ID: 6f0b578c3e54
Revises: add_google_sync_001
Create Date: 2026-04-02 06:20:34.717535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f0b578c3e54"
down_revision: Union[str, Sequence[str], None] = "add_google_sync_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# SQLite batch mode needs the existing table's columns to recreate it.
# We declare naming_convention so batch mode can identify unnamed FKs.
naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    """Add multi-user FK constraints and indexes."""
    # --- comments table ---
    # Recreate via batch to add user_id FK and fix parent_id FK with ON DELETE SET NULL
    with op.batch_alter_table(
        "comments",
        schema=None,
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_comments_document_id"), ["document_id"], unique=False
        )
        # Drop the old unnamed parent_id FK; batch mode identifies by referent
        batch_op.drop_constraint(
            "fk_comments_parent_id_comments", type_="foreignkey"
        )
        # Re-add parent_id FK with ON DELETE SET NULL
        batch_op.create_foreign_key(
            "fk_comments_parent_id_comments",
            "comments",
            ["parent_id"],
            ["id"],
            ondelete="SET NULL",
        )
        # Add user_id FK
        batch_op.create_foreign_key(
            "fk_comments_user_id_users", "users", ["user_id"], ["id"]
        )

    # --- documents table ---
    # Add FK constraints for owner_id and project_id columns (already exist)
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_documents_created_at"), ["created_at"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_documents_owner_id_users", "users", ["owner_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_documents_project_id_projects",
            "projects",
            ["project_id"],
            ["id"],
        )


def downgrade() -> None:
    """Remove multi-user FK constraints and indexes."""
    with op.batch_alter_table(
        "documents",
        schema=None,
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_documents_project_id_projects", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_documents_owner_id_users", type_="foreignkey"
        )
        batch_op.drop_index(batch_op.f("ix_documents_created_at"))

    with op.batch_alter_table(
        "comments",
        schema=None,
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_comments_user_id_users", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_comments_parent_id_comments", type_="foreignkey"
        )
        # Restore original unnamed FK
        batch_op.create_foreign_key(
            None, "comments", ["parent_id"], ["id"]
        )
        batch_op.drop_index(batch_op.f("ix_comments_document_id"))
