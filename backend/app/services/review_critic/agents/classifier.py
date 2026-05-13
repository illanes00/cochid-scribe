"""Stage 1: Classifier.

Takes 91 comments from comment-mapping.json and classifies each by:
- type: factual | structural | stylistic | methodological | strategic | question | general
- specificity: local | section | document
- verifiability: factual_claim | opinion | suggestion
- touches_sections: list of section refs
- has_embedded_claim: bool
- style_consistency_hint: consistent_rule | local_substitution | n/a
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.io.state import save_stage, hash_file
from app.services.review_critic.schemas import ClassifiedComment, CommentInput

_log = logging.getLogger(__name__)

MAPPING_FILE = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/comment-mapping.json"
)


def load_comments() -> list[CommentInput]:
    """Load the 91 comments from comment-mapping.json."""
    with open(MAPPING_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return [CommentInput(**item) for item in raw]


SYSTEM_PROMPT = """Eres un editor académico senior. Vas a clasificar comentarios de revisores sobre un informe de política pública chileno (medicamentos en planes de salud).

Para CADA comentario asigna:

1. **type** (uno de):
   - "factual": afirma o cuestiona un hecho específico verificable (cifra, decreto, dato)
   - "structural": sobre estructura del documento (secciones, orden, headings, subsecciones)
   - "stylistic": sobre redacción, jerga, tono, sustitución de palabras
   - "methodological": sobre cómo se hizo el análisis (selección, fuentes, metodología)
   - "strategic": sobre dirección general (prescriptivo vs descriptivo, framing)
   - "question": el revisor está preguntando algo (no afirmando)
   - "general": observación amplia sobre el documento como un todo

2. **specificity**:
   - "local": afecta un texto específico
   - "section": afecta una sección
   - "document": afecta el doc completo

3. **verifiability**:
   - "factual_claim": el revisor afirma algo chequeable (ej: "GES tiene 87 patologías pero son 90")
   - "opinion": preferencia subjetiva
   - "suggestion": cambio propuesto sin claim factual

4. **touches_sections**: lista de secciones que toca (ej ["2.4", "5.3"])

5. **has_embedded_claim**: true si el comentario contiene una afirmación factual chequeable

6. **raw_claims**: lista de afirmaciones factuales extraídas del comentario (vacía si no hay)

7. **style_consistency_hint** (solo si type=stylistic):
   - "consistent_rule": la regla aplica consistente (ej: "p.ej.→e.g." debe ser en todo el doc)
   - "local_substitution": depende del contexto (ej: "sostienen→explican" funciona aquí pero no allá)
   - "n/a": para todo lo que no es stylistic

Responde SOLO con un JSON array, formato:
```json
[
  {"id": "C-CIF1", "type": "factual", "specificity": "section", "verifiability": "factual_claim", "touches_sections": ["2.4"], "has_embedded_claim": true, "raw_claims": ["La tabla de coberturas no incorpora DAC"], "style_consistency_hint": "n/a"},
  ...
]
```

NO incluyas otros campos. NO incluyas prosa fuera del JSON."""


BATCH_SIZE = 15


def classify_batch(comments: list[CommentInput]) -> list[dict]:
    """Classify a batch of comments. Returns raw dicts."""
    items_for_llm = []
    for c in comments:
        items_for_llm.append(
            {
                "id": c.id,
                "author": c.author,
                "comment_text": c.comment_text[:400],
                "search_phrase": c.search_phrase[:100] if c.search_phrase else "",
                "section_hint": c.section_hint,
            }
        )

    user_content = (
        f"COMENTARIOS A CLASIFICAR ({len(items_for_llm)} total):\n\n"
        f"{json.dumps(items_for_llm, ensure_ascii=False, indent=1)}\n\n"
        f"Clasifica TODOS los {len(items_for_llm)} comentarios. "
        "Responde con JSON array de objetos, uno por comentario, en el mismo orden."
    )

    _log.info("Classifier: batch of %d", len(comments))
    response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=600)
    return extract_json_array(response)


def classify_all(comments: list[CommentInput]) -> list[ClassifiedComment]:
    """Classify all 91 comments in batches."""
    raw_classifications: list[dict] = []
    for i in range(0, len(comments), BATCH_SIZE):
        batch = comments[i : i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}/{(len(comments) + BATCH_SIZE - 1) // BATCH_SIZE}: {len(batch)} comments")
        raw_classifications.extend(classify_batch(batch))
    _log.info("Classifier: got %d classifications total", len(raw_classifications))

    # Map by ID, then build ClassifiedComment by zipping with input
    by_id = {item["id"]: item for item in raw_classifications}

    results: list[ClassifiedComment] = []
    for c in comments:
        cls = by_id.get(c.id)
        if cls is None:
            _log.warning("Classifier: missing classification for %s — defaulting", c.id)
            cls = {
                "type": "general",
                "specificity": "section",
                "verifiability": "opinion",
                "touches_sections": [c.section_hint] if c.section_hint else [],
                "has_embedded_claim": False,
                "raw_claims": [],
                "style_consistency_hint": "n/a",
            }
        results.append(
            ClassifiedComment(
                id=c.id,
                author=c.author,
                comment_text=c.comment_text,
                quoted_text=c.search_phrase[:200] if c.search_phrase else None,
                section_hint=c.section_hint,
                type=cls.get("type", "general"),
                specificity=cls.get("specificity", "section"),
                verifiability=cls.get("verifiability", "opinion"),
                touches_sections=cls.get("touches_sections", []) or [],
                has_embedded_claim=cls.get("has_embedded_claim", False),
                raw_claims=cls.get("raw_claims", []) or [],
                style_consistency_hint=cls.get("style_consistency_hint", "n/a"),
            )
        )

    return results


def run() -> Path:
    """Run the Classifier and save output."""
    comments = load_comments()
    classified = classify_all(comments)

    # Compute and report stats
    from collections import Counter

    type_counts = Counter(c.type for c in classified)
    spec_counts = Counter(c.specificity for c in classified)
    print(f"\n=== Classified {len(classified)} comments ===")
    print(f"Types: {dict(type_counts)}")
    print(f"Specificity: {dict(spec_counts)}")

    path = save_stage(
        "10_classified.json",
        classified,
        input_hashes={
            "comment-mapping.json": hash_file(MAPPING_FILE),
        },
    )
    print(f"\nSaved → {path}")
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
