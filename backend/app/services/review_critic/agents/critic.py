"""Stage 3: Critic — per-comment evaluation.

Takes a classified comment + ledger + doc context, produces CriticJudgment.
Batched in groups of 10-15 comments for efficiency.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.review_critic.io.state import (
    save_stage,
    load_stage,
    hash_file,
)
from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.schemas import (
    ClassifiedComment,
    CriticJudgment,
)

_log = logging.getLogger(__name__)

DOC_FILE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/informe-final-text.md")
BATCH_SIZE = 10

SYSTEM_PROMPT = """Eres un editor critico senior con experiencia en politica publica chilena (medicamentos en planes de salud).

Tu tarea: para CADA comentario te doy: classification + texto del comentario + texto citado + verification ledger + contexto de seccion.

Para CADA uno generas un JSON con:

{
  "comment_id": "C-CIF1",
  "recommendation": "ACCEPT|ACCEPT_PARTIAL|REJECT|DEFER|NEEDS_DATA",
  "reasoning": "2-4 oraciones justificando la decision",
  "improvement_score": 0-5 (cuanto mejora el doc si se acepta),
  "preference_score": 0-5 (cuanto es solo gusto vs sustantivo),
  "benja_alignment": 0-5 (alinea con 'profundidad tecnica SI, casarnos con politica NO'),
  "correctness_score": 0-5 (si factual, que tan correcto es el reviewer 0=incorrecto 5=totalmente correcto),
  "conflicts_with": ["C-EU2"],
  "supports": ["C-CC15"],
  "verification_refs": ["V-ges-patologias"],
  "proposed_action": "apply_local_edit|apply_consistent_edit|restructure_section|add_content|delete_content|none_reply_only",
  "requires_director_approval": false
}

REGLAS DURAS (no LLM, deterministicas — sigue):

1. **factual + verification=confirmed (reviewer correcto)** → ACCEPT, apply_local_edit
2. **factual + verification=refuted (reviewer incorrecto)** → REJECT, none_reply_only (defender con evidencia)
3. **factual + verification=inconclusive** → DEFER (con propuesta tentativa) o ACCEPT_PARTIAL
4. **factual + verification=needs_data** → NEEDS_DATA
5. **stylistic + style_consistency_hint=consistent_rule** → ACCEPT, apply_consistent_edit
6. **stylistic + style_consistency_hint=local_substitution** → ACCEPT, apply_local_edit
7. **structural pequeno (<500 chars cambio estimado)** → ACCEPT, restructure_section
8. **structural grande (>500 chars)** → DEFER pero requires_director_approval=true (sugerir mejor opcion en reply)
9. **strategic (Eduardo 'menos prescriptivo')** → ACCEPT_PARTIAL con softening, benja_alignment alta
10. **methodological (CIF 'explicar seleccion')** → ACCEPT, add_content
11. **question (Carla '?')** → none_reply_only (responder en reply, no editar)
12. **general (CIF 'borrador avanzado')** → none_reply_only + reply apuntando a fixes especificos

LINEA EDITORIAL DE BENJA (ARBITRO):
"Profundidad tecnica SI, casarnos con politica NO. Someter a discusion en el evento."
- Aceptar contenido factual/tecnico (DAC, judicializacion, biosimilares != genericos)
- Suavizar prescripciones (sin "se debe", "proponemos como solucion")
- Preferir "alternativas/opciones/trade-offs/preguntas a discutir"

CONFLICTOS:
- CIF (mas detalle) vs Eduardo+Carla (menos prescriptivo) → NO siempre conflicto real
- DAC factual no es prescripcion (CIF tiene razon agregar)
- BFAU como solucion = SI prescriptivo (Eduardo tiene razon suavizar)

DEFER por defecto significa: el reviewer toca un punto valido pero la solucion exacta no es trivial → en el reply propones tu mejor opcion + flagueas para directores

