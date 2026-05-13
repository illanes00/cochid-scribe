"""LLM-based spot-check QA: 10% sample of edits + 100% of structural + low-confidence.

Uses Claude CLI to evaluate edit quality on:
- correctness vs source comment
- benja alignment
- replacement_text quality
"""

from __future__ import annotations

import json
import logging
import random
from typing import Any

from app.services.review_critic.io.state import load_stage
from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    ReplyEntry,
)

_log = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un editor crítico evaluando la calidad de ediciones propuestas para un informe de política pública.

Para cada edit te doy:
- comment_id (origen del cambio)
- comment_text (lo que pidió el reviewer)
- scope (local/consistent/structural)
- original_text (texto a reemplazar)
- replacement_text (texto nuevo)
- rationale (justificación)

Evalúa scoring 0-5:
- edit_quality: ¿el cambio hace lo que el comentario pide?
- benja_alignment: ¿técnico SI, prescriptivo NO?
- coherence: ¿el replacement fluye con el contexto?

Output:
[
  {
    "edit_id": "E-CIF1",
    "edit_quality": 4,
    "benja_alignment": 5,
    "coherence": 4,
    "issues": ["lista de issues si hay"],
    "should_block": false,
    "should_revise": false
  }
]

REGLAS:
- Cualquier score < 3 → flag para revisión
- "se debe", "proponemos crear", "es necesario" → benja_alignment penalizado
- Replacement que no aborda el comentario → edit_quality bajo
- Replacement que rompe la oración → coherence bajo

Responde SOLO JSON array."""


def select_sample(edits: list[EditPatch]) -> list[EditPatch]:
    """10% random sample + all structural + all low-confidence."""
    structural = [e for e in edits if e.scope == "structural"]
    low_conf = [e for e in edits if e.confidence < 0.6 and e.scope != "structural"]
    others = [e for e in edits if e.scope != "structural" and e.confidence >= 0.6]

    sample_size = max(5, len(others) // 10)
    random.seed(42)
    sampled_others = random.sample(others, min(sample_size, len(others)))

    selected = list(set(structural + low_conf + sampled_others))
    return selected


def spot_check(
    edits: list[EditPatch],
    classified_by_id: dict[str, ClassifiedComment],
) -> dict[str, dict]:
    """Run LLM spot-check on selected edits."""
    selected = select_sample(edits)
    if not selected:
        return {}

    items = []
    for e in selected:
        cids = e.source_comment_ids
        primary_comment = classified_by_id.get(cids[0]) if cids else None
        items.append(
            {
                "edit_id": e.edit_id,
                "comment_id": cids[0] if cids else "",
                "comment_text": (
                    primary_comment.comment_text[:300]
                    if primary_comment
                    else ""
                ),
                "scope": e.scope,
                "original_text": e.original_text[:200] or e.find_pattern or "",
                "replacement_text": e.replacement_text[:300] or e.replace_with or "",
                "rationale": e.rationale[:200],
            }
        )

    user_content = (
        f"EVALUAR {len(items)} EDITS:\n\n"
        f"{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
        "Devuelve scores y flags por cada uno. JSON array."
    )

    try:
        response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=180)
        raw = extract_json_array(response)
        return {r["edit_id"]: r for r in raw}
    except Exception as e:
        _log.warning("LLM spotcheck failed: %s", e)
        return {}


def run() -> dict[str, dict]:
    edits = load_stage("50_edit_patches.json", EditPatch)
    classified = load_stage("10_classified.json", ClassifiedComment)
    classified_by_id = {c.id: c for c in classified}
    return spot_check(edits, classified_by_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    results = run()
    print(f"Spot-checked {len(results)} edits")
    blocked = [k for k, v in results.items() if v.get("should_block")]
    revise = [k for k, v in results.items() if v.get("should_revise")]
    print(f"Blocked: {len(blocked)}, Revise: {len(revise)}")
    for eid, r in list(results.items())[:5]:
        print(f"  {eid}: quality={r.get('edit_quality')}, benja={r.get('benja_alignment')}, coherence={r.get('coherence')}")
