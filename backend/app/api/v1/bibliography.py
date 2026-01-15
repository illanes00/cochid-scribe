"""Bibliography API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.bibliography import BibliographyEntry
from app.schemas.bibliography import BibEntryCreate, BibEntryResponse

router = APIRouter()


@router.get("", response_model=list[BibEntryResponse])
async def list_bibliography(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List bibliography entries."""
    entries = (
        db.query(BibliographyEntry)
        .order_by(BibliographyEntry.bib_key)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries


@router.post("", response_model=BibEntryResponse, status_code=201)
async def create_bibliography_entry(
    data: BibEntryCreate,
    db: Session = Depends(get_db),
):
    """Create a bibliography entry."""
    # Check if key exists
    existing = (
        db.query(BibliographyEntry)
        .filter(BibliographyEntry.bib_key == data.bib_key)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Bibliography key already exists")

    entry = BibliographyEntry(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry


@router.get("/search", response_model=list[BibEntryResponse])
async def search_bibliography(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search bibliography entries by title, author, or key."""
    search_term = f"%{q}%"
    entries = (
        db.query(BibliographyEntry)
        .filter(
            (BibliographyEntry.title.ilike(search_term))
            | (BibliographyEntry.author.ilike(search_term))
            | (BibliographyEntry.bib_key.ilike(search_term))
        )
        .limit(limit)
        .all()
    )
    return entries


@router.get("/{bib_key}", response_model=BibEntryResponse)
async def get_bibliography_entry(
    bib_key: str,
    db: Session = Depends(get_db),
):
    """Get a bibliography entry by key."""
    entry = (
        db.query(BibliographyEntry)
        .filter(BibliographyEntry.bib_key == bib_key)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Bibliography entry not found")

    return entry


@router.delete("/{bib_key}", status_code=204)
async def delete_bibliography_entry(
    bib_key: str,
    db: Session = Depends(get_db),
):
    """Delete a bibliography entry."""
    entry = (
        db.query(BibliographyEntry)
        .filter(BibliographyEntry.bib_key == bib_key)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Bibliography entry not found")

    db.delete(entry)
    db.commit()


@router.post("/import", response_model=list[BibEntryResponse], status_code=201)
async def import_bibtex(
    bibtex_content: str,
    db: Session = Depends(get_db),
):
    """Import bibliography entries from BibTeX string."""
    import bibtexparser

    try:
        bib_database = bibtexparser.loads(bibtex_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid BibTeX: {str(e)}") from None

    created_entries = []

    for bib_entry in bib_database.entries:
        bib_key = bib_entry.get("ID", "")
        if not bib_key:
            continue

        # Check if exists
        existing = (
            db.query(BibliographyEntry)
            .filter(BibliographyEntry.bib_key == bib_key)
            .first()
        )
        if existing:
            continue

        entry = BibliographyEntry(
            bib_key=bib_key,
            entry_type=bib_entry.get("ENTRYTYPE", "misc"),
            title=bib_entry.get("title", ""),
            author=bib_entry.get("author", ""),
            year=int(bib_entry.get("year", 0)) if bib_entry.get("year") else None,
            journal=bib_entry.get("journal"),
            booktitle=bib_entry.get("booktitle"),
            volume=bib_entry.get("volume"),
            number=bib_entry.get("number"),
            pages=bib_entry.get("pages"),
            publisher=bib_entry.get("publisher"),
            doi=bib_entry.get("doi"),
            url=bib_entry.get("url"),
            abstract=bib_entry.get("abstract"),
            bibtex=bibtexparser.dumps(
                bibtexparser.bibdatabase.BibDatabase(entries=[bib_entry])
            ),
        )
        db.add(entry)
        created_entries.append(entry)

    db.commit()

    for entry in created_entries:
        db.refresh(entry)

    return created_entries
