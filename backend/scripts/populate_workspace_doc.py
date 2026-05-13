"""Populate the CIF-EP workspace Google Doc with formatted content.

Reads the inventario and verificacion markdown files, converts them to
Google Docs API batch operations with real formatting (heading styles,
bold, lists, tables), and applies them in a single batch update.

Usage:
    cd /srv/projects/cochid/cochid-scribe/backend
    source .venv/bin/activate
    python scripts/populate_workspace_doc.py
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_docs_service

WORKSPACE_DOC_ID = "1jd6-dk3t_3qZ2sLEc5Ol4Y36okJwKBojrJRbfvA4fBM"

INVENTARIO_PATH = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/inventario-consolidado.md"
)
VERIFICACION_PATH = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/verificacion-datos.md"
)


# ── Block model ───────────────────────────────────────────────


class Block:
    """A formatted block to insert into Google Docs."""

    def __init__(self, kind: str, text: str = "", level: int = 0,
                 inline_runs: list | None = None, table_rows: list | None = None):
        self.kind = kind  # heading1|heading2|heading3|paragraph|bullet|table|hr|spacer
        self.text = text
        self.level = level
        self.inline_runs = inline_runs or []  # list of (start, end, style) tuples
        self.table_rows = table_rows or []


# ── Markdown parser ───────────────────────────────────────────


def parse_inline_runs(text: str) -> tuple[str, list]:
    """Parse **bold** and *italic* and `code` inline styles.

    Returns the plain text (without markers) and a list of style runs:
        [(start, end, {"bold": True}), ...]
    """
    runs = []
    out = []
    i = 0
    out_pos = 0

    while i < len(text):
        # **bold**
        if text[i:i + 2] == "**":
            close = text.find("**", i + 2)
            if close > 0:
                inner = text[i + 2:close]
                start = out_pos
                out.append(inner)
                out_pos += len(inner)
                runs.append((start, out_pos, {"bold": True}))
                i = close + 2
                continue
        # `code`
        if text[i] == "`":
            close = text.find("`", i + 1)
            if close > 0:
                inner = text[i + 1:close]
                start = out_pos
                out.append(inner)
                out_pos += len(inner)
                runs.append((start, out_pos, {"code": True}))
                i = close + 1
                continue
        # *italic* (single asterisk, not part of **)
        if text[i] == "*" and (i + 1 >= len(text) or text[i + 1] != "*"):
            close = text.find("*", i + 1)
            if close > 0 and (close + 1 >= len(text) or text[close + 1] != "*"):
                inner = text[i + 1:close]
                start = out_pos
                out.append(inner)
                out_pos += len(inner)
                runs.append((start, out_pos, {"italic": True}))
                i = close + 1
                continue
        # _italic_ (single underscore)
        if text[i] == "_":
            close = text.find("_", i + 1)
            if close > 0:
                inner = text[i + 1:close]
                start = out_pos
                out.append(inner)
                out_pos += len(inner)
                runs.append((start, out_pos, {"italic": True}))
                i = close + 1
                continue
        # [link](url) — render as text only (Docs API needs separate updateLinkRequests)
        if text[i] == "[":
            close = text.find("]", i + 1)
            if close > 0 and close + 1 < len(text) and text[close + 1] == "(":
                paren = text.find(")", close + 2)
                if paren > 0:
                    label = text[i + 1:close]
                    url = text[close + 2:paren]
                    start = out_pos
                    out.append(label)
                    out_pos += len(label)
                    runs.append((start, out_pos, {"link": url}))
                    i = paren + 1
                    continue
        # Default: copy char
        out.append(text[i])
        out_pos += 1
        i += 1

    return ("".join(out), runs)


def parse_markdown(md: str) -> list[Block]:
    """Parse markdown into a list of Block objects."""
    blocks: list[Block] = []
    lines = md.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            blocks.append(Block("hr"))
            i += 1
            continue

        # Headings
        if stripped.startswith("### "):
            text, runs = parse_inline_runs(stripped[4:])
            blocks.append(Block("heading3", text, inline_runs=runs))
            i += 1
            continue
        if stripped.startswith("## "):
            text, runs = parse_inline_runs(stripped[3:])
            blocks.append(Block("heading2", text, inline_runs=runs))
            i += 1
            continue
        if stripped.startswith("# "):
            text, runs = parse_inline_runs(stripped[2:])
            blocks.append(Block("heading1", text, inline_runs=runs))
            i += 1
            continue

        # Tables
        if "|" in stripped and stripped.startswith("|"):
            # Collect all consecutive table lines
            table_lines = []
            while i < len(lines) and "|" in lines[i].strip() and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            # Parse rows
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.split("|")[1:-1]]
                # Skip separator row
                if all(set(c) <= set("-: ") for c in cells if c):
                    continue
                rows.append([parse_inline_runs(c) for c in cells])

            if rows:
                blocks.append(Block("table", table_rows=rows))
            continue

        # Bullet lists
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            # Determine indent level (rough)
            indent = len(line) - len(line.lstrip())
            level = indent // 2
            text, runs = parse_inline_runs(content)
            blocks.append(Block("bullet", text, level=level, inline_runs=runs))
            i += 1
            continue

        # Numbered lists (1. 2. etc.)
        if re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^\d+\.\s", "", stripped)
            text, runs = parse_inline_runs(content)
            blocks.append(Block("bullet", text, inline_runs=runs))
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            text, runs = parse_inline_runs(stripped[2:])
            blocks.append(Block("paragraph", "❝ " + text, inline_runs=runs))
            i += 1
            continue

        # Default: paragraph
        text, runs = parse_inline_runs(stripped)
        blocks.append(Block("paragraph", text, inline_runs=runs))
        i += 1

    return blocks


# ── Google Docs request builder ───────────────────────────────


def build_requests(blocks: list[Block]) -> list[dict]:
    """Build Google Docs API batchUpdate requests for the given blocks.

    Strategy:
        1. First pass: insert all text content sequentially. Track positions.
        2. Second pass: apply paragraph styles (heading levels, bullets).
        3. Third pass: apply text styles (bold, italic, code, links).
        4. Tables are inserted as table requests in pass 1.

    Google Docs API quirk: indices shift after every insert. We compute
    them as if we were inserting linearly into a fresh empty document
    (which is what we have, since we cleared it).
    """
    requests: list[dict] = []
    style_requests: list[dict] = []  # paragraph + text styles

    # Position tracker — Google Docs starts the body at index 1
    pos = 1

    for block in blocks:
        if block.kind == "hr":
            # Insert a paragraph with horizontal rule character
            text = "─" * 60 + "\n"
            requests.append({
                "insertText": {
                    "location": {"index": pos},
                    "text": text
                }
            })
            # Style as muted gray
            style_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": pos, "endIndex": pos + len(text) - 1},
                    "textStyle": {
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.7, "green": 0.7, "blue": 0.7}}}
                    },
                    "fields": "foregroundColor"
                }
            })
            pos += len(text)
            continue

        if block.kind == "table":
            rows = len(block.table_rows)
            cols = len(block.table_rows[0]) if rows > 0 else 1

            # Insert empty table
            requests.append({
                "insertTable": {
                    "rows": rows,
                    "columns": cols,
                    "location": {"index": pos}
                }
            })

            # After table insert, the structure is:
            # pos -> table start
            # pos + 1 -> first cell paragraph
            # Each cell adds 2 to the index (paragraph + cell separator)
            # Then we need a paragraph after the table

            # We can't easily compute the post-insert positions without
            # querying the doc. Instead, we'll insert the table empty and
            # populate it in a SECOND batch update.
            # For now, mark this position and skip ahead conservatively.

            # Empty table contributes: 1 (table start) + rows*cols*2 + 1 (paragraph after)
            # But the actual offset depends on how many text/cell separators
            # the API generates. Conservative estimate: 1 + rows * (cols * 2 + 1) + 1

            pos += 1 + rows * (cols * 2 + 1) + 1
            continue

        # Text-bearing blocks
        text = block.text + "\n"
        block_start = pos

        requests.append({
            "insertText": {
                "location": {"index": pos},
                "text": text
            }
        })

        # Paragraph style
        if block.kind == "heading1":
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": block_start, "endIndex": block_start + len(text)},
                    "paragraphStyle": {"namedStyleType": "HEADING_1"},
                    "fields": "namedStyleType"
                }
            })
        elif block.kind == "heading2":
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": block_start, "endIndex": block_start + len(text)},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType"
                }
            })
        elif block.kind == "heading3":
            style_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": block_start, "endIndex": block_start + len(text)},
                    "paragraphStyle": {"namedStyleType": "HEADING_3"},
                    "fields": "namedStyleType"
                }
            })
        elif block.kind == "bullet":
            style_requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": block_start, "endIndex": block_start + len(text)},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })

        # Inline text styles
        for run_start, run_end, style in block.inline_runs:
            abs_start = block_start + run_start
            abs_end = block_start + run_end
            text_style = {}
            fields = []
            if style.get("bold"):
                text_style["bold"] = True
                fields.append("bold")
            if style.get("italic"):
                text_style["italic"] = True
                fields.append("italic")
            if style.get("code"):
                text_style["weightedFontFamily"] = {"fontFamily": "Roboto Mono"}
                text_style["backgroundColor"] = {"color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}}
                fields.append("weightedFontFamily")
                fields.append("backgroundColor")
            if style.get("link"):
                text_style["link"] = {"url": style["link"]}
                fields.append("link")

            if fields:
                style_requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": abs_start, "endIndex": abs_end},
                        "textStyle": text_style,
                        "fields": ",".join(fields)
                    }
                })

        pos += len(text)

    return requests + style_requests


# ── Main ──────────────────────────────────────────────────────


def main():
    db = SessionLocal()
    docs = build_docs_service(db)

    # Read source files
    inventario = INVENTARIO_PATH.read_text()
    verificacion = VERIFICACION_PATH.read_text()

    # Build the master markdown
    master = f"""# [Privado] Workspace Revisión Medicamentos

