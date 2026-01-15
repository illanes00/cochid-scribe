"""Note model for Knowledge Base."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String, Text

from app.db.session import Base


def generate_uuid():
    import uuid
    return str(uuid.uuid4())


class Note(Base):
    """A note/idea in the knowledge base (Obsidian-like)."""

    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(JSON, nullable=False, default=dict)  # Tiptap JSON
    markdown = Column(Text, default="")
    note_type = Column(String(50), default="idea")  # idea, summary, quote, concept
    tags = Column(JSON, default=list)  # List of tag strings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Link(Base):
    """Links between knowledge base entities (graph edges).

    This is a polymorphic table that can link any entity type to any other.
    No ForeignKey constraints since source/target can be different entity types.
    """

    __tablename__ = "links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_type = Column(String(50), nullable=False)  # note, document, claim, bib
    source_id = Column(String(36), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False, index=True)
    link_type = Column(String(50), default="reference")  # reference, supports, contradicts
    context = Column(Text, default="")  # Text around the link
    created_at = Column(DateTime, default=datetime.utcnow)
