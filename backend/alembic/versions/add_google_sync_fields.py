"""add_google_sync_fields

Add Google Docs synchronization fields to documents table.

Revision ID: add_google_sync_001
Revises: 51e906076f28
Create Date: 2026-01-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_google_sync_001"
down_revision: Union[str, Sequence[str], None] = "51e906076f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Google Docs sync fields to documents table."""
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("google_revision_id", sa.String(100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_synced_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("sync_status", sa.String(20), server_default="none", nullable=True)
        )
        batch_op.add_column(
            sa.Column("local_version_hash", sa.String(64), nullable=True)
        )


def downgrade() -> None:
    """Remove Google Docs sync fields from documents table."""
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_column("local_version_hash")
        batch_op.drop_column("sync_status")
        batch_op.drop_column("last_synced_at")
        batch_op.drop_column("google_revision_id")
