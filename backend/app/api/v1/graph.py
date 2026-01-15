"""Graph API endpoints for Knowledge Base visualization."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.document import Document
from app.models.note import Link, Note
from app.schemas.note import GraphEdge, GraphNode, GraphResponse

router = APIRouter()


@router.get("", response_model=GraphResponse)
async def get_full_graph(
    include_documents: bool = Query(True),
    include_claims: bool = Query(False),
    include_bib: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get the full knowledge graph for visualization."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()

    # Add notes
    notes = db.query(Note).all()
    for note in notes:
        nodes.append(
            GraphNode(
                id=note.id,
                type="note",
                label=note.title,
                metadata={
                    "slug": note.slug,
                    "note_type": note.note_type,
                    "tags": note.tags or [],
                },
            )
        )
        node_ids.add(note.id)

    # Add documents
    if include_documents:
        documents = db.query(Document).all()
        for doc in documents:
            nodes.append(
                GraphNode(
                    id=doc.id,
                    type="document",
                    label=doc.title,
                    metadata={
                        "slug": doc.slug,
                        "doc_type": doc.doc_type,
                        "status": doc.status,
                    },
                )
            )
            node_ids.add(doc.id)

    # Add claims
    if include_claims:
        claims = db.query(Claim).all()
        for claim in claims:
            # Truncate claim text for label
            label = claim.claim_text[:50] + "..." if len(claim.claim_text) > 50 else claim.claim_text
            nodes.append(
                GraphNode(
                    id=claim.id,
                    type="claim",
                    label=label,
                    metadata={
                        "claim_id": claim.claim_id,
                        "claim_type": claim.claim_type,
                        "status": claim.status,
                    },
                )
            )
            node_ids.add(claim.id)

            # Add edge from document to claim
            if claim.document_id and claim.document_id in node_ids:
                edges.append(
                    GraphEdge(
                        source=claim.document_id,
                        target=claim.id,
                        type="contains",
                    )
                )

    # Add bibliography entries
    if include_bib:
        bib_entries = db.query(BibliographyEntry).all()
        for entry in bib_entries:
            nodes.append(
                GraphNode(
                    id=entry.id,
                    type="bib",
                    label=f"{entry.author.split(',')[0] if entry.author else 'Unknown'} ({entry.year or '?'})",
                    metadata={
                        "bib_key": entry.bib_key,
                        "title": entry.title,
                        "year": entry.year,
                    },
                )
            )
            node_ids.add(entry.id)

    # Add links as edges
    links = db.query(Link).all()
    for link in links:
        # Only add edge if both nodes exist in graph
        if link.source_id in node_ids and link.target_id in node_ids:
            edges.append(
                GraphEdge(
                    source=link.source_id,
                    target=link.target_id,
                    type=link.link_type,
                )
            )

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/local/{entity_type}/{entity_id}", response_model=GraphResponse)
async def get_local_graph(
    entity_type: str,
    entity_id: str,
    depth: int = Query(1, ge=1, le=3),
    db: Session = Depends(get_db),
):
    """Get the local graph around a specific entity (neighbors)."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()

    # Find the central entity
    center_node = None

    if entity_type == "note":
        note = db.query(Note).filter(Note.id == entity_id).first()
        if note:
            center_node = GraphNode(
                id=note.id,
                type="note",
                label=note.title,
                metadata={"slug": note.slug, "note_type": note.note_type},
            )
    elif entity_type == "document":
        doc = db.query(Document).filter(Document.id == entity_id).first()
        if doc:
            center_node = GraphNode(
                id=doc.id,
                type="document",
                label=doc.title,
                metadata={"slug": doc.slug, "doc_type": doc.doc_type},
            )
    elif entity_type == "bib":
        entry = db.query(BibliographyEntry).filter(BibliographyEntry.id == entity_id).first()
        if entry:
            center_node = GraphNode(
                id=entry.id,
                type="bib",
                label=f"{entry.author.split(',')[0] if entry.author else 'Unknown'} ({entry.year or '?'})",
                metadata={"bib_key": entry.bib_key, "title": entry.title},
            )

    if not center_node:
        return GraphResponse(nodes=[], edges=[])

    nodes.append(center_node)
    node_ids.add(center_node.id)

    # BFS to find neighbors
    current_level = {entity_id}

    for _ in range(depth):
        next_level: set[str] = set()

        # Find outgoing links
        outgoing = (
            db.query(Link)
            .filter(Link.source_id.in_(current_level))
            .all()
        )

        # Find incoming links
        incoming = (
            db.query(Link)
            .filter(Link.target_id.in_(current_level))
            .all()
        )

        for link in outgoing + incoming:
            # Determine the neighbor
            neighbor_id = link.target_id if link.source_id in current_level else link.source_id
            neighbor_type = link.target_type if link.source_id in current_level else link.source_type

            if neighbor_id not in node_ids:
                # Fetch the neighbor entity
                neighbor_node = None

                if neighbor_type == "note":
                    note = db.query(Note).filter(Note.id == neighbor_id).first()
                    if note:
                        neighbor_node = GraphNode(
                            id=note.id,
                            type="note",
                            label=note.title,
                            metadata={"slug": note.slug},
                        )
                elif neighbor_type == "document":
                    doc = db.query(Document).filter(Document.id == neighbor_id).first()
                    if doc:
                        neighbor_node = GraphNode(
                            id=doc.id,
                            type="document",
                            label=doc.title,
                            metadata={"slug": doc.slug},
                        )
                elif neighbor_type == "bib":
                    entry = db.query(BibliographyEntry).filter(BibliographyEntry.id == neighbor_id).first()
                    if entry:
                        neighbor_node = GraphNode(
                            id=entry.id,
                            type="bib",
                            label=f"{entry.bib_key}",
                            metadata={"title": entry.title},
                        )

                if neighbor_node:
                    nodes.append(neighbor_node)
                    node_ids.add(neighbor_id)
                    next_level.add(neighbor_id)

            # Add the edge
            edges.append(
                GraphEdge(
                    source=link.source_id,
                    target=link.target_id,
                    type=link.link_type,
                )
            )

        current_level = next_level

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/search", response_model=GraphResponse)
async def search_graph(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Search the knowledge graph by text."""
    nodes: list[GraphNode] = []
    node_ids: set[str] = set()

    # Search notes
    notes = (
        db.query(Note)
        .filter(Note.title.ilike(f"%{query}%"))
        .limit(20)
        .all()
    )
    for note in notes:
        nodes.append(
            GraphNode(
                id=note.id,
                type="note",
                label=note.title,
                metadata={"slug": note.slug},
            )
        )
        node_ids.add(note.id)

    # Search documents
    documents = (
        db.query(Document)
        .filter(Document.title.ilike(f"%{query}%"))
        .limit(20)
        .all()
    )
    for doc in documents:
        nodes.append(
            GraphNode(
                id=doc.id,
                type="document",
                label=doc.title,
                metadata={"slug": doc.slug},
            )
        )
        node_ids.add(doc.id)

    # Search bibliography
    bib_entries = (
        db.query(BibliographyEntry)
        .filter(
            BibliographyEntry.title.ilike(f"%{query}%")
            | BibliographyEntry.author.ilike(f"%{query}%")
        )
        .limit(20)
        .all()
    )
    for entry in bib_entries:
        nodes.append(
            GraphNode(
                id=entry.id,
                type="bib",
                label=f"{entry.bib_key}",
                metadata={"title": entry.title, "author": entry.author},
            )
        )
        node_ids.add(entry.id)

    # Find edges between found nodes
    edges: list[GraphEdge] = []
    if node_ids:
        links = (
            db.query(Link)
            .filter(
                Link.source_id.in_(node_ids),
                Link.target_id.in_(node_ids),
            )
            .all()
        )
        for link in links:
            edges.append(
                GraphEdge(
                    source=link.source_id,
                    target=link.target_id,
                    type=link.link_type,
                )
            )

    return GraphResponse(nodes=nodes, edges=edges)
