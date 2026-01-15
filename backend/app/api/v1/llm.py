"""LLM API endpoints for AI-assisted writing."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

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


@router.post("/extract-claims", response_model=ExtractClaimsResponse)
async def extract_claims(request: ExtractClaimsRequest):
    """Extract claims from text."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="LLM service not configured")

    try:
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
                    "content": f"Extract claims from this text:\n\n{request.text}",
                }
            ],
        )

        response_text = message.content[0].text

        # Try to parse JSON from response
        try:
            # Find JSON array in response
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start >= 0 and end > start:  # noqa: SIM108
                claims = json.loads(response_text[start:end])
            else:
                claims = []
        except json.JSONDecodeError:
            claims = []

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
