"""Dataset and Chart models for data visualization."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.session import Base


def generate_uuid():
    import uuid
    return str(uuid.uuid4())


class Dataset(Base):
    """A dataset for visualization and analysis."""

    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, default="")
    data_type = Column(String(50), nullable=False)  # csv, json, manual
    data = Column(JSON, nullable=False, default=list)  # Parsed data rows
    columns = Column(JSON, default=list)  # Column metadata [{name, type, ...}]
    row_count = Column(Integer, default=0)
    source_file = Column(String(500), default="")  # Original filename
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Chart(Base):
    """A saved chart visualization."""

    __tablename__ = "charts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    chart_type = Column(String(50), nullable=False)  # bar, line, scatter, pie, table
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    config = Column(JSON, nullable=False, default=dict)  # Chart configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
