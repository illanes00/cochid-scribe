"""Diff export — shows each comment with its concrete text change.

Generates a visual diff (like git/diffchecker) showing what text existed
before and what was changed/added for each reviewer comment.
"""

from __future__ import annotations

import html
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.document import Document
from app.models.track_change import TrackChange


# Map of comment content prefixes → concrete before/after diffs
COMMENT_DIFFS = {
    "El estudio parece borrador": {
        "section": "Secciones 4.1-4.3",
        "before": """**[TABLA PROPUESTA: Estructura de copagos por quintil - requiere definición técnica]**

**[PROPUESTA: Mecanismo de articulación BFAU-Ley Ricarte Soto - requiere diseño operativo]**

**[PROPUESTA: Reglas de transición ISAPRE - requiere diseño regulatorio]**

**[PROPUESTA: Cronograma detallado de implementación - requiere planificación]**""",
        "after": "(7 placeholders eliminados. Contenido desarrollado en tabla de opciones por nivel de reforma y sección de seminario de discusión.)",
        "action": "delete",
    },
    "Mezcla diagnóstico": {
        "section": "Sección 4 (título) + Sección 7 (título)",
        "before": "## 4. Propuesta: Beneficio Farmacéutico Ambulatorio Universal\n\nEl estudio propone la creación de un BFAU como mecanismo estructural...",
        "after": "## 4. Opciones de Política: Hacia un Beneficio Farmacéutico\n\nPara traducir las lecciones internacionales al contexto chileno, se presentan opciones de política. Estas no constituyen una recomendación única, sino un marco para la discusión...",
        "action": "replace",
    },
    "Hay secciones que no parecen cerradas": {
        "section": "Sección 7 + Nueva sección 8",
        "before": "## 7. Conclusiones y Recomendaciones\n\nEl análisis permite establecer cinco conclusiones principales.",
        "after": "## 7. Marco para la Discusión\n\nEl análisis presentado permite establecer cinco conclusiones principales que informan la discusión.\n\n## 8. Hacia el Seminario de Discusión\n\n1. ¿Qué nivel de cobertura es deseable y fiscalmente sostenible?\n2. ¿Qué mecanismo de financiamiento equilibra equidad y sostenibilidad?\n3. ¿Cómo articular BFAU, GES, Ricarte Soto y DAC?\n4. ¿Qué rol debe tener ETESA?\n5. ¿Cómo incorporar innovación farmacéutica?",
        "action": "replace",
    },
    "Explicar con mayor precisión cómo se seleccionaron": {
        "section": "Sección 3 (inicio)",
        "before": "## 3. Comparación Internacional: Lecciones de la OCDE\n\nChile presenta indicadores...",
        "after": "## 3. Comparación Internacional: Lecciones de la OCDE\n\n*Nota metodológica: Se seleccionaron países de ingreso medio-alto con sistemas mixtos (Brasil, México) y cobertura universal (Costa Rica) como benchmarks regionales. Los datos corresponden al último año disponible en OECD Health at a Glance 2025 y WHO GHED 2024. Las comparaciones requieren cautela: la proporción de gasto retail refleja la estructura institucional de cada país, no solo la equidad del sistema.*\n\nChile presenta indicadores...",
        "action": "insert",
    },
    "Ordenar claramente qué medidas": {
        "section": "Sección 4 (nueva tabla)",
        "before": "(No existía tabla de clasificación de medidas)",
        "after": "| Sin reforma legal mayor | Ajustes regulatorios | Rediseño sistémico |\n|---|---|---|\n| Fortalecer gestión inventarios APS | Copagos diferenciados con topes | BFAU universal (FONASA + ISAPRE) |\n| Prescripción electrónica | Listado nacional vinculante ETESA | Integración compras CENABAST-ISAPRE |\n| Ampliar formulario nacional | Regulación biosimilares | Reforma financiamiento solidario |\n| Farmacias comunitarias APS | Exenciones grupos vulnerables | Cobertura costo intermedio |\n| Fortalecer CENABAST | Trazabilidad genéricos | Articulación BFAU-GES-Ricarte-DAC |",
        "action": "insert",
    },
    "Se incorpora la brecha de cobertura en medicamentos": {
        "section": "Sección 2.2 → 2.3 (nueva)",
        "before": "(La sección 2.2 mencionaba antineoplásicos 0% Q1 vs 1% Q5 pero sin desarrollo de patologías complejas ni experiencia de exclusión)",
        "after": "### 2.3 Judicialización como Indicador de Brechas de Acceso\n\nLa judicialización del acceso a medicamentos constituye un síntoma directo de las fallas del sistema de cobertura. Vargas-Pelaez et al. (2019) documentan que en Chile la mayoría de demandas sanitarias se dirigen contra aseguradoras privadas. En febrero 2026, la Corte Suprema limitó los recursos de protección para medicamentos no listados, estableciendo que el acceso judicial individual genera discriminación frente a quienes no litigan.",
        "action": "insert",
    },
    "Reforzar que el objetivo de ETESA": {
        "section": "Sección 3 punto 4 + Sección 6",
        "before": "**Reglas de sustitución por bioequivalentes y genéricos** para contener costos sin afectar la calidad terapéutica.",
        "after": "**Listados positivos explícitos** actualizados mediante ETESA. La ETESA opera como mecanismo de priorización basado en valor sanitario, social y económico — no como instrumento de contención de gasto. Su proceso de tres etapas cubre eficacia, seguridad, costo-efectividad y dimensiones éticas y sociales (Armijo et al., 2022).",
        "action": "replace",
    },
    "Se debieran incorporar con mayor claridad ejemplos": {
        "section": "Sección 3.1 (nueva)",
        "before": "(No existía sección de innovación con valor sanitario)",
        "after": "### 3.1 Innovación con Valor Sanitario\n\nExisten ejemplos internacionales de innovación que generan simultáneamente valor sanitario y ahorro sistémico:\n(1) biosimilares oncológicos en Europa: -20-40% costos sin afectar resultados clínicos\n(2) programas diabetes con cobertura + seguimiento digital: -15-25% hospitalizaciones\n(Cortez, Medici & Singh, 2023)",
        "action": "insert",
    },
    "Se tiende a asimilar biosimilares": {
        "section": "Sección 3 punto 4",
        "before": "**Reglas de sustitución por bioequivalentes y genéricos** para contener costos sin afectar la calidad terapéutica.",
        "after": "**Reglas diferenciadas de sustitución farmacéutica**: (a) genéricos con bioequivalencia demostrada → sustitución directa por DCI; (b) biosimilares → sustitución bajo supervisión médica con estudios de comparabilidad. Es fundamental no asimilar biosimilares a genéricos: sus vías regulatorias son sustancialmente distintas (Kirchlechner & Cohen, 2025).",
        "action": "replace",
    },
    "En la experiencia internacional en biosimilares": {
        "section": "Sección 3 (biosimilares)",
        "before": "(No se mencionaba heterogeneidad regulatoria)",
        "after": "La regulación internacional es heterogénea: la EMA permite intercambiabilidad desde 2022, la FDA requiere estudios adicionales de switching, y en Latinoamérica solo Argentina y Brasil tienen marcos regulatorios alineados a ICH (Kirchlechner & Cohen, 2025).",
        "action": "insert",
    },
    "La tabla de coberturas generales no incorpora DAC": {
        "section": "Sección 2.1 Marco Institucional",
        "before": "- **Ley Ricarte Soto**: Vigente desde 2015, financia tratamientos de alto costo para condiciones de baja prevalencia.",
        "after": "- **Ley Ricarte Soto**: Vigente desde 2015, financia tratamientos de alto costo para condiciones de baja prevalencia.\n- **DAC (Decreto de Acceso Complementario)**: Operativo desde 2019, cubre drogas oncológicas de alto costo para pacientes FONASA sin cobertura GES ni Ley Ricarte Soto. Administrado por FONASA, MINSAL (Comité DAC) y CENABAST. Presupuesto 2026: hasta $91.200 millones (MINSAL, 2026).",
        "action": "insert",
    },
    "Debiera incorporarse la judicialización": {
        "section": "Sección 2.3 (nueva)",
        "before": "(No se mencionaba judicialización en el documento)",
        "after": "### 2.3 Judicialización como Indicador de Brechas de Acceso\n\nLa judicialización evidencia fallas del sistema. Vargas-Pelaez et al. (2019): mayoría de demandas contra aseguradoras privadas. Corte Suprema (feb 2026): limitó recursos de protección para medicamentos no listados — acceso judicial individual genera discriminación.\n\nLa persistencia de la judicialización muestra que pacientes recurren a mecanismos extraordinarios, impactando sostenibilidad y equidad.",
        "action": "insert",
    },
    "Mantendría la discusión un poco más de alto": {
        "section": "Sección 1 + Sección 3",
        "before": "Chile presenta indicadores de gasto farmacéutico por debajo del promedio OCDE, aunque con una carga de bolsillo similar a la de países desarrollados.",
        "after": "*Nota metodológica: Las comparaciones internacionales requieren cautela: la proporción de gasto retail refleja la estructura institucional de cada país (convenios con farmacias, cobertura pública, copagos), no solo la equidad del sistema.*\n\nChile presenta indicadores de gasto farmacéutico por debajo del promedio OCDE...",
        "action": "insert",
    },
    "Sería mucho menos prescriptivo": {
        "section": "Sección 4 título + Sección 7 título + Sección 8 nueva",
        "before": "## 4. Propuesta: Beneficio Farmacéutico Ambulatorio Universal\n...\n## 7. Conclusiones y Recomendaciones",
        "after": "## 4. Opciones de Política: Hacia un Beneficio Farmacéutico\n(BFAU como UNA alternativa, no prescripción)\n\n## 7. Marco para la Discusión\n(Insumo para deliberación)\n\n## 8. Hacia el Seminario de Discusión\n(5 preguntas abiertas)\n\nCierre: \"EP presenta opciones como insumo para deliberación pública, no como prescripción de política.\"",
        "action": "replace",
    },
    "Sería mucho mejor cerrar el reporte": {
        "section": "Sección 8 (nueva)",
        "before": "(Documento terminaba en sección 7 con recomendaciones prescriptivas)",
        "after": "## 8. Hacia el Seminario de Discusión\n\n1. ¿Qué nivel de cobertura farmacéutica es deseable y fiscalmente sostenible?\n2. ¿Qué mecanismo de financiamiento equilibra equidad y sostenibilidad?\n3. ¿Cómo articular BFAU, GES, Ley Ricarte Soto y DAC?\n4. ¿Qué rol debe tener ETESA en la gobernanza?\n5. ¿Cómo incorporar innovación farmacéutica sin comprometer sostenibilidad?\n\nEspacio Público presenta estas opciones como insumo para la deliberación pública.",
        "action": "insert",
    },
}


