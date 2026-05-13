"""Populate workspace Google Doc with REAL formatting + tables + design system.

Design goals:
    - Clean visual hierarchy with intentional spacing
    - Real tables (not text) for structured data
    - Callouts with background colors for highlights
    - Page breaks between major sections
    - Links clickable
    - Consistent body font and line height

Usage:
    cd /srv/projects/cochid/cochid-scribe/backend
    source .venv/bin/activate
    python scripts/populate_workspace_doc_v2.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_docs_service

WORKSPACE_DOC_ID = "1jd6-dk3t_3qZ2sLEc5Ol4Y36okJwKBojrJRbfvA4fBM"


# ── Design system colors (RGB 0-1) ─────────────────────────────

COLOR_INK = {"red": 0.059, "green": 0.067, "blue": 0.075}
COLOR_MUTED = {"red": 0.29, "green": 0.33, "blue": 0.39}
COLOR_MUTED_LIGHT = {"red": 0.42, "green": 0.45, "blue": 0.50}
COLOR_BLUE = {"red": 0.122, "green": 0.306, "blue": 0.847}
COLOR_GREEN = {"red": 0.043, "green": 0.494, "blue": 0.349}
COLOR_AMBER = {"red": 0.851, "green": 0.463, "blue": 0.024}
COLOR_RED = {"red": 0.753, "green": 0.208, "blue": 0.169}
COLOR_BG_YELLOW = {"red": 1.0, "green": 0.976, "blue": 0.769}
COLOR_BG_BLUE = {"red": 0.937, "green": 0.965, "blue": 1.0}
COLOR_BG_GREEN = {"red": 0.933, "green": 0.98, "blue": 0.953}
COLOR_BG_GRAY = {"red": 0.953, "green": 0.957, "blue": 0.961}

FONT_BODY = "IBM Plex Sans"
FONT_MONO = "JetBrains Mono"


# ── Helper functions ───────────────────────────────────────────


def get_doc_end_index(docs, doc_id: str) -> int:
    doc = docs.documents().get(documentId=doc_id).execute()
    end = 1
    for el in doc.get("body", {}).get("content", []):
        if "endIndex" in el:
            end = max(end, el["endIndex"])
    return end


def clear_doc(docs, doc_id: str) -> None:
    end = get_doc_end_index(docs, doc_id)
    if end > 2:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [
                {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}
            ]}
        ).execute()


def apply_requests(docs, doc_id: str, requests: list, label: str = "") -> None:
    """Apply a batch of requests, splitting into chunks if large."""
    if not requests:
        return
    chunk = 80
    for i in range(0, len(requests), chunk):
        batch = requests[i:i + chunk]
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": batch}
        ).execute()
    if label:
        print(f"  ✓ {label}: {len(requests)} requests applied")


# ── Writer: accumulates content with format operations ─────────


class DocWriter:
    """Builds insert+style requests with proper index tracking."""

    def __init__(self):
        self.pos = 1
        self.text_requests: list[dict] = []
        self.style_requests: list[dict] = []
        # Tables are inserted later via a second pass
        self.table_placeholders: list[dict] = []

    # ── Low-level text insertion ──

    def _insert(self, text: str) -> tuple[int, int]:
        """Insert text at current position. Returns (start, end) of inserted text."""
        start = self.pos
        self.text_requests.append({
            "insertText": {
                "location": {"index": start},
                "text": text
            }
        })
        self.pos += len(text)
        return (start, self.pos)

    def _text_style(self, start: int, end: int, style: dict, fields: list[str]) -> None:
        if start >= end:
            return
        self.style_requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "textStyle": style,
                "fields": ",".join(fields)
            }
        })

    def _paragraph_style(self, start: int, end: int, style: dict, fields: list[str]) -> None:
        self.style_requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": style,
                "fields": ",".join(fields)
            }
        })

    # ── Block-level helpers ──

    def title(self, text: str) -> None:
        """Big title — 24pt bold black, tight line spacing, stays with next block."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "TITLE",
                "alignment": "START",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                "lineSpacing": 110,
                "keepWithNext": True,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "alignment", "spaceAbove", "spaceBelow",
             "lineSpacing", "keepWithNext", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 24, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "bold", "foregroundColor"]
        )

    def subtitle(self, text: str) -> None:
        """Subtitle under title — 14pt regular muted, tight leading."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "SUBTITLE",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
                "lineSpacing": 115,
                "keepWithNext": True,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing",
             "keepWithNext", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 14, "unit": "PT"},
                "bold": False,
                "italic": False,
                "foregroundColor": {"color": {"rgbColor": COLOR_MUTED}},
            },
            ["weightedFontFamily", "fontSize", "bold", "italic", "foregroundColor"]
        )

    def meta(self, text: str) -> None:
        """Metadata line — 10pt light gray, single line spacing."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 2, "unit": "PT"},
                "lineSpacing": 115,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 10, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": COLOR_MUTED_LIGHT}},
            },
            ["weightedFontFamily", "fontSize", "foregroundColor"]
        )

    def h2(self, text: str, color: dict | None = None) -> None:
        """Section heading — 16pt bold, colored, tight leading, stays with next."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "HEADING_2",
                "spaceAbove": {"magnitude": 18, "unit": "PT"},
                "spaceBelow": {"magnitude": 10, "unit": "PT"},
                "lineSpacing": 115,
                "keepWithNext": True,
                "keepLinesTogether": True,
                "borderBottom": {
                    "width": {"magnitude": 1, "unit": "PT"},
                    "padding": {"magnitude": 4, "unit": "PT"},
                    "color": {"color": {"rgbColor": {"red": 0.85, "green": 0.87, "blue": 0.91}}},
                    "dashStyle": "SOLID",
                },
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing",
             "keepWithNext", "keepLinesTogether", "borderBottom"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 16, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": color or COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "bold", "foregroundColor"]
        )

    def h3(self, text: str) -> None:
        """Subsection — 13pt bold black, tight leading, stays with next."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "HEADING_3",
                "spaceAbove": {"magnitude": 16, "unit": "PT"},
                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                "lineSpacing": 115,
                "keepWithNext": True,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing",
             "keepWithNext", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 13, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "bold", "foregroundColor"]
        )

    def h4(self, text: str) -> None:
        """Small heading — 11pt bold, single leading, stays with next."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "HEADING_4",
                "spaceAbove": {"magnitude": 12, "unit": "PT"},
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
                "lineSpacing": 115,
                "keepWithNext": True,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing",
             "keepWithNext", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 11, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "bold", "foregroundColor"]
        )

    def p(self, text: str, *, bold_ranges: list[tuple[int, int]] | None = None,
          italic: bool = False, muted: bool = False, size: int = 11) -> None:
        """Paragraph — 11pt regular, comfortable leading, kept together."""
        start, end = self._insert(text + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
                "lineSpacing": 140,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": size, "unit": "PT"},
                "italic": italic,
                "bold": False,
                "foregroundColor": {"color": {"rgbColor": COLOR_MUTED if muted else COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "italic", "bold", "foregroundColor"]
        )
        if bold_ranges:
            for b_start, b_end in bold_ranges:
                self._text_style(
                    start + b_start, start + b_end,
                    {"bold": True},
                    ["bold"]
                )

    def bullet(self, text: str, *, bold_prefix: str | None = None) -> None:
        """Bullet item — 11pt regular with disc marker, kept together on page."""
        full = text
        if bold_prefix:
            full = f"{bold_prefix}: {text}"
        start, end = self._insert(full + "\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
                "lineSpacing": 135,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing", "keepLinesTogether"]
        )
        self._text_style(
            start, end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 11, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": COLOR_INK}},
            },
            ["weightedFontFamily", "fontSize", "foregroundColor"]
        )
        if bold_prefix:
            self._text_style(
                start, start + len(bold_prefix) + 1,  # include the colon
                {"bold": True},
                ["bold"]
            )
        # Apply bullet
        self.style_requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

    def callout(self, heading: str, body: str, variant: str = "blue") -> None:
        """Callout box with colored background and left border."""
        bg = {
            "blue": COLOR_BG_BLUE,
            "yellow": COLOR_BG_YELLOW,
            "green": COLOR_BG_GREEN,
            "gray": COLOR_BG_GRAY,
        }.get(variant, COLOR_BG_BLUE)
        border_color = {
            "blue": COLOR_BLUE,
            "yellow": COLOR_AMBER,
            "green": COLOR_GREEN,
            "gray": COLOR_MUTED,
        }.get(variant, COLOR_BLUE)

        # Heading line — keeps with body below
        h_start, h_end = self._insert(heading + "\n")
        self._paragraph_style(
            h_start, h_end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 10, "unit": "PT"},
                "spaceBelow": {"magnitude": 2, "unit": "PT"},
                "lineSpacing": 120,
                "keepWithNext": True,
                "keepLinesTogether": True,
                "shading": {"backgroundColor": {"color": {"rgbColor": bg}}},
                "borderLeft": {
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 10, "unit": "PT"},
                    "color": {"color": {"rgbColor": border_color}},
                    "dashStyle": "SOLID",
                },
                "indentFirstLine": {"magnitude": 12, "unit": "PT"},
                "indentStart": {"magnitude": 12, "unit": "PT"},
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "lineSpacing",
             "keepWithNext", "keepLinesTogether", "shading", "borderLeft",
             "indentFirstLine", "indentStart"]
        )
        self._text_style(
            h_start, h_end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 11, "unit": "PT"},
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": border_color}},
            },
            ["weightedFontFamily", "fontSize", "bold", "foregroundColor"]
        )
        # Body — avoids breaking mid-paragraph
        b_start, b_end = self._insert(body + "\n")
        self._paragraph_style(
            b_start, b_end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 10, "unit": "PT"},
                "shading": {"backgroundColor": {"color": {"rgbColor": bg}}},
                "borderLeft": {
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 10, "unit": "PT"},
                    "color": {"color": {"rgbColor": border_color}},
                    "dashStyle": "SOLID",
                },
                "indentFirstLine": {"magnitude": 12, "unit": "PT"},
                "indentStart": {"magnitude": 12, "unit": "PT"},
                "lineSpacing": 135,
                "keepLinesTogether": True,
            },
            ["namedStyleType", "spaceAbove", "spaceBelow", "shading", "borderLeft",
             "indentFirstLine", "indentStart", "lineSpacing", "keepLinesTogether"]
        )
        self._text_style(
            b_start, b_end - 1,
            {
                "weightedFontFamily": {"fontFamily": FONT_BODY},
                "fontSize": {"magnitude": 11, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": COLOR_INK}},
                "bold": False,
                "italic": False,
            },
            ["weightedFontFamily", "fontSize", "foregroundColor", "bold", "italic"]
        )

    def page_break(self) -> None:
        self.text_requests.append({
            "insertPageBreak": {"location": {"index": self.pos}}
        })
        self.pos += 1

    def blank(self) -> None:
        """Empty line for breathing room."""
        start, end = self._insert("\n")
        self._paragraph_style(
            start, end,
            {
                "namedStyleType": "NORMAL_TEXT",
                "spaceAbove": {"magnitude": 0, "unit": "PT"},
                "spaceBelow": {"magnitude": 0, "unit": "PT"},
            },
            ["namedStyleType", "spaceAbove", "spaceBelow"]
        )

    def register_table(self, rows: list[list[str]], headers: list[str] | None = None,
                       caption: str | None = None) -> None:
        """Mark a position for a table. Actual insertion happens in a second pass."""
        # Insert placeholder text that we'll replace
        marker = f"[[TABLE_{len(self.table_placeholders)}]]\n"
        start, end = self._insert(marker)
        self.table_placeholders.append({
            "marker_start": start,
            "marker_end": end,
            "marker_text": marker,
            "rows": rows,
            "headers": headers,
            "caption": caption,
        })

    def get_all_requests(self) -> list[dict]:
        return self.text_requests + self.style_requests


# ── Content builder ────────────────────────────────────────────


def build_workspace_content(writer: DocWriter) -> None:
    now = datetime.now().strftime('%d de %B de %Y — %H:%M')

    # ════════════════ PÁGINA 1: PORTADA Y PLAN ════════════════

    writer.title("Workspace Revisión Medicamentos")
    writer.subtitle("CIF-EP — Inclusión sostenible de medicamentos en los planes de salud en Chile")
    writer.meta(f"Última actualización: {now}")
    writer.meta("Mantenedor: Martín Illanes (martin.illanes@espaciopublico.cl)")
    writer.meta("Documento privado · workspace interno de trabajo")
    writer.blank()

    writer.h2("0. Plan de trabajo y estado", color=COLOR_BLUE)

    writer.h3("Entregables comprometidos")

    writer.callout(
        "Entregable 1 — Consolidado de comentarios y verificación de datos",
        "Fecha objetivo: lunes 13 o martes 14 de abril. Para Benja → Eduardo y Carla. "
        "Contenido: tabla de los 45 items consolidados + tabla de datos verificados con discrepancias resueltas. "
        "Sin decisiones de respuesta — esa fase queda para que los directores puedan meter mano si quieren acelerar.",
        variant="blue"
    )

    writer.callout(
        "Entregable 2 — Versión final del informe revisado",
        "Fecha objetivo: semana del 4 de mayo. Puede adelantarse si los directores aportan en la fase de respuestas. "
        "Para Benja → CIF. Contenido: documento reescrito con todas las decisiones aplicadas, "
        "comentarios respondidos directamente en el Google Doc original, bibliografía completa.",
        variant="blue"
    )

    writer.h3("Etapas del plan")

    writer.h4("Fase A — Procesamiento y respuestas")
    writer.bullet("Diagnóstico y estrategia editorial — HECHA", bold_prefix="Etapa 1")
    writer.bullet("Centralizar feedback (inventario puro) — EN CURSO", bold_prefix="Etapa 2")
    writer.bullet("Verificación de datos críticos — EN CURSO", bold_prefix="Etapa 3")
    writer.bullet("Decidir respuestas (colaborativa o solo) — pendiente", bold_prefix="Etapa 4")
    writer.bullet("Documento de respuestas + 3 muestras de prosa — pendiente", bold_prefix="Etapa 5")

    writer.h4("Fase B — Reescritura e integración")
    writer.bullet("Reescritura sustantiva de secciones — pendiente", bold_prefix="Etapa 6")
    writer.bullet("Trasladar todo al Google Doc real con suggesting mode — pendiente", bold_prefix="Etapa 7")
    writer.bullet("Cargar respuestas en threads de comentarios del GDoc — pendiente", bold_prefix="Etapa 8")
    writer.bullet("Pase final de coherencia — pendiente", bold_prefix="Etapa 9")
    writer.bullet("Entrega final a Benja — pendiente", bold_prefix="Etapa 10")

    writer.page_break()

    # ════════════════ PÁGINA 2: INVENTARIO ════════════════

    writer.h2("1. Inventario consolidado de comentarios", color=COLOR_BLUE)

    writer.p(
        "Este inventario consolida todo el feedback recibido en una sola lista, "
        "agrupado por revisor y sección del informe afectada. Aún no incluye decisiones de respuesta "
        "— esa fase es la siguiente. Si Eduardo o Carla quieren tomar comentarios específicos y proponer "
        "respuesta directamente, este es el momento de hacerlo."
    )

    writer.h3("Resumen numérico")

    writer.register_table(
        headers=["Revisor", "Fuente", "Items"],
        rows=[
            ["Francisca Rodríguez (CIF)", "Email del 18 marzo", "14"],
            ["Eduardo Undurraga (Director)", "Email del 30 marzo", "2"],
            ["Eduardo Undurraga", "Comentarios en Google Doc (26-27 enero)", "8"],
            ["Eduardo Undurraga", "Sugerencias de redacción en Google Doc", "20"],
            ["Carla Castillo (Directora)", "Email del 30 marzo", "1"],
            ["Carla Castillo", "Docx adjunto con track changes", "pendiente"],
            ["TOTAL consolidado", "—", "45"],
        ],
    )

    writer.h3("CIF — Francisca Rodríguez (14 items)")

    writer.h4("Sobre el Marco Institucional (sección 2.1)")
    writer.bullet(
        "La tabla de coberturas generales no incorpora DAC, pese a que este instrumento formaba parte de los componentes "
        "que se solicitó considerar para reflejar adecuadamente la fragmentación del sistema chileno. "
        "Su omisión debilita la representación completa del esquema vigente.",
        bold_prefix="#1"
    )

    writer.h4("Sobre las Dos Dimensiones del desafío (sección 2.2)")
    writer.bullet(
        "Se incorpora la brecha de cobertura en medicamentos ambulatorios, pero no desarrolla con la misma fuerza "
        "el problema de patologías complejas y de alto costo, ni la experiencia concreta de exclusión que enfrentan "
        "pacientes y familias cuando el sistema no cubre un tratamiento.",
        bold_prefix="#2"
    )

    writer.h4("Sobre la Judicialización (nueva sección 2.3)")
    writer.bullet(
        "Debiera incorporarse la judicialización como síntoma de falla institucional de acceso y no solo como "
        "fenómeno lateral. Este punto es clave para mostrar que, en ausencia de beneficios explícitos suficientes, "
        "se recurren a mecanismos extraordinarios para obtener cobertura que impactan en la sostenibilidad del sistema.",
        bold_prefix="#3"
    )

    writer.h4("Sobre la Comparación Internacional (sección 3)")
    writer.bullet(
        "Mezcla diagnóstico, comparación internacional y propuestas normativas sin separar con suficiente claridad "
        "la evidencia, la interpretación y la recomendación.",
        bold_prefix="#4"
    )
    writer.bullet(
        "Explicar con mayor precisión cómo se seleccionaron los países de la comparación internacional, "
        "qué años base se utilizaron para cada indicador, cuáles fueron las fuentes empleadas y qué limitaciones "
        "tienen las extrapolaciones realizadas al caso chileno.",
        bold_prefix="#5"
    )
    writer.bullet(
        "Se tiende a asimilar biosimilares a genéricos en materia de intercambiabilidad, prescripción por DCI, "
        "sustitución y preferencia por menor precio.",
        bold_prefix="#6"
    )
    writer.bullet(
        "En la experiencia internacional en biosimilares no existe un estándar único, por lo que el estudio "
        "debiera reflejar esa heterogeneidad regulatoria.",
        bold_prefix="#7"
    )

    writer.h4("Sobre Innovación con Valor (nueva sección 3.1)")
    writer.bullet(
        "Se debieran incorporar con mayor claridad ejemplos de innovación que generen valor sanitario y ahorro futuro, "
        "de modo de evitar que la agenda propositiva quede leída únicamente desde la lógica de contención de precios.",
        bold_prefix="#8"
    )

    writer.h4("Sobre las Opciones de Política (sección 4)")
    writer.bullet(
        "Ordenar claramente qué medidas podrían implementarse sin reforma legal mayor, cuáles requieren ajustes "
        "regulatorios o institucionales y cuáles suponen rediseños sistémicos del aseguramiento.",
        bold_prefix="#9"
    )

    writer.h4("Sobre los Requisitos Institucionales (sección 6)")
    writer.bullet(
        "Reforzar que el objetivo de ETESA no es contener el gasto y que se debiera avanzar a una priorización "
        "basada en valor sanitario, social y económico.",
        bold_prefix="#10"
    )

    writer.h4("Sobre el Marco para la Discusión (sección 7)")
    writer.bullet(
        "Hay secciones que no parecen cerradas, problemas de orden y la conclusión requiere mayor análisis.",
        bold_prefix="#11"
    )

    writer.h4("Sobre Tablas y figuras (generales)")
    writer.bullet(
        "Problemas de numeración de tablas y subtítulos, además de inconsistencias en algunas cifras y formulaciones.",
        bold_prefix="#12"
    )

    writer.h4("Sobre el Resumen Ejecutivo")
    writer.bullet(
        "El estudio parece borrador avanzado más que una versión final cerrada.",
        bold_prefix="#13"
    )
    writer.bullet(
        "La incorporación de las observaciones formuladas en la minuta previa fue parcial, ya que varios "
        "comentarios centrales para CIF no quedaron desarrollados con la fuerza esperada.",
        bold_prefix="#14"
    )

    writer.h3("Directores — Eduardo Undurraga (2 items por email)")

    writer.bullet(
        "Mantendría la discusión un poco más de alto vuelo. Le bajaría el tono a la parte de gastos de retail "
        "que pagan las familias, porque es algo relativamente micro y depende mucho del arreglo institucional. "
        "La comparación con UK no es tan directa porque allá el NHS tiene convenios con el retail. "
        "Lo mismo con el énfasis en la Ricarte Soto, que es sólo una forma de cobertura entre muchas otras.",
        bold_prefix="#15"
    )
    writer.bullet(
        "Sería mucho menos prescriptivo en el informe. EP no puede jugarse en una solución sino que nuestro rol "
        "es mostrar evidencia y datos, y los policymakers deben buscar qué es la mejor solución. A Carla se le "
        "ocurrió cerrar el reporte con un capítulo sobre conclusiones generales del seminario de discusión. "
        "Dejamos como blueprint general de problema y potenciales soluciones, pero sin alinearnos con ninguna.",
        bold_prefix="#16"
    )

    writer.h3("Directores — Carla Castillo (1 item por email)")

    writer.bullet(
        "Sería mucho mejor cerrar el reporte con un capítulo sobre conclusiones generales del seminario de discusión, "
        "donde podremos analizar y conversar sobre las alternativas de políticas pública para avanzar en este problema. "
        "Los cambios y sugerencias específicas están en el documento adjunto con track changes.",
        bold_prefix="#17"
    )

    writer.h3("Eduardo Undurraga — Comentarios en el Google Doc (8 items, 26-27 enero)")

    writer.bullet('"Diciembre de 2025" — supongo que enero 2026', bold_prefix="#18")
    writer.bullet('En general no se usan subcategorías cuando es solo 1 (sobre sección "Cómo op...")', bold_prefix="#19")
    writer.bullet('Sección 6.1 — acá tampoco, es solo otro párrafo (no necesita subsección)', bold_prefix="#20")
    writer.bullet('Sección 2.1 — no se usa otra subsección cuando es solo 1', bold_prefix="#21")
    writer.bullet('Tabla 1 — tamaño 11 como lo anterior (formato inconsistente)', bold_prefix="#22")
    writer.bullet('"en el canal retail" — jargon, evitar lenguaje técnico de industria', bold_prefix="#23")
    writer.bullet('En el cuadro resumen, sería útil indicar en qué capítulo o sección se profundiza el tema, para facilitar acceso de lectores', bold_prefix="#24")
    writer.bullet('"en el canal de" — mejor evitar jargon', bold_prefix="#25")

    writer.h3("Eduardo Undurraga — Sugerencias de redacción en el Google Doc (20 items)")

    writer.p(
        "Estas son ediciones de texto específicas. La mayoría son cambios menores de ortografía, artículos "
        "o convenciones académicas. Se listan abreviadas; los cambios sustantivos están marcados con 📝.",
        muted=True, size=10
    )

    suggestions = [
        ('Reemplazar: "u" → "ú" (corrección ortográfica)', False),
        ('Agregar: "la" (artículo faltante)', False),
        ('Agregar: "los" (artículo faltante)', False),
        ('Eliminar: "," (coma innecesaria)', False),
        ('Agregar: "de ajuste" (precisión conceptual)', False),
        ('Reemplazar: "p. ej." → "e.g." (convención académica)', False),
        ('Reemplazar: "y gobernada" → "e informada" (mejora de redacción)', False),
        ('📝 Reemplazar: "muestra" → "comparada sugiere" (más cauteloso)', True),
        ('📝 Agregar párrafo: "Ambos frentes responden a lógicas distintas de riesgo financiero y requieren instrumentos diferenciados..."', True),
        ('Agregar: "y coordinada" (sobre implementación)', False),
        ('📝 Agregar párrafo: "La efectividad de estos instrumentos depende de su implementación conjunta..."', True),
        ('📝 Reemplazar: "cluster intermedio" → "conjunto de países OCDE de protección farmacéutica intermedia" (evitar jargon)', True),
        ('Agregar: "con foco prioritario en medicamentos" (precisión)', False),
        ('📝 Reemplazar: "experiencia" → "evidencia" (más riguroso)', True),
        ('📝 Agregar: ", por brechas de canasta" (concepto faltante)', True),
        ('📝 Eliminar párrafo (contenido redundante)', True),
        ('📝 Agregar: "informada por evidencia," (calificador importante)', True),
        ('📝 Reemplazar: "precios más accesibles" → "reducciones del precio efectivo enfrentado por el paciente" (más preciso)', True),
        ('📝 Reemplazar: "sostienen el" → "explican una fracción sustantiva del" (más cauteloso)', True),
        ('📝 Reemplazar: "cotidiano" → "persistente" (más preciso)', True),
    ]

    for idx, (text, substantive) in enumerate(suggestions, start=26):
        writer.bullet(text, bold_prefix=f"#{idx}")

    writer.page_break()

    # ════════════════ PÁGINA 3: VERIFICACIÓN DE DATOS ════════════════

    writer.h2("2. Verificación de datos críticos", color=COLOR_BLUE)

    writer.p(
        "Primer pase de verificación contra fuentes originales del proyecto "
        "illanes00-cif (archivado). Los datos críticos que sustentan argumentos centrales del informe "
        "se chequearon y se identificaron discrepancias que deben corregirse antes de la reescritura."
    )

    writer.h3("Resumen de hallazgos")

    writer.register_table(
        headers=["Dato citado", "En el informe", "Verificado", "Acción"],
        rows=[
            ["Gasto meds per cápita Chile", "US$206 PPA", "US$206 corrientes 2022 (OMS GHED)", "Corregir cita: fuente y unidad"],
            ["Mediana OCDE per cápita", "~US$600 PPA", "~US$550 (16 países OCDE)", "Recalcular y corregir"],
            ["Carga Q1 sobre ingreso", "9.8%", "9.84% (EPF cálculo propio)", "Mantener"],
            ["Carga Q5 sobre ingreso", "1.9%", "1.90% (EPF cálculo propio)", "Mantener"],
            ["Incidencia Q1", "37.5%", "37.52%", "Mantener"],
            ["Incidencia Q5", "63.6%", "63.65%", "Mantener"],
            ["Gasto bolsillo en farmacias", "71%", "No reproducido", "⚠ Reproducir o explicitar metodología"],
            ["GES patologías", "87", "90 (Decreto 2025-2028)", "Actualizar"],
            ["Costa Rica CCSS cobertura", "~95%", "91-93% (estimación)", "Verificar y corregir"],
            ["FONASA cobertura", "~80% población", "Pendiente verificar", "Pendiente"],
        ],
    )

    writer.h3("Hallazgos detallados")

    writer.callout(
        "⚠ Sobre el dato US$206 PPA — la cita está mal, el dato es correcto",
        "El valor de US$206 existe y está confirmado en el proyecto illanes00-cif "
        "(outputs/pharma_profile_detail.md). Pero la cita actual del informe está mal en TRES dimensiones:\n"
        "  (1) Fuente: no es OECD Health at a Glance, es GHED de OMS\n"
        "  (2) Unidad: no es PPA, es US$ corrientes del año 2022\n"
        "  (3) Año del dato: no es 2025, es 2022\n"
        "Acción: reescribir la cita corrigiendo atribución, unidad y año. No hay que eliminar el dato.",
        variant="yellow"
    )

    writer.callout(
        "⚠ Sobre la mediana OCDE de US$600 — probablemente incorrecto",
        "El dataset original tiene 22 países, de los cuales 16 son OCDE. Calculando la mediana sobre esos 16: "
        "~US$550. La cifra de US$600 del informe parece ser una estimación a ojo o un redondeo incorrecto. "
        "Acción: recalcular con los valores exactos del dataset y corregir la cifra en la prosa.",
        variant="yellow"
    )

    writer.callout(
        "⚠ Sobre el 71% de gasto de bolsillo en farmacias — el dato más expuesto",
        "Esta es la discrepancia más sensible. Cálculos simples no reproducen el 71% "
        "(US$80 bolsillo / US$206 total = 39%). El informe cita \"INE EPF 2022-2023, Cuadro 8.1, cálculo del autor\". "
        "Para defender este número ante CIF hay dos opciones: (1) ejecutar el script app.py del proyecto illanes00-cif "
        "para reproducir la metodología exacta, o (2) explicitar en una nota metodológica cómo se calculó. "
        "Sin eso, si CIF lo chequea, encontramos problemas.",
        variant="yellow"
    )

    writer.h3("Tabla de 22 países del dataset OECD (fuente: illanes00-cif)")

    writer.register_table(
        headers=["País", "Gasto meds pc (USD 2022)", "Bolsillo pc (USD corr)", "Meds % PIB", "Año"],
        rows=[
            ["Switzerland", "$1,302", "$281", "1.39%", "2022"],
            ["Canada", "$921", "$138", "1.66%", "2023"],
            ["Germany", "$839", "$95", "1.71%", "2022"],
            ["Australia", "$772", "$115", "1.16%", "2021"],
            ["Japan", "$667", "$76", "1.99%", "2021"],
            ["France", "$629", "$56", "1.54%", "2022"],
            ["Norway", "$620", "$87", "0.57%", "2022"],
            ["Israel", "$593", "$120", "1.08%", "2021"],
            ["Sweden", "$567", "$74", "1.00%", "2022"],
            ["South Korea", "$533", "$163", "1.62%", "2023"],
            ["Denmark", "$496", "$68", "0.72%", "2023"],
            ["United Kingdom", "$485", "$71", "1.06%", "2022"],
            ["Spain", "$424", "$81", "1.42%", "2022"],
            ["Netherlands", "$404", "$40", "0.70%", "2022"],
            ["Chile", "$206", "$80", "1.34%", "2022"],
            ["Brazil", "$158", "$42", "1.75%", "2019"],
            ["Mexico", "$136", "$53", "1.20%", "2022"],
            ["Uruguay", "$104", "$17", "0.50%", "2022"],
            ["Costa Rica", "$90", "$20", "0.66%", "2022"],
        ],
    )

    writer.p(
        "Mediana de los 16 países OCDE de la lista: aproximadamente US$550 (entre Sweden US$567 y South Korea US$533). "
        "El promedio es US$610. El dato citado en el informe de US$600 está más cerca del promedio que de la mediana.",
        muted=True
    )

    writer.page_break()

    # ════════════════ PÁGINA 4: DECISIONES (PLACEHOLDER) ════════════════

    writer.h2("3. Decisiones de respuesta", color=COLOR_MUTED)

    writer.p(
        "Esta sección se llenará en la Etapa 4 con la decisión específica para cada comentario. "
        "Cada decisión puede ser:",
        italic=True, muted=True
    )
    writer.bullet("Aceptar, con cambio concreto en el documento original")
    writer.bullet("Rechazar, con argumento basado en evidencia")
    writer.bullet("Parcial, explicitando qué se acepta y qué no")

    writer.callout(
        "Nota para Eduardo y Carla",
        "Si quieren tomar comentarios específicos y proponer respuesta directamente desde su lado, "
        "este es el momento de hacerlo. Pueden indicar el número del comentario y enviarme su propuesta. "
        "Eso ahorra tiempo de mi lado y nos permite adelantar el cierre de la versión final.",
        variant="green"
    )

    writer.page_break()

    # ════════════════ PÁGINA 5: BORRADORES (PLACEHOLDER) ════════════════

    writer.h2("4. Borradores de prosa reescrita", color=COLOR_MUTED)

    writer.p(
        "Esta sección se llenará en la Etapa 6 con borradores de las secciones que requieren "
        "reescritura sustantiva. Son los cambios más pesados del informe:",
        italic=True, muted=True
    )
    writer.bullet("Sección 4 — Renombre a \"Opciones de Política\" y reescritura del contenido")
    writer.bullet("Sección 7 — Renombre a \"Marco para la Discusión\" y reescritura")
    writer.bullet("Resumen Ejecutivo — Alineación con el nuevo framing (hoy sigue diciendo \"propone el BFAU\")")
    writer.bullet("Sección 2.1 — Agregar DAC al marco institucional")
    writer.bullet("Sección 2.3 — Nueva, sobre Judicialización")
    writer.bullet("Sección 3 — Separar biosimilares de genéricos, ETESA reorientada, nota metodológica")
    writer.bullet("Nueva sección — Innovación con valor sanitario")

    writer.page_break()

    # ════════════════ PÁGINA 6: NOTAS Y DUDAS ════════════════

    writer.h2("5. Notas y dudas", color=COLOR_BLUE)

    writer.h3("Preguntas abiertas")

    writer.bullet("¿Dónde está exactamente la minuta previa de CIF con las observaciones que Francisca dice que quedaron \"parcialmente incorporadas\"? Sin esa minuta no puedo hacer tracking de lo que faltaría agregar.")
    writer.bullet("¿Eduardo y Carla van a poder dedicar tiempo a la fase de respuestas la semana del 13, o esperan recibir la versión con decisiones ya tomadas?")
    writer.bullet("¿Benja quiere ver el workspace mientras avanzo, o prefiere recibir los entregables ya cerrados?")

    writer.h3("Riesgos identificados")

    writer.bullet(
        "El cálculo del 71% es el punto más vulnerable ante revisión técnica de CIF. Si no logro reproducirlo, "
        "hay que elegir entre explicitar metodología o bajar el tono de la afirmación.",
        bold_prefix="Alto"
    )
    writer.bullet(
        "El docx de Carla con track changes no ha sido procesado. Puede contener cambios que afecten cómo "
        "responder los comentarios de CIF.",
        bold_prefix="Medio"
    )
    writer.bullet(
        "La fecha del 4 de mayo asume que Eduardo y Carla dan feedback rápido sobre el Entregable 1. "
        "Si demoran, se corre la fecha final.",
        bold_prefix="Medio"
    )

    writer.page_break()

    # ════════════════ PÁGINA 7: LINKS ════════════════

    writer.h2("Links de trabajo", color=COLOR_BLUE)

    writer.bullet("Informe original en Google Docs — docs.google.com/document/d/1ZuaOF9IvZA61B_ZbU6DWuR2uEcMjI6guruLESRuUuxI/edit", bold_prefix="Informe CIF-EP")
    writer.bullet("scribe.illanes00.cl/editor/cif-medicamentos", bold_prefix="Scribe (revisión interna)")
    writer.bullet("/srv/projects/archives/illanes00-cif (servidor interno)", bold_prefix="Datos crudos")
    writer.bullet("/srv/projects/cochid/cochid-scribe/docs/cif-review/ (servidor interno)", bold_prefix="Archivos de workspace")


# ── Table insertion: SECOND PASS ───────────────────────────────


def insert_tables_second_pass(docs, doc_id: str, placeholders: list[dict]) -> None:
    """After the main text is inserted, replace each [[TABLE_N]] marker with
    a real Google Docs table populated with its rows."""
    # Process in REVERSE order so indices of earlier markers don't shift
    for i in range(len(placeholders) - 1, -1, -1):
        ph = placeholders[i]
        rows = ph["rows"]
        headers = ph.get("headers")
        caption = ph.get("caption")

        # Re-fetch doc to find the current position of the marker
        doc = docs.documents().get(documentId=doc_id).execute()
        marker_text = ph["marker_text"].strip()

        marker_start = None
        marker_end = None
        for element in doc.get("body", {}).get("content", []):
            para = element.get("paragraph")
            if not para:
                continue
            for run in para.get("elements", []):
                text_run = run.get("textRun")
                if not text_run:
                    continue
                content = text_run.get("content", "")
                if marker_text in content:
                    local_start = content.index(marker_text)
                    marker_start = run["startIndex"] + local_start
                    marker_end = marker_start + len(marker_text)
                    break
            if marker_start is not None:
                break

        if marker_start is None:
            print(f"  ⚠ Marker {i} not found in doc, skipping table")
            continue

        total_rows = len(rows) + (1 if headers else 0)
        total_cols = len(rows[0]) if rows else (len(headers) if headers else 1)

        # Step 1: delete marker + insert empty table at that position
        delete_and_insert = [
            {
                "deleteContentRange": {
                    "range": {"startIndex": marker_start, "endIndex": marker_end}
                }
            },
            {
                "insertTable": {
                    "location": {"index": marker_start},
                    "rows": total_rows,
                    "columns": total_cols,
                }
            }
        ]
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": delete_and_insert}).execute()

        # Step 2: re-fetch doc and find the cell positions
        doc = docs.documents().get(documentId=doc_id).execute()

        cell_positions: list[list[int]] = []
        for element in doc.get("body", {}).get("content", []):
            if "table" not in element:
                continue
            table = element["table"]
            # Check if this is the table we just inserted (matches dimensions)
            if len(table.get("tableRows", [])) != total_rows:
                continue
            # Check that it starts at or near marker_start
            if abs(element.get("startIndex", 0) - marker_start) > 5:
                continue

            for table_row in table.get("tableRows", []):
                row_positions = []
                for table_cell in table_row.get("tableCells", []):
                    # Each cell's first paragraph is at cell.startIndex + 1
                    cell_start = table_cell.get("startIndex", 0)
                    # The paragraph inside the cell starts one after cell boundary
                    row_positions.append(cell_start + 1)
                cell_positions.append(row_positions)
            break

        if not cell_positions:
            print(f"  ⚠ Could not find inserted table for marker {i}")
            continue

        # Step 3: populate cells in REVERSE order so earlier positions don't shift
        populate_requests = []
        all_rows = ([headers] if headers else []) + rows

        # Build the flat list of (row_idx, col_idx, cell_start, text)
        cell_inserts = []
        for row_idx, row_data in enumerate(all_rows):
            for col_idx, cell_text in enumerate(row_data):
                if row_idx >= len(cell_positions) or col_idx >= len(cell_positions[row_idx]):
                    continue
                cell_start = cell_positions[row_idx][col_idx]
                cell_inserts.append((row_idx, col_idx, cell_start, str(cell_text)))

        # Sort by cell_start DESCENDING so earlier inserts don't shift later positions
        cell_inserts.sort(key=lambda x: -x[2])

        for row_idx, col_idx, cell_start, cell_text in cell_inserts:
            # Skip empty cells — Google Docs API rejects empty insertText requests
            if not cell_text or not cell_text.strip():
                continue
            populate_requests.append({
                "insertText": {
                    "location": {"index": cell_start},
                    "text": cell_text
                }
            })

        # Execute the text inserts
        if populate_requests:
            docs.documents().batchUpdate(documentId=doc_id, body={"requests": populate_requests}).execute()

        # Step 4: style the header row (re-fetch to get accurate ranges)
        if headers:
            doc = docs.documents().get(documentId=doc_id).execute()
            style_requests = []
            for element in doc.get("body", {}).get("content", []):
                if "table" not in element:
                    continue
                table = element["table"]
                if len(table.get("tableRows", [])) != total_rows:
                    continue
                if abs(element.get("startIndex", 0) - marker_start) > 5:
                    continue

                header_row = table["tableRows"][0]
                for cell in header_row.get("tableCells", []):
                    cell_start_idx = cell.get("startIndex", 0)
                    cell_end_idx = cell.get("endIndex", 0)
                    # Style cell background
                    style_requests.append({
                        "updateTableCellStyle": {
                            "tableCellStyle": {
                                "backgroundColor": {"color": {"rgbColor": COLOR_BG_GRAY}}
                            },
                            "fields": "backgroundColor",
                            "tableRange": {
                                "tableCellLocation": {
                                    "tableStartLocation": {"index": element["startIndex"]},
                                    "rowIndex": 0,
                                    "columnIndex": header_row["tableCells"].index(cell),
                                },
                                "rowSpan": 1,
                                "columnSpan": 1,
                            }
                        }
                    })
                    # Style text bold
                    if cell_start_idx + 1 < cell_end_idx - 1:
                        style_requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": cell_start_idx + 1,
                                    "endIndex": cell_end_idx - 1,
                                },
                                "textStyle": {
                                    "bold": True,
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "weightedFontFamily": {"fontFamily": FONT_BODY},
                                },
                                "fields": "bold,fontSize,weightedFontFamily"
                            }
                        })
                break

            if style_requests:
                try:
                    docs.documents().batchUpdate(documentId=doc_id, body={"requests": style_requests}).execute()
                except Exception as e:
                    print(f"  ⚠ Header styling failed: {str(e)[:200]}")

        print(f"  ✓ Table {i} inserted: {total_rows}×{total_cols}")


# ── Main ──────────────────────────────────────────────────────


def main():
    db = SessionLocal()
    docs = build_docs_service(db)

    print("Clearing document...")
    clear_doc(docs, WORKSPACE_DOC_ID)

    print("Building content...")
    writer = DocWriter()
    build_workspace_content(writer)

    print(f"Writer state: pos={writer.pos}, "
          f"text_requests={len(writer.text_requests)}, "
          f"style_requests={len(writer.style_requests)}, "
          f"tables={len(writer.table_placeholders)}")

    print("\nApplying text insertions + styles...")
    apply_requests(docs, WORKSPACE_DOC_ID, writer.get_all_requests(), "Main content")

    print("\nInserting tables (second pass)...")
    insert_tables_second_pass(docs, WORKSPACE_DOC_ID, writer.table_placeholders)

    print(f"\n✓ Workspace doc populated")
    print(f"  Link: https://docs.google.com/document/d/{WORKSPACE_DOC_ID}/edit")


if __name__ == "__main__":
    main()
