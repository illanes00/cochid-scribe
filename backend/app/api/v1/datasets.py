"""Datasets API endpoints."""

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from slugify import slugify
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import (
    ColumnInfo,
    DatasetCreate,
    DatasetList,
    DatasetResponse,
    DatasetSummary,
    DatasetUpdate,
)

router = APIRouter()


def generate_unique_slug(db: Session, name: str, existing_slug: str | None = None) -> str:
    """Generate a unique slug for a dataset."""
    base_slug = slugify(name, max_length=50)
    if not base_slug:
        base_slug = "dataset"

    slug = base_slug
    counter = 1

    while True:
        existing = db.query(Dataset).filter(Dataset.slug == slug).first()
        if not existing or (existing_slug and existing.slug == existing_slug):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def infer_column_type(values: list[Any]) -> str:
    """Infer column type from sample values."""
    # Filter out None values
    non_null = [v for v in values if v is not None and v != ""]

    if not non_null:
        return "string"

    # Check if all values are numbers
    all_numbers = True
    for v in non_null[:100]:  # Check first 100 values
        if isinstance(v, bool):
            return "boolean"
        if not isinstance(v, int | float):
            try:
                float(v)
            except (ValueError, TypeError):
                all_numbers = False
                break

    if all_numbers:
        return "number"

    return "string"


def parse_csv_data(content: str) -> tuple[list[dict[str, Any]], list[ColumnInfo]]:
    """Parse CSV content into data rows and column info."""
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        return [], []

    # Get column names
    column_names = list(rows[0].keys()) if rows else []

    # Infer column types and get sample values
    columns = []
    for name in column_names:
        values = [row.get(name) for row in rows]
        col_type = infer_column_type(values)
        sample = values[:5]
        columns.append(ColumnInfo(name=name, type=col_type, sample_values=sample))

    # Convert numeric values
    import contextlib

    for row in rows:
        for col in columns:
            if col.type == "number" and row.get(col.name):
                with contextlib.suppress(ValueError, TypeError):
                    row[col.name] = float(row[col.name])

    return rows, columns


def parse_json_data(content: str) -> tuple[list[dict[str, Any]], list[ColumnInfo]]:
    """Parse JSON content into data rows and column info."""
    data = json.loads(content)

    # Handle array of objects
    if isinstance(data, list) and data and isinstance(data[0], dict):
        rows = data
    # Handle object with data key
    elif isinstance(data, dict) and "data" in data:
        rows = data["data"]
    else:
        raise ValueError("JSON must be an array of objects or have a 'data' key")

    if not rows:
        return [], []

    # Get column names from first row
    column_names = list(rows[0].keys())

    # Infer column types
    columns = []
    for name in column_names:
        values = [row.get(name) for row in rows]
        col_type = infer_column_type(values)
        sample = values[:5]
        columns.append(ColumnInfo(name=name, type=col_type, sample_values=sample))

    return rows, columns