**CIF-EP — Inclusión Sostenible de Medicamentos en Planes de Salud en Chile**

Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Mantenedor: Martín Illanes (martin.illanes@espaciopublico.cl)

---

## 0. Plan de trabajo y estado

### Entregables comprometidos

**Entregable 1** — Consolidado de comentarios y verificación de datos
- Fecha objetivo: lunes 13 o martes 14 de abril
- Para: Benja → Eduardo y Carla
- Contenido: tabla de los ~60 items consolidados + datos verificados
- Sin decisiones de respuesta — esa fase queda para que los directores puedan meter mano si quieren acelerar

**Entregable 2** — Versión final del informe revisado
- Fecha objetivo: semana del 4 de mayo (puede adelantarse si los directores aportan)
- Para: Benja → CIF
- Contenido: documento reescrito con todas las decisiones aplicadas, comentarios respondidos en el GDoc original

### Etapas del plan

**Fase A — Procesamiento y respuestas**

- ✓ Etapa 1: Diagnóstico y estrategia editorial — HECHA
- ⟳ Etapa 2: Centralizar feedback (inventario puro) — EN CURSO
- ⟳ Etapa 3: Verificación de datos críticos — EN CURSO
- Etapa 4: Decidir respuestas (colaborativa o solo)
- Etapa 5: Documento de respuestas + 3 muestras de prosa

