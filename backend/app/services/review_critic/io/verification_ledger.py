"""Verification ledger operations.

The ledger is authoritative truth for the Critic. It contains:
- Facts: claims that have been verified (confirmed/refuted/inconclusive)
- Bibliography: per-entry audit results

The ledger is appendable: facts are added as they're verified, never removed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.services.review_critic.io.state import STATE_DIR, save_stage, load_stage, stage_exists
from app.services.review_critic.schemas import (
    BibliographyAuditEntry,
    VerificationLedger,
    VerificationResult,
)

LEDGER_FILE = "21_verification_ledger.json"


def load_ledger() -> VerificationLedger:
    """Load the current ledger, or return empty if not yet created."""
    if not stage_exists(LEDGER_FILE):
        return VerificationLedger()
    data = load_stage(LEDGER_FILE)
    if isinstance(data, dict):
        return VerificationLedger(**data)
    return VerificationLedger()


def save_ledger(ledger: VerificationLedger) -> Path:
    """Save the ledger atomically."""
    ledger.last_updated = datetime.utcnow()
    return save_stage(LEDGER_FILE, ledger)


def add_fact(ledger: VerificationLedger, fact: VerificationResult) -> None:
    """Append a fact to the ledger (in-place)."""
    # Replace if claim_id already exists
    ledger.facts = [f for f in ledger.facts if f.claim_id != fact.claim_id]
    ledger.facts.append(fact)


def add_bib_entry(ledger: VerificationLedger, entry: BibliographyAuditEntry) -> None:
    """Append a bibliography audit entry (in-place)."""
    ledger.bibliography = [
        b for b in ledger.bibliography if b.bib_key != entry.bib_key
    ]
    ledger.bibliography.append(entry)


def get_fact(ledger: VerificationLedger, claim_id: str) -> VerificationResult | None:
    for f in ledger.facts:
        if f.claim_id == claim_id:
            return f
    return None


def facts_for_comment(
    ledger: VerificationLedger, comment_id: str
) -> list[VerificationResult]:
    return [f for f in ledger.facts if f.source_comment_id == comment_id]


# ============================================================================
# Pre-seeded facts (known from prior verification work)
# ============================================================================


def seed_known_facts() -> VerificationLedger:
    """Build a ledger pre-seeded with verification results from prior work."""
    ledger = VerificationLedger()

    # Fact 1: 71% retail OOP — methodology clarification
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-71-retail-oop",
            source_comment_id=None,  # General doc-level fact
            claim_text="71% del gasto en medicamentos de farmacias (retail) financiado por hogares en 2022 (INE EPF + OECD)",
            status="inconclusive",
            evidence=(
                "Reproducción desde EPF sola da 28.44% (medicamentos/gasto_salud_hogar) "
                "o 37.13% (filtrando hogares con gasto positivo). El 71% del informe es "
                "una share de FINANCIAMIENTO (OOP / total_retail_medicines), no de spending. "
                "Requiere combinar EPF (OOP hogares) con OECD/MINSAL (gasto público retail). "
                "Trayectoria documentada en doc: 78% (2021) → 71% (2022) → ~66% (2023) según OECD. "
                "Aclarar metodología: 'Para 2022, OOP de hogares = $143.770M EPF; gasto público "
                "retail (FONASA/ISAPRE compra externa) ≈ $58.000M; OOP/Total ≈ 71%'."
            ),
            authoritative_source="OECD Health at a Glance + INE EPF 2022-2023",
            confidence=0.7,
        ),
    )

    # Fact 2: GES patologías — outdated number
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-ges-patologias",
            source_comment_id=None,
            claim_text="GES tiene 87 patologías priorizadas",
            status="refuted",
            evidence=(
                "El Decreto Supremo MINSAL para el periodo 2025-2028 actualiza GES a "
                "90 patologías priorizadas. La cifra 87 corresponde al decreto pre-2025. "
                "Corrección sugerida: 'GES (90 patologías priorizadas, Decreto MINSAL 2025-2028)'."
            ),
            authoritative_source="Decreto Supremo MINSAL 2025-2028 (Diario Oficial)",
            confidence=0.95,
        ),
    )

    # Fact 3: US$206 attribution — wrong source/unit/year
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-us206-attribution",
            source_comment_id=None,
            claim_text="US$206 per cápita en medicamentos (atribuido a OECD 2025 como PPA)",
            status="refuted",
            evidence=(
                "El dato US$206 viene de OMS GHED (Global Health Expenditure Database) "
                "para Chile en 2022, expresado en US$ corrientes (NO PPA). "
                "Atribución actual del informe ('OCDE, 2025, PPA') es triple error: "
                "fuente equivocada (OMS no OECD), unidad equivocada (corrientes no PPA), "
                "año equivocado (2022 no 2025). "
                "Corrección: 'US$206 per cápita en 2022 (US$ corrientes), OMS GHED 2024'. "
                "Para PPA real de Chile 2023 según OECD: US$455."
            ),
            authoritative_source="OMS Global Health Expenditure Database 2024",
            confidence=0.95,
        ),
    )

    # Fact 4: Costa Rica CCSS coverage
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-costa-rica-ccss",
            source_comment_id=None,
            claim_text="Costa Rica CCSS cubre ~95% de la población",
            status="refuted",
            evidence=(
                "La cobertura real efectiva de CCSS para 2023 está entre 91% y 93% según "
                "estadísticas oficiales CCSS y reportes PAHO. El 95% es una cifra de "
                "afiliación nominal o de períodos anteriores. "
                "Corrección: 'Costa Rica CCSS cubre 91-93% de la población (CCSS 2023)'."
            ),
            authoritative_source="CCSS Memoria Institucional + PAHO Health in the Americas 2024",
            confidence=0.85,
        ),
    )

    # Fact 5: Q1 burden calculation inconsistency
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-q1-burden-calc",
            source_comment_id=None,
            claim_text="Q1 (quintil 1): ingreso $329.000 CLP/mes, gasto medicamentos $16.526 CLP/mes, carga 9.8%",
            status="inconclusive",
            evidence=(
                "Cálculo directo: 16.526 / 329.000 = 5.02%, no 9.8%. "
                "El 9.8% en la tabla del CSV (99_tabla_gasto_medicamentos_quintil.csv) "
                "puede corresponder a una definición distinta de ingreso (ingreso disponible "
                "vs ingreso total vs ingreso per cápita) o a hogares filtrados (solo con "
                "gasto positivo). Verificación con dataset_hogares_meds.csv da Q1 = 5.34% "
                "(meds/ingreso ponderado). "
                "Acción requerida: documentar explícitamente la definición de ingreso usada "
                "para llegar a 9.8%, o corregir a 5-5.34%."
            ),
            authoritative_source="EPF IX 2022-2023, dataset_hogares_meds.csv",
            confidence=0.7,
        ),
    )

    # Fact 6: Mediana OECD per cápita medicamentos
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-mediana-ocde-percapita",
            source_comment_id=None,
            claim_text="Mediana OCDE per cápita medicamentos = US$600",
            status="refuted",
            evidence=(
                "Cálculo desde oecd_pharma_ppp.csv (16-19 países OECD con datos disponibles): "
                "mediana real ≈ US$533-550. La cifra US$600 es una sobreestimación. "
                "Corrección: 'mediana OCDE de aproximadamente US$533-550 (cálculo propio "
                "sobre dataset OECD Health at a Glance 2023, 16 países OECD)'."
            ),
            authoritative_source="OECD Health at a Glance 2023 + oecd_pharma_ppp.csv",
            confidence=0.85,
        ),
    )

    # Fact 7: USD 455 PPA per cápita Chile 2023
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-us455-ppa-chile",
            source_comment_id=None,
            claim_text="US$455 PPA per cápita Chile 2023 (vs US$766 promedio OCDE)",
            status="confirmed",
            evidence=(
                "Confirmado contra OECD Health at a Glance 2023, dataset oecd_pharma_ppp.csv. "
                "Chile 2023: USD 455 PPP, debajo del promedio OECD USD 766."
            ),
            authoritative_source="OECD Health at a Glance 2023",
            confidence=0.9,
        ),
    )

    # Fact 8: 78% retail OOP 2021
    add_fact(
        ledger,
        VerificationResult(
            claim_id="V-78-retail-2021",
            source_comment_id=None,
            claim_text="78% del gasto retail medicamentos OOP en Chile (2021) según OECD",
            status="confirmed",
            evidence=(
                "Confirmado por OECD Health at a Glance 2023 (datos 2021). "
                "Trayectoria temporal coherente: 78% (2021) → 71% (2022) → ~66% (2023)."
            ),
            authoritative_source="OECD Health at a Glance 2023",
            confidence=0.9,
        ),
    )

    return ledger


if __name__ == "__main__":
    # Initialize ledger with seed facts
    ledger = seed_known_facts()
    path = save_ledger(ledger)
    print(f"Ledger seeded with {len(ledger.facts)} facts → {path}")
    for f in ledger.facts:
        print(f"  [{f.status:15s}] {f.claim_id}: {f.claim_text[:70]}")