@router.get("", response_model=DatasetList)
async def list_datasets(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """List all datasets with pagination."""
    query = db.query(Dataset)

    if search:
        query = query.filter(
            or_(
                Dataset.name.ilike(f"%{search}%"),
                Dataset.description.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    datasets = (
        query.order_by(Dataset.updated_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return DatasetList(
        datasets=[
            DatasetResponse(
                id=d.id,
                slug=d.slug,
                name=d.name,
                description=d.description,
                data_type=d.data_type,
                data=d.data or [],
                columns=[ColumnInfo(**c) for c in (d.columns or [])],
                row_count=d.row_count,
                source_file=d.source_file or "",
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in datasets
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    dataset_in: DatasetCreate,
    db: Session = Depends(get_db),
):
    """Create a new dataset."""
    slug = dataset_in.slug or generate_unique_slug(db, dataset_in.name)

    dataset = Dataset(
        slug=slug,
        name=dataset_in.name,
        description=dataset_in.description,
        data_type=dataset_in.data_type,
        data=dataset_in.data,
        columns=[c.model_dump() for c in dataset_in.columns],
        row_count=len(dataset_in.data),
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        slug=dataset.slug,
        name=dataset.name,
        description=dataset.description,
        data_type=dataset.data_type,
        data=dataset.data or [],
        columns=[ColumnInfo(**c) for c in (dataset.columns or [])],
        row_count=dataset.row_count,
        source_file=dataset.source_file or "",
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = None,
    db: Session = Depends(get_db),
):
    """Upload a CSV or JSON file as a dataset."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    content_str = content.decode("utf-8")

    # Determine file type
    filename_lower = file.filename.lower()
    if filename_lower.endswith(".csv"):
        data_type = "csv"
        rows, columns = parse_csv_data(content_str)
    elif filename_lower.endswith(".json"):
        data_type = "json"
        try:
            rows, columns = parse_json_data(content_str)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}") from None
    else:
        raise HTTPException(status_code=400, detail="File must be CSV or JSON")

    dataset_name = name or file.filename.rsplit(".", 1)[0]
    slug = generate_unique_slug(db, dataset_name)

    dataset = Dataset(
        slug=slug,
        name=dataset_name,
        data_type=data_type,
        data=rows,
        columns=[c.model_dump() for c in columns],
        row_count=len(rows),
        source_file=file.filename,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        slug=dataset.slug,
        name=dataset.name,
        description=dataset.description or "",
        data_type=dataset.data_type,
        data=dataset.data or [],
        columns=[ColumnInfo(**c) for c in (dataset.columns or [])],
        row_count=dataset.row_count,
        source_file=dataset.source_file or "",
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.get("/{slug}", response_model=DatasetResponse)
async def get_dataset(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a dataset by slug."""
    dataset = db.query(Dataset).filter(Dataset.slug == slug).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetResponse(
        id=dataset.id,
        slug=dataset.slug,
        name=dataset.name,
        description=dataset.description or "",
        data_type=dataset.data_type,
        data=dataset.data or [],
        columns=[ColumnInfo(**c) for c in (dataset.columns or [])],
        row_count=dataset.row_count,
        source_file=dataset.source_file or "",
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.get("/{slug}/summary", response_model=DatasetSummary)
async def get_dataset_summary(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get dataset summary without full data."""
    dataset = db.query(Dataset).filter(Dataset.slug == slug).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetSummary(
        id=dataset.id,
        slug=dataset.slug,
        name=dataset.name,
        description=dataset.description or "",
        data_type=dataset.data_type,
        row_count=dataset.row_count,
        columns=[ColumnInfo(**c) for c in (dataset.columns or [])],
        created_at=dataset.created_at,
    )


@router.put("/{slug}", response_model=DatasetResponse)
async def update_dataset(
    slug: str,
    dataset_in: DatasetUpdate,
    db: Session = Depends(get_db),
):
    """Update a dataset."""
    dataset = db.query(Dataset).filter(Dataset.slug == slug).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    update_data = dataset_in.model_dump(exclude_unset=True)

    if "columns" in update_data:
        update_data["columns"] = [c.model_dump() for c in update_data["columns"]]

    if "data" in update_data:
        update_data["row_count"] = len(update_data["data"])

    for field, value in update_data.items():
        setattr(dataset, field, value)

    db.commit()
    db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        slug=dataset.slug,
        name=dataset.name,
        description=dataset.description or "",
        data_type=dataset.data_type,
        data=dataset.data or [],
        columns=[ColumnInfo(**c) for c in (dataset.columns or [])],
        row_count=dataset.row_count,
        source_file=dataset.source_file or "",
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.delete("/{slug}", status_code=204)
async def delete_dataset(
    slug: str,
    db: Session = Depends(get_db),
):
    """Delete a dataset."""
    dataset = db.query(Dataset).filter(Dataset.slug == slug).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db.delete(dataset)
    db.commit()
