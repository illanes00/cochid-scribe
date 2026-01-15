"""Pydantic schemas for datasets and charts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# Dataset schemas

class ColumnInfo(BaseModel):
    """Information about a dataset column."""

    name: str
    type: str  # string, number, date, boolean
    sample_values: list[Any] = Field(default_factory=list)


class DatasetBase(BaseModel):
    """Base dataset schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    data_type: str = "csv"


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset."""

    slug: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[ColumnInfo] = Field(default_factory=list)


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset."""

    name: str | None = None
    description: str | None = None
    data: list[dict[str, Any]] | None = None
    columns: list[ColumnInfo] | None = None


class DatasetResponse(DatasetBase):
    """Schema for dataset response."""

    id: str
    slug: str
    data: list[dict[str, Any]]
    columns: list[ColumnInfo]
    row_count: int
    source_file: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetList(BaseModel):
    """Schema for paginated dataset list."""

    datasets: list[DatasetResponse]
    total: int
    page: int
    per_page: int


class DatasetSummary(BaseModel):
    """Brief dataset info (without full data)."""

    id: str
    slug: str
    name: str
    description: str
    data_type: str
    row_count: int
    columns: list[ColumnInfo]
    created_at: datetime

    class Config:
        from_attributes = True


# Chart schemas

class ChartConfig(BaseModel):
    """Configuration for a chart."""

    x_column: str | None = None
    y_column: str | None = None
    color_column: str | None = None
    size_column: str | None = None
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    legend: bool = True
    grid: bool = True
    colors: list[str] = Field(default_factory=list)


class ChartBase(BaseModel):
    """Base chart schema."""

    title: str = Field(..., min_length=1, max_length=500)
    chart_type: str  # bar, line, scatter, pie, table, area


class ChartCreate(ChartBase):
    """Schema for creating a chart."""

    slug: str | None = None
    dataset_id: str | None = None
    config: ChartConfig = Field(default_factory=ChartConfig)


class ChartUpdate(BaseModel):
    """Schema for updating a chart."""

    title: str | None = None
    chart_type: str | None = None
    dataset_id: str | None = None
    config: ChartConfig | None = None


class ChartResponse(ChartBase):
    """Schema for chart response."""

    id: str
    slug: str
    dataset_id: str | None
    config: ChartConfig
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChartList(BaseModel):
    """Schema for paginated chart list."""

    charts: list[ChartResponse]
    total: int
    page: int
    per_page: int
