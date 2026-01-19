"""Charts API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from slugify import slugify
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Chart
from app.schemas.dataset import (
    ChartConfig,
    ChartCreate,
    ChartList,
    ChartResponse,
    ChartUpdate,
)

router = APIRouter()


def generate_unique_slug(db: Session, title: str, existing_slug: str | None = None) -> str:
    """Generate a unique slug for a chart."""
    base_slug = slugify(title, max_length=50)
    if not base_slug:
        base_slug = "chart"

    slug = base_slug
    counter = 1

    while True:
        existing = db.query(Chart).filter(Chart.slug == slug).first()
        if not existing or (existing_slug and existing.slug == existing_slug):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=ChartList)
async def list_charts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    chart_type: str | None = None,
    db: Session = Depends(get_db),
):
    """List all charts with pagination."""
    query = db.query(Chart)

    if search:
        query = query.filter(Chart.title.ilike(f"%{search}%"))

    if chart_type:
        query = query.filter(Chart.chart_type == chart_type)

    total = query.count()
    charts = (
        query.order_by(Chart.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    )

    return ChartList(
        charts=[
            ChartResponse(
                id=c.id,
                slug=c.slug,
                title=c.title,
                chart_type=c.chart_type,
                dataset_id=c.dataset_id,
                config=ChartConfig(**c.config) if c.config else ChartConfig(),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in charts
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ChartResponse, status_code=201)
async def create_chart(
    chart_in: ChartCreate,
    db: Session = Depends(get_db),
):
    """Create a new chart."""
    slug = chart_in.slug or generate_unique_slug(db, chart_in.title)

    chart = Chart(
        slug=slug,
        title=chart_in.title,
        chart_type=chart_in.chart_type,
        dataset_id=chart_in.dataset_id,
        config=chart_in.config.model_dump(),
    )

    db.add(chart)
    db.commit()
    db.refresh(chart)

    return ChartResponse(
        id=chart.id,
        slug=chart.slug,
        title=chart.title,
        chart_type=chart.chart_type,
        dataset_id=chart.dataset_id,
        config=ChartConfig(**chart.config) if chart.config else ChartConfig(),
        created_at=chart.created_at,
        updated_at=chart.updated_at,
    )


@router.get("/{slug}", response_model=ChartResponse)
async def get_chart(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get a chart by slug."""
    chart = db.query(Chart).filter(Chart.slug == slug).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    return ChartResponse(
        id=chart.id,
        slug=chart.slug,
        title=chart.title,
        chart_type=chart.chart_type,
        dataset_id=chart.dataset_id,
        config=ChartConfig(**chart.config) if chart.config else ChartConfig(),
        created_at=chart.created_at,
        updated_at=chart.updated_at,
    )


@router.put("/{slug}", response_model=ChartResponse)
async def update_chart(
    slug: str,
    chart_in: ChartUpdate,
    db: Session = Depends(get_db),
):
    """Update a chart."""
    chart = db.query(Chart).filter(Chart.slug == slug).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    update_data = chart_in.model_dump(exclude_unset=True)

    if "config" in update_data:
        update_data["config"] = update_data["config"].model_dump()

    for field, value in update_data.items():
        setattr(chart, field, value)

    db.commit()
    db.refresh(chart)

    return ChartResponse(
        id=chart.id,
        slug=chart.slug,
        title=chart.title,
        chart_type=chart.chart_type,
        dataset_id=chart.dataset_id,
        config=ChartConfig(**chart.config) if chart.config else ChartConfig(),
        created_at=chart.created_at,
        updated_at=chart.updated_at,
    )


@router.delete("/{slug}", status_code=204)
async def delete_chart(
    slug: str,
    db: Session = Depends(get_db),
):
    """Delete a chart."""
    chart = db.query(Chart).filter(Chart.slug == slug).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    db.delete(chart)
    db.commit()