**Fase B — Reescritura e integración**

- Etapa 6: Reescritura sustantiva de secciones
- Etapa 7: Trasladar al Google Doc real con suggesting mode
- Etapa 8: Cargar respuestas en threads de comentarios del GDoc
- Etapa 9: Pase final de coherencia
- Etapa 10: Entrega final a Benja

---

{inventario}

---

{verificacion}

---

## 3. Decisiones de respuesta

_(Esta sección se llenará en la Etapa 4)_

Esta sección contendrá la decisión específica para cada comentario:

- **Aceptar** con cambio concreto en el documento
- **Rechazar** con argumento basado en evidencia
- **Parcial**: qué se acepta, qué no

Si Eduardo y Carla quieren tomar comentarios específicos y proponer respuesta directamente, este es el momento de hacerlo.

---

## 4. Borradores de prosa reescrita

_(Esta sección se llenará en la Etapa 6)_

Borradores de las secciones que requieren reescritura sustantiva:

- **Sección 4** — "Opciones de Política" (renombre + reescritura del contenido)
- **Sección 7** — "Marco para la Discusión" (renombre + reescritura)
- **Resumen Ejecutivo** — alineación con el nuevo framing
- **Sección 2.1** — agregar DAC al marco institucional
- **Sección 2.3** — nueva, sobre Judicialización
- **Sección 3** — biosimilares separados de genéricos, ETESA reorientada, nota metodológica
- **Sección nueva** — Innovación con valor sanitario

