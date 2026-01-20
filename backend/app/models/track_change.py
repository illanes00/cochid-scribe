"""Track Changes model for document revision tracking."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class ChangeType(str, enum.Enum):
    """Type of tracked change."""
    INSERT = "insert"
    DELETE = "delete"


class ChangeStatus(str, enum.Enum):
    """Status of a tracked change."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TrackChange(Base):
    """Model for tracking document changes.

    Each change represents an insertion or deletion that has been tracked
    in the document. Changes can be pending, accepted, or rejected.

    The actual content is stored in the TipTap document JSON as marks.
    This model stores metadata about the changes for UI and history.
    """
    __tablename__ = "track_changes"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Change identification
    change_id = Column(String(50), nullable=False, index=True)  # Unique ID within document
    change_type = Column(Enum(ChangeType), nullable=False)

    # Content info
    content = Column(Text, nullable=True)  # The text that was inserted/deleted
    position_start = Column(Integer, nullable=True)  # Position in document
    position_end = Column(Integer, nullable=True)

    # Attribution
    author_name = Column(String(255), nullable=True)
    author_email = Column(String(255), nullable=True)

    # Status tracking
    status = Column(Enum(ChangeStatus), default=ChangeStatus.PENDING, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)

    # Comment on resolution
    resolution_comment = Column(Text, nullable=True)

    # Relationship
    document = relationship("Document", back_populates="track_changes")

    def __repr__(self):
        return f"<TrackChange(id={self.id}, type={self.change_type}, status={self.status})>"

    def accept(self, resolved_by: str = None, comment: str = None):
        """Accept this change."""
        self.status = ChangeStatus.ACCEPTED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_comment = comment

    def reject(self, resolved_by: str = None, comment: str = None):
        """Reject this change."""
        self.status = ChangeStatus.REJECTED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_comment = comment
