"""Database session configuration."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite needs different configuration than PostgreSQL
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
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
        document,
        document_version,
        export,
        integration,
        note,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_claim_offsets()
    print(f"Database initialized: {settings.database_url}")


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
