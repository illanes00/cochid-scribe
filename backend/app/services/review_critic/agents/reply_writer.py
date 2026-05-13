"""Stage 6: Reply Writer.

Generates Spanish reply for each comment based on the resolved decision.
Batched for stylistic consistency.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.review_critic.io.state import save_stage, load_stage
from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    ReplyEntry,
    ResolvedDecision,
)

_log = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres Martin Illanes, autor del informe, respondiendo a los comentarios de los revisores en español.

Para cada comentario te doy:
- texto del comentario + autor
- decision final (ACCEPT/ACCEPT_PARTIAL/REJECT/DEFER/NEEDS_DATA)
- razonamiento
- si hay edit aplicado
- requires_director_approval

Generas un reply profesional, conciso (2-4 oraciones) en español:

OUTPUT:
{
  "comment_id": "C-CIF1",
  "reply_text": "el reply en español",
  "decision_label": "ACEPTADO|ACEPTADO_PARCIAL|RECHAZADO|PENDIENTE_DIRECTORES|PENDIENTE_DATOS|RESPUESTA",
  "references_edit_ids": ["E-C-CIF1"]
}

REGLAS DE ESTILO:

1. **ACCEPT**: empezar con "Aceptado." o "De acuerdo." → mencionar el cambio aplicado y donde
   Ej: "Aceptado. Se incorpora DAC al marco institucional (sección 2.4) describiendo operación post-2019."

2. **ACCEPT_PARTIAL** (con director_approval=true): empezar con "Aceptado parcialmente." → propuesta + flag
   Ej: "Propuesta tentativa: agregar nota sobre judicialización (sección 2.3 + cita Vargas-Pelaez 2019). A confirmar con directores."

3. **REJECT**: defender con evidencia del ledger
   Ej: "Discrepamos: el dato 87 patologías GES corresponde al decreto 2022-2025; el decreto 2025-2028 actualiza a 90."

4. **DEFER**: indicar que va a directores
   Ej: "Dependerá de definición editorial: opciones A o B. A confirmar con Eduardo y Carla."

5. **NEEDS_DATA**: indicar que falta verificación
   Ej: "Pendiente: requiere reproducción del cálculo desde EPF + datos de gasto público retail."

6. **none_reply_only / RESPUESTA**: responder la pregunta o aclarar
   Ej: "En FONASA aplicaría tanto en MAI como MLE. La distinción se aborda en sección 7.3 (Diseño operacional)."

NO usar:
- "Gracias por el comentario" (cliché)
- "Tomaremos en cuenta" (vago)
- "Quedo atento" / "Saludos"

SI usar:
- Datos concretos del ledger
- Referencia a sección/párrafo específico cuando aplique
- "Trade-off entre X e Y" cuando hay decisión editorial

Tono: senior, factual, directo. Como entre colegas profesionales.

Responde SOLO con JSON array."""


def derive_label(rec: str, requires_approval: bool, action: str) -> str:
    if action == "none_reply_only":
        return "RESPUESTA"
    if rec == "ACCEPT":
        return "ACEPTADO"
    if rec == "ACCEPT_PARTIAL":
        return "PENDIENTE_DIRECTORES" if requires_approval else "ACEPTADO_PARCIAL"
    if rec == "REJECT":
        return "RECHAZADO"
    if rec == "DEFER":
        return "PENDIENTE_DIRECTORES"
    if rec == "NEEDS_DATA":
        return "PENDIENTE_DATOS"
    return "RESPUESTA"


