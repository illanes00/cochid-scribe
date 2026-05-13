"""Stage 5: Edit Generator.

Takes resolved decisions, generates exact text patches.
Three scopes: local, consistent, structural (≤500 chars).

Validates: original_text appears EXACTLY ONCE in document.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.review_critic.io.state import save_stage, load_stage
from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.qa.benja_predicate import benja_alignment
from app.services.review_critic.schemas import (
    ClassifiedComment,
    CriticJudgment,
    EditPatch,
    ResolvedDecision,
)

_log = logging.getLogger(__name__)

DOC_FILE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/informe-final-text.md")
MAX_STRUCTURAL_CHARS = 500


SYSTEM_PROMPT = """Eres un editor experto generando ediciones precisas para Google Docs en modo Sugerencia.

Te doy un comentario, su decision (ACCEPT/ACCEPT_PARTIAL), su action (apply_local_edit/apply_consistent_edit/restructure_section/add_content/delete_content), texto del documento, y ledger de facts.

Generas el JSON del edit:

Para apply_local_edit / restructure_section / add_content / delete_content (LOCAL/STRUCTURAL):
{
  "edit_id": "E-C-CIF1",
  "source_comment_ids": ["C-CIF1"],
  "scope": "local" o "structural",
  "original_text": "TEXTO EXACTO del documento que sera reemplazado, ≥30 chars, UNICO en el doc",
  "replacement_text": "TEXTO NUEVO completo (con cambio aplicado)",
  "rationale": "Por que este cambio responde al comentario",
  "confidence": 0.0-1.0
}

Para apply_consistent_edit (CONSISTENT — patron global):
{
  "edit_id": "E-C-EU34",
  "source_comment_ids": ["C-EU-SUG34"],
  "scope": "consistent",
  "find_pattern": "p\\\\. ej\\\\.",  // regex
  "replace_with": "e.g.",
  "context_filter": "exclude_bibliography",  // opcional
  "rationale": "Convencion academica unificada",
  "confidence": 0.95
}

REGLAS:

1. **original_text DEBE existir EXACTAMENTE en el documento que te doy.** Si no estas seguro, anade mas contexto (oracion completa, no fragmento).
2. **original_text >= 30 chars y UNICO.** Si la frase aparece varias veces, extender contexto antes/despues hasta que sea unica.
3. **replacement_text aplica el cambio descrito** preservando estilo, formato, signos.
4. **NO inventar nuevos numeros** que no esten en el ledger. Si necesitas dato, marca [VERIFICAR].
5. **LINEA BENJA:** evitar "se debe", "proponemos", "es necesario crear". Preferir "alternativas", "opciones", "trade-offs", "a discutir".
6. **Para structural (>500 chars cambio total): NO generar.** Marca como skip y el orchestrator lo defiere.
7. **Para consistent edits**, dar regex Python valido escapado.
8. **Para add_content** (CIF "agregar DAC al marco"): original_text = oracion despues de la cual insertas. replacement_text = original_text + ' ' + nuevo parrafo.
9. **Para delete_content**: original_text = lo a borrar. replacement_text = '' (vacio).

Si tienes duda absoluta, marca confidence < 0.5.

