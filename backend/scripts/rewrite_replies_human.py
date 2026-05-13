"""Rewrite replies in human voice: no em dashes, no IA clichés, explicit process for DEFER."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/srv/projects/cochid/cochid-scribe/backend")

from app.services.review_critic.llm import call_claude, extract_json_array

REPLIES_PATH = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/critic-state/60_replies.json")
DECISIONS_PATH = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/critic-state/41_resolved_decisions.json")
CLASSIFIED_PATH = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/critic-state/10_classified.json")
OUTPUT_PATH = REPLIES_PATH  # overwrite

SYSTEM_PROMPT = """Eres un corrector senior que revisa un informe de políticas públicas. Reescribes los replies de un documento manteniendo su contenido tecnico y las decisiones, pero con voz humana y directa.

REGLAS DE ESTILO (criticas):

1. SIN em dashes (—). Usa coma, parentesis, dos puntos, o punto aparte.
2. SIN prefijos tipo [ACEPTADO] / [RECHAZADO] / [PENDIENTE] en el texto. El sistema ya lleva el label aparte.
3. SIN estas frases cliche de IA:
   - "Aceptado parcialmente."
   - "Propuesta tentativa:"
   - "Alerta valida"
   - "Buena observacion"
   - "Se incorpora como..."
   - "Se agrega..."
   - "Discrepamos:"
   - "A validar con..."
4. Tono: corrector senior hablando a un autor academico. Directo, conciso, tecnico. Sin adulacion, sin defensividad.
5. Para DEFER / PENDIENTE_DIRECTORES (cambios mayores): ser EXPLICITO sobre:
   - Por que no se aplico directamente
   - Que opciones hay (A, B, C)
   - Quien debe decidir (Benja / Eduardo / Carla / equipo)
   - Proceso sugerido: "revisar en reunion de directores" o "confirmar antes del envio a CIF"
6. Para ACCEPT: decir que cambio se hizo y donde (seccion X.Y), con dato o fuente si aplica.
7. Para REJECT: dar la razon con fuente o evidencia, sin frases de cortesia.
8. Para RESPUESTA (preguntas): responder directo, con la seccion o ejemplo concreto.
9. Para NEEDS_DATA: decir exactamente que dato falta y donde verificarlo.
10. Longitud: 2 a 4 oraciones. Conciso.

CONTEXTO IMPORTANTE: Benja (director ejecutivo) esta preocupado por el rigor de los datos y por que todos (CIF, Eduardo, Carla) queden tranquilos con el resultado. Para los cambios mayores, hay que dejar explicito como se validaran antes de cerrarlos.

INPUT: JSON array con objetos {comment_id, old_reply, decision_label, decision_reasoning, comment_author, comment_text}

OUTPUT: JSON array con {comment_id, reply_text}. reply_text es el texto reescrito. Sin prefijos, sin em dashes.

Responde SOLO el JSON array, sin prosa adicional, sin bloques markdown."""


def load_json(path: Path) -> list:
    return json.loads(path.read_text())["data"]


def save_replies(new_texts: dict[str, str]):
    full = json.loads(REPLIES_PATH.read_text())
    for r in full["data"]:
        cid = r["comment_id"]
        if cid in new_texts:
            r["reply_text"] = new_texts[cid]
    REPLIES_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2))


def main():
    replies = load_json(REPLIES_PATH)
    decisions = {d["comment_id"]: d for d in load_json(DECISIONS_PATH)}
    classified = {c["id"]: c for c in load_json(CLASSIFIED_PATH)}

    print(f"Rewriting {len(replies)} replies...")

    # Process in batches of 15
    BATCH = 15
    all_new: dict[str, str] = {}

    for i in range(0, len(replies), BATCH):
        batch = replies[i : i + BATCH]
        items = []
        for r in batch:
            cid = r["comment_id"]
            d = decisions.get(cid, {})
            c = classified.get(cid, {})
            items.append(
                {
                    "comment_id": cid,
                    "old_reply": r["reply_text"],
                    "decision_label": r["decision_label"],
                    "final_recommendation": d.get("final_recommendation", ""),
                    "requires_director_approval": d.get("requires_director_approval", False),
                    "decision_reasoning": (d.get("final_reasoning") or "")[:500],
                    "comment_author": c.get("author", "?"),
                    "comment_text": (c.get("comment_text") or "")[:300],
                }
            )

        user_content = json.dumps(items, ensure_ascii=False, indent=1)
        print(f"  Batch {i // BATCH + 1}/{(len(replies) + BATCH - 1) // BATCH} ({len(items)} items)")

        try:
            resp = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=300)
            new_items = extract_json_array(resp)
            for it in new_items:
                if "comment_id" in it and "reply_text" in it:
                    txt = it["reply_text"].strip()
                    # Safety: strip residual em dashes and [LABEL] prefix
                    txt = txt.replace("—", ",").replace("–", ",")
                    import re
                    txt = re.sub(r"^\[[A-Z_]+\]\s*", "", txt)
                    all_new[it["comment_id"]] = txt
        except Exception as e:
            print(f"  !! batch failed: {e}")
            continue

    print(f"\nRewrote {len(all_new)} / {len(replies)}")
    save_replies(all_new)
    print(f"Saved → {REPLIES_PATH}")


if __name__ == "__main__":
    main()
