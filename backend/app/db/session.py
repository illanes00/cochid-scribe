"""Database session configuration."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _normalize_database_url(database_url: str) -> str:
    """Resolve relative SQLite paths against the backend root."""
    if not database_url.startswith("sqlite:///"):
        return database_url

    prefix = "sqlite:///"
    raw_path = database_url[len(prefix):]
    if not raw_path or raw_path.startswith("/"):
        return database_url

    path_part, separator, query = raw_path.partition("?")
    resolved_path = (BACKEND_ROOT / path_part).resolve()
    normalized = f"{prefix}{resolved_path}"
    if separator:
        normalized = f"{normalized}?{query}"
    return normalized


normalized_database_url = _normalize_database_url(settings.database_url)

# SQLite needs different configuration than PostgreSQL
if normalized_database_url.startswith("sqlite"):
    engine = create_engine(
        normalized_database_url,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        normalized_database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    # Import all models to register them with Base
    from app.models import (  # noqa: F401
        asset,
        bibliography,
        claim,
        comment,
        dataset,
        dictation_session,
        document,
        document_version,
        export,
        integration,
        note,
        project,
        user,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_claim_offsets()
    _ensure_multiuser_columns()

    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("db.initialized", database_url=normalized_database_url)


def _ensure_multiuser_columns() -> None:
    """Add nullable FK columns for multi-user support on existing tables."""
    migrations = [
        ("documents", "owner_id", "VARCHAR(36)"),
        ("documents", "project_id", "VARCHAR(36)"),
        ("comments", "user_id", "VARCHAR(36)"),
    ]
    try:
        with engine.begin() as conn:
            for table, column, col_type in migrations:
                if settings.database_url.startswith("sqlite"):
                    result = conn.exec_driver_sql(f"PRAGMA table_info({table})")
                    columns = {row[1] for row in result}
                    if column not in columns:
                        conn.exec_driver_sql(
                            f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                        )
                else:
                    conn.exec_driver_sql(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                    )
    except Exception:
        # Best-effort: do not block application startup.
        return


def _ensure_claim_offsets() -> None:
    """Add claim offset columns for databases if missing."""
    try:
        with engine.begin() as conn:
            if settings.database_url.startswith("sqlite"):
                result = conn.exec_driver_sql("PRAGMA table_info(claims)")
                columns = {row[1] for row in result}
                if "start_offset" not in columns:
                    conn.exec_driver_sql("ALTER TABLE claims ADD COLUMN start_offset INTEGER")
                if "end_offset" not in columns:
                    conn.exec_driver_sql("ALTER TABLE claims ADD COLUMN end_offset INTEGER")
                return

            conn.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS start_offset INTEGER")
            conn.exec_driver_sql("ALTER TABLE claims ADD COLUMN IF NOT EXISTS end_offset INTEGER")
    except Exception:
        # Best-effort: do not block application startup.
        return
