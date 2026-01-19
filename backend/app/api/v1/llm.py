"""LLM API endpoints for AI-assisted writing."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.services.claim_positions import find_claim_offsets

router = APIRouter()
settings = get_settings()


class RewriteRequest(BaseModel):
    """Request for text rewriting."""

    text: str
    instruction: str
    tone: str = "academic"


class RewriteResponse(BaseModel):
    """Response from text rewriting."""

    original: str
    rewritten: str


class ExtractClaimsRequest(BaseModel):
    """Request for claim extraction."""

    text: str


class ExtractClaimsResponse(BaseModel):
    """Response from claim extraction."""

    claims: list[dict]


class HedgingRequest(BaseModel):
    """Request for hedging improvement."""

    text: str


class HedgingResponse(BaseModel):
    """Response from hedging improvement."""

    original: str
    improved: str
    changes: list[str]


class SummarizeRequest(BaseModel):
    """Request for document summarization."""

    text: str
    target_words: int = 6000
    preserve_data: bool = True
    preserve_citations: bool = True
    language: str = "es"


class SummarizeResponse(BaseModel):
    """Response from document summarization."""

    original_word_count: int
    summary: str
    summary_word_count: int
    preserved_data_points: list[str]
    sections_covered: list[str]


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_text(request: RewriteRequest):
    """Rewrite text with AI assistance."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        system_prompt = """You are an academic writing assistant. Rewrite the given text following the instruction while maintaining academic rigor and clarity. Return only the rewritten text without any explanation."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Instruction: {request.instruction}\n\nTone: {request.tone}\n\nText to rewrite:\n{request.text}",
                }
            ],
        )

        rewritten = message.content[0].text

        return RewriteResponse(original=request.text, rewritten=rewritten)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}") from None


def extract_claims_from_text(text: str) -> list[dict]:
    """Extract claims from text using the LLM."""
    import json

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    system_prompt = """You are an academic writing assistant. Extract all verifiable claims from the given text. For each claim, identify:
- claim_text: The exact claim
- claim_type: DATA (quantitative), LITERATURE (from citations), MIXED, or HYPOTHESIS
- evidence_needed: What evidence would verify this claim

Return as JSON array."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Extract claims from this text:\n\n{text}",
            }
        ],
    )

    response_text = message.content[0].text

    try:
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start >= 0 and end > start:  # noqa: SIM108
            return json.loads(response_text[start:end])
    except json.JSONDecodeError:
        return []

    return []


@router.post("/extract-claims-document/{slug}")
async def extract_claims_for_document(
    slug: str,
    db: Session = Depends(get_db),
):
    """Extract claims for an entire document and persist them."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = doc.markdown or (doc.content.get("html") if isinstance(doc.content, dict) else "") or ""
    claims = extract_claims_from_text(text)

    import uuid

    existing_texts = {
        row[0] for row in db.query(Claim.claim_text).filter(Claim.document_id == doc.id).all()
    }
    created = []
    for claim in claims:
        claim_text = str(claim.get("claim_text") or claim.get("text") or "").strip()
        if not claim_text or claim_text in existing_texts:
            continue
        start_offset, end_offset = find_claim_offsets(text, claim_text)
        claim_type = str(claim.get("claim_type") or claim.get("type") or "MIXED").upper()
        evidence_needed = claim.get("evidence_needed")
        evidence = (
            [{"kind": "OBSERVATION", "ref": "LLM", "notes": str(evidence_needed)}]
            if evidence_needed
            else []
        )
        claim_obj = Claim(
            claim_id=f"C-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            document_id=doc.id,
            claim_text=claim_text,
            claim_type=claim_type,
            start_offset=start_offset,
            end_offset=end_offset,
            section=str(claim.get("section") or "").strip() or None,
            evidence=evidence,
            source_sentences=[],
        )
        db.add(claim_obj)
        created.append(claim_obj)
        existing_texts.add(claim_text)

    db.commit()

    return {"created": len(created)}


@router.post("/extract-claims", response_model=ExtractClaimsResponse)
async def extract_claims(request: ExtractClaimsRequest):
    """Extract claims from text."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    try:
        claims = extract_claims_from_text(request.text)
        return ExtractClaimsResponse(claims=claims)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}") from None


@router.post("/improve-hedging", response_model=HedgingResponse)
async def improve_hedging(request: HedgingRequest):
    """Improve hedging in academic text."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        system_prompt = """You are an academic writing assistant specializing in hedging. Improve the hedging in the given text by:
1. Replacing absolute statements with tentative language (may, might, appears to, suggests)
2. Adding qualifiers where appropriate (generally, typically, often)
3. Using passive voice for claims without direct evidence

Return the improved text followed by a list of changes made, separated by "---CHANGES---"."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Improve hedging in this text:\n\n{request.text}",
                }
            ],
        )

        response = message.content[0].text

        # Parse response
        if "---CHANGES---" in response:
            parts = response.split("---CHANGES---")
            improved = parts[0].strip()
            changes = [c.strip() for c in parts[1].strip().split("\n") if c.strip()]
        else:
            improved = response.strip()
            changes = []

        return HedgingResponse(original=request.text, improved=improved, changes=changes)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}") from None


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(request: SummarizeRequest):
    """Summarize a document while preserving factual content."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    try:
        import re

        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Count original words
        original_word_count = len(request.text.split())

        # Extract data points (numbers, percentages, currency)
        data_pattern = r"[\d,.]+\s*(?:%|USD|US\$|\$|millones|billones|mil)"
        data_points = list(set(re.findall(data_pattern, request.text)))

        # Extract section headers
        section_pattern = r"^(?:\d+\.[\d.]*\s+)?([A-Z][^.:\n]+)"
        sections = re.findall(section_pattern, request.text, re.MULTILINE)[:20]

        # Build the summarization prompt
        lang_instruction = "en español" if request.language == "es" else "in English"

        system_prompt = f"""Eres un editor académico experto en policy briefs y documentos de política pública.

TU TAREA: Resumir este documento a aproximadamente {request.target_words} palabras, {lang_instruction}.

REGLAS ESTRICTAS DE PRESERVACIÓN FACTUAL:
1. NUNCA omitas cifras, porcentajes, montos o datos cuantitativos
2. MANTÉN todas las citas y referencias (Autor, año) o [número]
3. PRESERVA los hallazgos principales con su evidencia numérica
4. INCLUYE las recomendaciones de política con sus implicaciones fiscales
5. Condensa SOLO el texto explicativo, contexto histórico y ejemplos redundantes

ESTRUCTURA DEL RESUMEN:
- Resumen ejecutivo (breve)
- Diagnóstico y problema
- Hallazgos clave (con datos)
- Comparación internacional (datos relevantes)
- Recomendaciones y escenarios
- Implicaciones fiscales

FORMATO:
- Usa encabezados claros (##)
- Mantén tablas si son esenciales
- Preserva listas con viñetas para datos clave

El documento original tiene {original_word_count:,} palabras.
Debes producir ~{request.target_words:,} palabras (±10%)."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Resume el siguiente documento preservando toda la información factual:\n\n{request.text}",
                }
            ],
        )

        summary = message.content[0].text
        summary_word_count = len(summary.split())

        return SummarizeResponse(
            original_word_count=original_word_count,
            summary=summary,
            summary_word_count=summary_word_count,
            preserved_data_points=data_points[:50],
            sections_covered=sections,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}") from None