def write_replies_batch(
    decisions: list[ResolvedDecision],
    classified_by_id: dict[str, ClassifiedComment],
    edits_by_comment: dict[str, list[EditPatch]],
    ledger_summary: str,
) -> list[ReplyEntry]:
    """Generate replies for a batch of decisions."""
    items = []
    for d in decisions:
        c = classified_by_id.get(d.comment_id)
        if not c:
            continue
        edit_ids = [e.edit_id for e in edits_by_comment.get(d.comment_id, [])]
        items.append(
            {
                "comment_id": d.comment_id,
                "author": c.author,
                "comment_text": c.comment_text[:400],
                "comment_type": c.type,
                "decision": d.final_recommendation,
                "action": d.proposed_action,
                "requires_director_approval": d.requires_director_approval,
                "reasoning": d.final_reasoning[:400],
                "applied_edits": edit_ids,
            }
        )

    user_content = (
        f"FACTS LEDGER (referencia para defender o citar):\n{ledger_summary}\n\n---\n\n"
        f"COMENTARIOS A RESPONDER ({len(items)}):\n\n"
        f"{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
        "Genera un reply para CADA uno. JSON array."
    )

    response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=300)
    raw = extract_json_array(response)
    by_id = {r["comment_id"]: r for r in raw}

    results: list[ReplyEntry] = []
    for d in decisions:
        item = by_id.get(d.comment_id)
        edit_ids = [e.edit_id for e in edits_by_comment.get(d.comment_id, [])]

        if item is None:
            # Fallback: generate basic reply
            label = derive_label(d.final_recommendation, d.requires_director_approval, d.proposed_action)
            results.append(
                ReplyEntry(
                    comment_id=d.comment_id,
                    reply_text=f"[{label}] {d.final_reasoning[:300]}",
                    decision_label=label,
                    references_edit_ids=edit_ids,
                )
            )
            continue

        results.append(
            ReplyEntry(
                comment_id=d.comment_id,
                reply_text=item.get("reply_text", "")[:1000],
                decision_label=item.get(
                    "decision_label",
                    derive_label(d.final_recommendation, d.requires_director_approval, d.proposed_action),
                ),
                references_edit_ids=item.get("references_edit_ids", edit_ids) or edit_ids,
            )
        )

    return results


def run() -> Path:
    decisions = load_stage("41_resolved_decisions.json", ResolvedDecision)
    classified = load_stage("10_classified.json", ClassifiedComment)
    edits = load_stage("50_edit_patches.json", EditPatch)

    classified_by_id = {c.id: c for c in classified}
    edits_by_comment: dict[str, list[EditPatch]] = {}
    for e in edits:
        for cid in e.source_comment_ids:
            edits_by_comment.setdefault(cid, []).append(e)

    ledger = load_ledger()
    ledger_summary = "\n".join(
        f"  [{f.status}] {f.claim_id}: {f.claim_text[:80]}" for f in ledger.facts
    )

    BATCH = 12
    print(f"Reply Writer: {len(decisions)} decisions in batches of {BATCH}")

    all_replies: list[ReplyEntry] = []
    for i in range(0, len(decisions), BATCH):
        batch = decisions[i : i + BATCH]
        print(f"  Batch {i // BATCH + 1}: {len(batch)} replies")
        try:
            batch_replies = write_replies_batch(
                batch, classified_by_id, edits_by_comment, ledger_summary
            )
            all_replies.extend(batch_replies)
            save_stage("60_replies.json", all_replies)
            print(f"    -> {len(batch_replies)} replies, total: {len(all_replies)}")
        except Exception as e:
            _log.warning("Batch %d failed: %s — defaulting", i // BATCH + 1, e)
            # Fallback: simple replies
            for d in batch:
                label = derive_label(d.final_recommendation, d.requires_director_approval, d.proposed_action)
                all_replies.append(
                    ReplyEntry(
                        comment_id=d.comment_id,
                        reply_text=f"[{label}] {d.final_reasoning[:300]}",
                        decision_label=label,
                        references_edit_ids=[],
                    )
                )
            save_stage("60_replies.json", all_replies)

    # Stats
    from collections import Counter

    label_counts = Counter(r.decision_label for r in all_replies)
    print(f"\n=== Replies: {len(all_replies)} ===")
    print(f"Labels: {dict(label_counts)}")

    path = save_stage("60_replies.json", all_replies)
    print(f"\nSaved → {path}")
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