def generate_diff_html(db: Session, slug: str) -> str:
    """Generate a visual diff showing each comment with its text change."""
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise ValueError(f"Document '{slug}' not found")

    comments = (
        db.query(Comment)
        .filter(Comment.document_id == doc.id, Comment.parent_id == None)  # noqa: E711
        .order_by(Comment.created_at.asc())
        .all()
    )

    changes = (
        db.query(TrackChange)
        .filter(TrackChange.document_id == doc.id)
        .order_by(TrackChange.created_at.asc())
        .all()
    )

    # Build diff cards
    diff_cards = []
    for i, comment in enumerate(comments, 1):
        # Find matching diff
        diff = None
        for prefix, d in COMMENT_DIFFS.items():
            if comment.content.startswith(prefix):
                diff = d
                break

        scope = getattr(comment, "comment_scope", "general")
        section = getattr(comment, "section", None)
        provider = {"email": "Email", "google-docs": "GDocs", "local": "Scribe"}.get(comment.provider, comment.provider)
        scope_badge = {"inline": "INLINE", "section": section or "SECCIÓN", "general": "GENERAL"}.get(scope, "")
        scope_color = {"inline": "#d97706", "section": "#3763e0", "general": "#4b5563"}.get(scope, "#4b5563")

        card = f"""<div class="diff-card">
  <div class="diff-header">
    <span class="diff-num">#{i}</span>
    <span class="diff-author">{html.escape(comment.author or 'Anon')}</span>
    <span class="diff-provider">{provider}</span>
    <span class="diff-scope" style="color:{scope_color};border-color:{scope_color}">{scope_badge}</span>
    <span class="diff-status {'resolved' if comment.resolved else 'pending'}">{'✓ Resuelto' if comment.resolved else '⏳ Pendiente'}</span>
  </div>
  <div class="diff-comment">{html.escape(comment.content)}</div>"""

        if diff:
            before_html = html.escape(diff["before"])
            after_html = html.escape(diff["after"])
            action = diff["action"]
            section_ref = diff.get("section", "")

            if action == "insert":
                card += f"""
  <div class="diff-section">📍 {html.escape(section_ref)}</div>
  <div class="diff-block">
    <div class="diff-add">
      <div class="diff-label">+ AGREGADO</div>
      <pre>{after_html}</pre>
    </div>
  </div>"""
            elif action == "delete":
                card += f"""
  <div class="diff-section">📍 {html.escape(section_ref)}</div>
  <div class="diff-block">
    <div class="diff-del">
      <div class="diff-label">− ELIMINADO</div>
      <pre>{before_html}</pre>
    </div>
  </div>"""
            elif action == "replace":
                card += f"""
  <div class="diff-section">📍 {html.escape(section_ref)}</div>
  <div class="diff-block">
    <div class="diff-del">
      <div class="diff-label">− ANTES</div>
      <pre>{before_html}</pre>
    </div>
    <div class="diff-add">
      <div class="diff-label">+ DESPUÉS</div>
      <pre>{after_html}</pre>
    </div>
  </div>"""
        else:
            # No concrete diff — editorial or minor
            if any(comment.content.startswith(p) for p in ["Reemplazar:", "Agregar:", "Eliminar:"]):
                card += f'<div class="diff-block"><div class="diff-add"><div class="diff-label">SUGERENCIA EDITORIAL</div><pre>{html.escape(comment.content)}</pre></div></div>'

        card += "</div>"
        diff_cards.append(card)

    # Stats
    resolved = sum(1 for c in comments if c.resolved)
    total = len(comments)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Diff: {html.escape(doc.title)}</title>