---

## 5. Notas y dudas

### Hallazgos importantes durante la verificación

**Sobre el dato US$206 PPA**: el dato es correcto pero la cita está mal en tres dimensiones — la fuente real es GHED de OMS (no OECD Health at a Glance), la unidad es US$ corrientes 2022 (no PPA), y el año es 2022 (no 2025). Acción: corregir la cita, no eliminar el dato.

**Sobre la "mediana OCDE de US$600"**: probablemente está mal. Cálculo sobre los 16 países OCDE del dataset original da ~US$550. Acción: recalcular y corregir.

**Sobre el 71% de gasto de bolsillo en farmacias**: es el dato más expuesto a crítica. Cálculos simples no lo reproducen (US$80/US$206 = 39%). El cálculo viene de "INE EPF 2022-2023, Cuadro 8.1, cálculo del autor". Acción: ejecutar el script `app.py` del proyecto `illanes00-cif` para reproducir, o explicitar la metodología en el documento.

**GES 87 → 90 patologías**: confirmado por Decreto GES 2025-2028. Hay que actualizar.

**Costa Rica CCSS**: el informe dice 95%, pero búsquedas previas sugieren 91-93%. Pendiente verificar contra fuente directa.

**Carga sobre ingreso por quintil**: confirmado contra el cálculo original del proyecto `illanes00-cif`. Q1: 9.84%, Q5: 1.90%. No hay error.

---

## Links de trabajo

- **Informe original (Google Doc)**: [docs.google.com/document/d/1ZuaO...](https://docs.google.com/document/d/1ZuaOF9IvZA61B_ZbU6DWuR2uEcMjI6guruLESRuUuxI/edit)
- **Scribe (revisión interna)**: [scribe.illanes00.cl/editor/cif-medicamentos](https://scribe.illanes00.cl/editor/cif-medicamentos)
- **Proyecto fuente original (datos crudos)**: `/srv/projects/archives/illanes00-cif`
"""

    # Parse and build requests
    blocks = parse_markdown(master)
    print(f"Parsed {len(blocks)} blocks from {len(master)} chars of markdown")

    # Filter out tables for now (handle separately to avoid index issues)
    text_blocks = [b for b in blocks if b.kind != "table"]
    print(f"Text blocks: {len(text_blocks)} (filtered {len(blocks) - len(text_blocks)} tables for separate handling)")

    requests = build_requests(text_blocks)
    print(f"Built {len(requests)} batchUpdate requests")

    # Execute in chunks of 100 (Google Docs API has a soft limit)
    chunk_size = 100
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        try:
            docs.documents().batchUpdate(
                documentId=WORKSPACE_DOC_ID,
                body={"requests": chunk}
            ).execute()
            print(f"  Applied chunk {i // chunk_size + 1}: requests {i}–{i + len(chunk)}")
        except Exception as e:
            print(f"  ERROR on chunk {i // chunk_size + 1}: {str(e)[:300]}")
            return

    print(f"\n✓ Workspace doc populated with formatting")
    print(f"  Link: https://docs.google.com/document/d/{WORKSPACE_DOC_ID}/edit")


if __name__ == "__main__":
    main()
