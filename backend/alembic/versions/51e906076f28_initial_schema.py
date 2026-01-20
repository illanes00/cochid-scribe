"""initial_schema

Baseline migration representing the initial database schema.
For existing databases, this is a no-op (tables already exist).
For new databases, this migration is run by init_db() via create_all().

Revision ID: 51e906076f28
Revises:
Create Date: 2026-01-20

Note: This migration serves as a baseline marker. The actual table
creation is handled by SQLAlchemy's Base.metadata.create_all() in
app/db/session.py for compatibility with both fresh and existing installs.
"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "51e906076f28"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - baseline migration.

    Tables created by this baseline:
    - documents: Main document storage
    - claims: Verifiable assertions in documents
    - bibliography: Reference citations
    - notes: Knowledge base entries
    - datasets: Data attachments
    - assets: Uploaded files
    - export_jobs: Export task tracking
    - integrations: OAuth tokens (Google, etc.)
    - comments: Document comments/annotations
    - document_versions: Version history snapshots

    Note: For existing databases, these tables already exist via create_all().
    This migration marks the database as being at the baseline schema.
    """
    # Tables are created by Base.metadata.create_all() in init_db()
    # This migration serves as a baseline marker for Alembic
    pass


def downgrade() -> None:
    """Downgrade schema.

    Warning: Downgrading from baseline would drop all tables.
    This is typically not desirable for production databases.
    """
    # For safety, we don't implement table drops in the baseline migration.
    # If you truly need to downgrade, drop tables manually or use a fresh DB.
    pass