<style>
@page {{ size: A3 portrait; margin: 1.5cm; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'IBM Plex Sans', -apple-system, sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #0f1113;
  background: #f6f7f8;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}}
.header {{
  padding: 1.5rem 2rem;
  background: #fff;
  border-bottom: 2px solid #0f1113;
  margin-bottom: 1.5rem;
}}
.header h1 {{ font-size: 1.3rem; font-weight: 800; }}
.header .meta {{ font-size: 0.8rem; color: #4b5563; margin-top: 0.3rem; }}
.stats {{
  display: flex; gap: 2rem; padding: 1rem 2rem;
  background: #fff; margin-bottom: 1.5rem;
  border-left: 3px solid #0f1113;
}}
.stat {{ font-size: 0.85rem; }}
.stat strong {{ font-size: 1.2rem; }}

.diff-card {{
  background: #fff;
  margin-bottom: 1rem;
  border: 1px solid #d5dbe3;
  overflow: hidden;
}}
.diff-header {{
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #d5dbe3;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  background: #fafbfc;
}}
.diff-num {{ font-weight: 800; font-size: 0.85rem; }}
.diff-author {{ font-weight: 600; font-size: 0.8rem; }}
.diff-provider {{ font-size: 0.65rem; text-transform: uppercase; color: #4b5563; letter-spacing: 0.04em; }}
.diff-scope {{
  font-size: 0.6rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.04em; padding: 0.1rem 0.4rem;
  border: 1px solid;
}}
.diff-status {{ margin-left: auto; font-size: 0.7rem; }}
.diff-status.resolved {{ color: #0b7e59; }}
.diff-status.pending {{ color: #d97706; }}
.diff-comment {{
  padding: 0.8rem 1rem;
  font-size: 0.85rem;
  line-height: 1.6;
  color: #0f1113;
  border-bottom: 1px solid #e5e7eb;
}}
.diff-section {{
  padding: 0.4rem 1rem;
  font-size: 0.75rem;
  color: #3763e0;
  font-weight: 600;
  background: #f0f4ff;
}}
.diff-block {{
  padding: 0;
}}
.diff-del {{
  background: #fef2f2;
  border-left: 3px solid #c0352b;
  padding: 0.6rem 1rem;
}}
.diff-add {{
  background: #f0fdf4;
  border-left: 3px solid #0b7e59;
  padding: 0.6rem 1rem;
}}
.diff-label {{
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.3rem;
}}
.diff-del .diff-label {{ color: #c0352b; }}
.diff-add .diff-label {{ color: #0b7e59; }}
pre {{
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.8rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}}
.links {{
  padding: 1rem 2rem;
  background: #fff;
  margin-top: 1rem;
  font-size: 0.85rem;
}}
a {{ color: #3763e0; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<div class="header">
  <h1>{html.escape(doc.title)}</h1>
  <div class="meta">
    Espacio Público · Diff de revisión · {datetime.now().strftime('%d/%m/%Y %H:%M')}
  </div>
</div>

<div class="stats">
  <div class="stat"><strong>{total}</strong> comentarios</div>
  <div class="stat"><strong>{resolved}</strong> resueltos</div>
  <div class="stat"><strong>{len(changes)}</strong> cambios propuestos</div>
</div>

{''.join(diff_cards)}

<div class="links">
  <a href="https://scribe.illanes00.cl/editor/{slug}">Ver en Scribe</a>
  · <a href="/api/v1/review/{slug}/export">Ver exportación completa (A3)</a>
  {f'· <a href="https://docs.google.com/document/d/{doc.source_id}/edit">Google Doc</a>' if doc.source_id else ''}
</div>

</body>
</html>"""
