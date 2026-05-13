"""Benja editorial predicate — machine-checkable rule.

Score 0-5 for how well a proposed edit aligns with Benja's editorial line:
"Profundidad técnica SÍ, casarnos con una política NO."
"""

from __future__ import annotations


PRESCRIPTIVE_PHRASES = [
    "se debe",
    "proponemos implementar",
    "proponemos crear",
    "recomendamos implementar",
    "es necesario crear",
    "la solución es",
    "debiera implementarse",
    "el camino correcto es",
    "el modelo a seguir es",
    "es imperativo",
]

OPENNESS_PHRASES = [
    "alternativas",
    "opciones",
    "trade-offs",
    "trade off",
    "a discutir",
    "posibles",
    "podría considerarse",
    "entre otras opciones",
    "marco para la discusión",
    "sin alinearnos",
    "preguntas abiertas",
    "para la deliberación",
]

EVIDENCE_MARKERS = [
    "fuente:",
    "minsal",
    "ine ",
    "epf",
    "oms ",
    "oecd",
    "ocde",
    "tabla",
    "figura",
    "ghed",
    "decreto",
    "ley n",
    "según",
    "datos de",
]


def benja_alignment(text: str) -> int:
    """Score 0-5: how well does this text fit Benja's editorial line.

    5 = adds technical evidence without prescription
    3 = neutral
    0 = strongly prescriptive without evidence
    """
    if not text:
        return 3
    txt = text.lower()
    score = 3  # neutral baseline

    # Reward evidence/sources
    evidence_hits = sum(1 for m in EVIDENCE_MARKERS if m in txt)
    if evidence_hits >= 2:
        score += 2
    elif evidence_hits >= 1:
        score += 1

    # Reward openness
    openness_hits = sum(1 for p in OPENNESS_PHRASES if p in txt)
    if openness_hits >= 1:
        score += 1

    # Penalize prescriptive
    prescriptive_hits = sum(1 for p in PRESCRIPTIVE_PHRASES if p in txt)
    if prescriptive_hits >= 2:
        score -= 3
    elif prescriptive_hits >= 1:
        score -= 2

    return max(0, min(5, score))


def is_acceptable(text: str, threshold: int = 2) -> bool:
    """Hard filter: reject text below threshold."""
    return benja_alignment(text) >= threshold


if __name__ == "__main__":
    samples = [
        ("Se debe crear un BFAU obligatorio.", "should be low"),
        ("El DAC opera desde 2019 (Decreto MINSAL), cubriendo medicamentos oncológicos.", "should be high"),
        ("Algunas opciones para discutir incluyen el BFAU como alternativa entre varias.", "should be high"),
        ("Proponemos implementar el modelo alemán.", "should be low"),
        ("Las experiencias internacionales muestran trade-offs entre cobertura y costo.", "should be high"),
    ]
    for text, expected in samples:
        s = benja_alignment(text)
        print(f"{s}/5 — {expected}: {text}")