Responde SOLO con JSON array. NO prosa fuera del JSON."""


def load_classified() -> list[ClassifiedComment]:
    return load_stage("10_classified.json", ClassifiedComment)


def build_doc_context() -> str:
    """Load doc text, truncated for LLM."""
    if not DOC_FILE.exists():
        return ""
    text = DOC_FILE.read_text()
    return text[:60000]  # ~15K tokens


def build_ledger_context() -> str:
    """Format ledger as context for Critic."""
    ledger = load_ledger()
    lines = ["FACTS VERIFICADOS (ledger):"]
    for f in ledger.facts:
        marker = {
            "confirmed": "[OK]",
            "refuted": "[X]",
            "inconclusive": "[?]",
            "needs_data": "[!]",
        }.get(f.status, "[?]")
        lines.append(f"  {marker} {f.claim_id}: {f.claim_text[:100]}")
        lines.append(f"        evidence: {f.evidence[:200]}")
    return "\n".join(lines)


def critique_batch(
    classified: list[ClassifiedComment],
    doc_context: str,
    ledger_context: str,
) -> list[CriticJudgment]:
    """Critique one batch of classified comments."""
    items_for_llm = []
    for c in classified:
        items_for_llm.append(
            {
                "id": c.id,
                "author": c.author,
                "comment_text": c.comment_text,
                "quoted_text": c.quoted_text or "",
                "section_hint": c.section_hint or "",
                "type": c.type,
                "specificity": c.specificity,
                "verifiability": c.verifiability,
                "raw_claims": c.raw_claims,
                "style_consistency_hint": c.style_consistency_hint,
            }
        )

    user_content = (
        f"DOCUMENTO (extracto):\n{doc_context}\n\n---\n\n"
        f"{ledger_context}\n\n---\n\n"
        f"COMENTARIOS A EVALUAR ({len(items_for_llm)}):\n\n"
        f"{json.dumps(items_for_llm, ensure_ascii=False, indent=1)}\n\n"
        f"Genera CriticJudgment para CADA uno de los {len(items_for_llm)} comentarios. "
        "Responde SOLO con JSON array."
    )

    _log.info("Critic: calling Claude CLI for batch of %d", len(classified))
    response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=420)

    raw = extract_json_array(response)
    by_id = {item["comment_id"]: item for item in raw}

    results: list[CriticJudgment] = []
    for c in classified:
        item = by_id.get(c.id)
        if item is None:
            _log.warning("Critic: missing judgment for %s — defaulting", c.id)
            item = {
                "comment_id": c.id,
                "recommendation": "DEFER",
                "reasoning": "AI did not return judgment for this comment.",
                "improvement_score": 0,
                "preference_score": 0,
                "benja_alignment": 3,
                "correctness_score": 0,
                "conflicts_with": [],
                "supports": [],
                "verification_refs": [],
                "proposed_action": "none_reply_only",
                "requires_director_approval": True,
            }
        try:
            results.append(
                CriticJudgment(
                    comment_id=item["comment_id"],
                    recommendation=item.get("recommendation", "DEFER"),
                    reasoning=item.get("reasoning", ""),
                    improvement_score=int(item.get("improvement_score", 3)),
                    preference_score=int(item.get("preference_score", 3)),
                    benja_alignment=int(item.get("benja_alignment", 3)),
                    correctness_score=int(item.get("correctness_score", 3)),
                    conflicts_with=item.get("conflicts_with", []) or [],
                    supports=item.get("supports", []) or [],
                    verification_refs=item.get("verification_refs", []) or [],
                    proposed_action=item.get("proposed_action", "none_reply_only"),
                    requires_director_approval=bool(
                        item.get("requires_director_approval", False)
                    ),
                )
            )
        except Exception as e:
            _log.warning("Critic: parse error for %s: %s", c.id, e)
            results.append(
                CriticJudgment(
                    comment_id=c.id,
                    recommendation="DEFER",
                    reasoning=f"Parse error: {e}",
                    improvement_score=0,
                    preference_score=0,
                    benja_alignment=3,
                    correctness_score=0,
                    proposed_action="none_reply_only",
                    requires_director_approval=True,
                )
            )

    return results


def run() -> Path:
    """Run the Critic on all classified comments in batches."""
    classified = load_classified()
    doc_context = build_doc_context()
    ledger_context = build_ledger_context()

    print(f"Critic: {len(classified)} comments in batches of {BATCH_SIZE}")

    all_judgments: list[CriticJudgment] = []
    for i in range(0, len(classified), BATCH_SIZE):
        batch = classified[i : i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}: comments {i + 1}-{i + len(batch)}")
        batch_judgments = critique_batch(batch, doc_context, ledger_context)
        all_judgments.extend(batch_judgments)

    # Stats
    from collections import Counter

    rec_counts = Counter(j.recommendation for j in all_judgments)
    print(f"\n=== Judgments: {len(all_judgments)} ===")
    print(f"Recommendations: {dict(rec_counts)}")

    path = save_stage(
        "30_critic_judgments.json",
        all_judgments,
        input_hashes={"10_classified": "from_load_stage"},
    )
    print(f"\nSaved → {path}")
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
