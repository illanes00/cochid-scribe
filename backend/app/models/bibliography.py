"""Bibliography model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.session import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class BibliographyEntry(Base):
    """Bibliography entry model for references."""

    __tablename__ = "bibliography_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bib_key = Column(String(100), unique=True, nullable=False, index=True)
    entry_type = Column(String(20), nullable=False, default="misc")
    title = Column(Text, nullable=False)
    author = Column(Text, nullable=False)
    year = Column(Integer)
    journal = Column(Text)
    booktitle = Column(Text)
    volume = Column(String(50))
    number = Column(String(50))
    pages = Column(String(50))
    publisher = Column(Text)
    doi = Column(String(255))
    url = Column(Text)
    abstract = Column(Text)
    bibtex = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BibliographyEntry(bib_key={self.bib_key})>"
