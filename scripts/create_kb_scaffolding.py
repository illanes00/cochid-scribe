#!/usr/bin/env python3
"""
Create/update KB scaffold notes (methodology) and link them to documents.

This supports deep analysis work without touching core app code.

Usage:
  python scripts/create_kb_scaffolding.py --db backend/scribe.db
"""

from __future__ import annotations

import argparse
import sqlite3

from connect_claims_kb import ensure_link, upsert_note


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="backend/scribe.db")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    # CIF methodology note
    cur.execute("SELECT id, title FROM documents WHERE slug = ?", ("cif-medicamentos",))
    row = cur.fetchone()
    if row:
        doc_id, doc_title = row
        note_id = upsert_note(
            cur,
            slug="metodologia-cif-epf-2022-2023",
            title="Metodología CIF — EPF 2022-2023 (INE) y medicamentos (CCIF 06.1.1)",
            note_type="concept",
            tags=["cif-medicamentos", "metodologia", "EPF", "CCIF"],
            markdown=(
                "# Metodología CIF — EPF 2022-2023 (INE) y medicamentos (CCIF 06.1.1)\n\n"
                "## Pregunta y alcance\n"
                "- ¿Cómo se distribuye el gasto en medicamentos (y su carga) por nivel socioeconómico?\n"
                "- Unidad de análisis: hogar (EPF). Periodo: 2022–2023.\n\n"
                "## Fuente de datos (EPF)\n"
                "- Encuesta de Presupuestos Familiares (INE), IX EPF 2022–2023.\n"
                "- Muestra ~15.000 hogares; diseño complejo (estratificado). Cobertura nacional.\n"
                "- Clasificación CCIF para identificar gasto en medicamentos: **06.1.1**.\n\n"
                "## Definiciones (operativas)\n"
                "- **Gasto mensual promedio**: promedio del gasto mensual reportado en medicamentos.\n"
                "- **Incidencia**: proporción de hogares con gasto positivo en medicamentos.\n"
                "- **Carga sobre ingreso**: gasto en medicamentos / ingreso del hogar (o proxy disponible).\n"
                "- **Mediana**: percentil 50 del gasto; mediana 0 implica que ≥50% reporta gasto 0.\n\n"
                "## Qué se puede y no se puede inferir\n"
                "- La **incidencia** no distingue entre:\n"
                "  - (a) no necesitó medicamentos,\n"
                "  - (b) accedió vía cobertura pública / programas,\n"
                "  - (c) no accedió por barreras (precio/financiamiento/disponibilidad).\n"
                "- EPF captura gasto monetario declarado; puede haber sustitución, compra informal, o provisión gratuita.\n\n"
                "## Riesgos de interpretación (alertas)\n"
                "- No confundir:\n"
                "  - **gasto de bolsillo en medicamentos** (nivel hogar/persona)\n"
                "  - con **medicamentos como % del gasto en salud** (macro).\n"
                "- Cuando se compare con OCDE: explicitar métrica (US$ PPP per cápita) y año.\n\n"
                "## Checklist de evidencia por claim (mínimo)\n"
                "- [ ] Fuente exacta (INE EPF / tabla / extracción) y definiciones.\n"
                "- [ ] Año, universo (hogares), y método (promedio/mediana/incidencia).\n"
                "- [ ] Nota de limitaciones cuando corresponda.\n\n"
                "## Cómo usar esta nota\n"
                "- Linkear desde claims relevantes (interpretación de incidencia, medianas, comparaciones).\n"
                "- Mantener consistencia de definiciones en el documento y en Google export.\n"
            ),
        )
        ensure_link(
            cur,
            source_type="document",
            source_id=doc_id,
            target_type="note",
            target_id=note_id,
            link_type="reference",
            context="methodology",
        )
        # Link all claims in the document to the methodology note (graph navigation)
        cur.execute("SELECT id FROM claims WHERE document_id = ?", (doc_id,))
        for (claim_db_id,) in cur.fetchall():
            ensure_link(
                cur,
                source_type="claim",
                source_id=claim_db_id,
                target_type="note",
                target_id=note_id,
                link_type="reference",
                context="methodology",
            )

    # BID methodology note
    cur.execute("SELECT id, title FROM documents WHERE slug = ?", ("bid-seguridad-resumen",))
    row = cur.fetchone()
    if row:
        doc_id, doc_title = row
        note_id = upsert_note(
            cur,
            slug="metodologia-bid-seguridad-cofog",
            title="Metodología BID — Gasto en seguridad (COFOG) y comparabilidad",
            note_type="concept",
            tags=["bid-seguridad-resumen", "metodologia", "COFOG", "DIPRES"],
            markdown=(
                "# Metodología BID — Gasto en seguridad (COFOG) y comparabilidad\n\n"
                "## Pregunta y alcance\n"
                "- ¿Cómo se compone el gasto en seguridad y qué márgenes de eficiencia existen?\n"
                "- Énfasis: composición (policías, justicia, prisiones, prevención) y gestión del gasto.\n\n"
                "## Fuentes típicas (a verificar por claim)\n"
                "- DIPRES / Presupuesto (ejecución y clasificación funcional).\n"
                "- Clasificación COFOG: funciones 7031–7036 (según disponibilidad).\n"
                "- CEP (prioridad ciudadana), ENUSC u otras encuestas (victimización/percepción).\n"
                "- Series de homicidios: fuente oficial (p.ej., CEAD / Ministerio Público / policías) según claim.\n\n"
                "## Definiciones (operativas)\n"
                "- **% del PIB** y **% del gasto total**: explicitar numerador/denominador y año.\n"
                "- **Comparación internacional**: requiere consistencia estadística (clasificación, PPP, año).\n"
                "- **I+D (COFOG 7035)**: confirmar si existe subfunción reportada o si es 0/no clasificado.\n\n"
                "## Riesgos de interpretación\n"
                "- “No subfinanciado” es un juicio comparativo: debe estar soportado por benchmark y método.\n"
                "- “Orden de magnitud” (p.ej., reasignaciones) debe tratarse como estimación y supuestos.\n\n"
                "## Checklist de evidencia por claim (mínimo)\n"
                "- [ ] Fuente oficial y tabla/serie exacta.\n"
                "- [ ] Definición del indicador y periodo.\n"
                "- [ ] Nota de comparabilidad (si aplica internacional).\n\n"
                "## Cómo usar esta nota\n"
                "- Linkear desde claims sobre niveles (%PIB), composición, encuestas y series de criminalidad.\n"
                "- Mantener consistencia entre resumen ejecutivo y deck.\n"
            ),
        )
        ensure_link(
            cur,
            source_type="document",
            source_id=doc_id,
            target_type="note",
            target_id=note_id,
            link_type="reference",
            context="methodology",
        )
        cur.execute("SELECT id FROM claims WHERE document_id = ?", (doc_id,))
        for (claim_db_id,) in cur.fetchall():
            ensure_link(
                cur,
                source_type="claim",
                source_id=claim_db_id,
                target_type="note",
                target_id=note_id,
                link_type="reference",
                context="methodology",
            )

    conn.commit()
    conn.close()
    print("OK: KB scaffolding ensured (methodology notes + links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