Responde SOLO JSON array. Si para un decision no se puede generar edit (ej. none_reply_only), no incluirlo en el array."""


def load_doc_text() -> str:
    return DOC_FILE.read_text() if DOC_FILE.exists() else ""


def validate_local_edit(edit: dict, doc_text: str) -> tuple[bool, str]:
    """Check that original_text appears exactly once. Returns (ok, message)."""
    orig = edit.get("original_text", "")
    if not orig or len(orig) < 20:
        return False, "original_text empty or too short"
    count = doc_text.count(orig)
    if count == 0:
        return False, f"original_text not found in doc"
    if count > 1:
        return False, f"original_text appears {count} times — not unique"
    return True, "ok"


def generate_for_decisions(
    decisions: list[ResolvedDecision],
    classified_by_id: dict[str, ClassifiedComment],
    doc_text: str,
    ledger_summary: str,
) -> list[EditPatch]:
    """Generate edits for the given decisions."""
    actionable = [
        d
        for d in decisions
        if d.proposed_action != "none_reply_only"
        and d.final_recommendation in ("ACCEPT", "ACCEPT_PARTIAL")
    ]

    if not actionable:
        return []

    items = []
    for d in actionable:
        c = classified_by_id.get(d.comment_id)
        if not c:
            continue
        items.append(
            {
                "comment_id": d.comment_id,
                "decision": d.final_recommendation,
                "action": d.proposed_action,
                "comment_text": c.comment_text[:500],
                "quoted_text": (c.quoted_text or "")[:200],
                "section_hint": c.section_hint or "",
                "type": c.type,
                "raw_claims": c.raw_claims,
                "style_hint": c.style_consistency_hint,
                "reasoning": d.final_reasoning,
                "requires_director_approval": d.requires_director_approval,
            }
        )

    user_content = (
        f"DOCUMENTO (extracto relevante):\n{doc_text[:40000]}\n\n---\n\n"
        f"FACTS LEDGER:\n{ledger_summary}\n\n---\n\n"
        f"DECISIONES A IMPLEMENTAR ({len(items)}):\n\n"
        f"{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
        "Genera EditPatch para CADA decision donde sea posible. "
        "Si no se puede generar (texto no encontrable, etc.), omitelo del array. "
        "Recuerda: original_text DEBE existir exacto en el documento."
    )

    response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=300)
    raw = extract_json_array(response)

    edits: list[EditPatch] = []
    for r in raw:
        scope = r.get("scope", "local")

        # Validate local/structural edits
        if scope in ("local", "structural"):
            ok, msg = validate_local_edit(r, doc_text)
            if not ok:
                _log.warning(
                    "Edit %s for %s: %s",
                    r.get("edit_id"),
                    r.get("source_comment_ids"),
                    msg,
                )
                continue
            # Check structural size
            if scope == "structural":
                delta = len(r.get("replacement_text", "")) - len(
                    r.get("original_text", "")
                )
                if abs(delta) > MAX_STRUCTURAL_CHARS:
                    _log.info(
                        "Skipping structural edit %s: delta %d > %d",
                        r.get("edit_id"),
                        abs(delta),
                        MAX_STRUCTURAL_CHARS,
                    )
                    continue

        # Benja predicate check
        repl = r.get("replacement_text", "") or r.get("replace_with", "")
        ba = benja_alignment(repl)
        if ba < 2 and len(repl) > 50:
            _log.warning(
                "Edit %s rejected by benja_predicate (score %d): %s",
                r.get("edit_id"),
                ba,
                repl[:80],
            )
            continue

        try:
            edits.append(
                EditPatch(
                    edit_id=r.get("edit_id", f"E-{r.get('source_comment_ids',['x'])[0]}"),
                    source_comment_ids=r.get("source_comment_ids", []),
                    scope=scope,
                    section_anchor=r.get("section_anchor"),
                    original_text=r.get("original_text", ""),
                    replacement_text=r.get("replacement_text", ""),
                    find_pattern=r.get("find_pattern"),
                    replace_with=r.get("replace_with"),
                    context_filter=r.get("context_filter"),
                    rationale=r.get("rationale", ""),
                    confidence=float(r.get("confidence", 0.5)),
                )
            )
        except Exception as e:
            _log.warning("EditPatch parse error: %s — raw: %s", e, r)

    return edits


def run() -> Path:
    decisions = load_stage("41_resolved_decisions.json", ResolvedDecision)
    classified = load_stage("10_classified.json", ClassifiedComment)
    classified_by_id = {c.id: c for c in classified}

    doc_text = load_doc_text()
    ledger = load_ledger()
    ledger_summary = "\n".join(
        f"  [{f.status}] {f.claim_id}: {f.claim_text[:80]}" for f in ledger.facts
    )

    print(f"Edit Generator: {len(decisions)} decisions")

    # Process in batches of 20 actionable decisions
    actionable = [
        d
        for d in decisions
        if d.proposed_action != "none_reply_only"
        and d.final_recommendation in ("ACCEPT", "ACCEPT_PARTIAL")
    ]
    print(f"  Actionable: {len(actionable)}")

    BATCH = 6
    all_edits: list[EditPatch] = []
    for i in range(0, len(actionable), BATCH):
        batch = actionable[i : i + BATCH]
        print(f"  Batch {i // BATCH + 1}: {len(batch)} decisions")
        try:
            batch_edits = generate_for_decisions(
                batch, classified_by_id, doc_text, ledger_summary
            )
            all_edits.extend(batch_edits)
            # Checkpoint after each batch
            save_stage("50_edit_patches.json", all_edits)
            print(f"    -> {len(batch_edits)} edits generated, total so far: {len(all_edits)}")
        except Exception as e:
            _log.warning("Batch %d failed: %s — continuing", i // BATCH + 1, e)
            save_stage("50_edit_patches.json", all_edits)

    # Stats
    from collections import Counter

    scope_counts = Counter(e.scope for e in all_edits)
    print(f"\n=== Edits generated: {len(all_edits)} ===")
    print(f"Scopes: {dict(scope_counts)}")

    path = save_stage("50_edit_patches.json", all_edits)
    print(f"\nSaved → {path}")
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
