#!/usr/bin/env python3
"""
Script para importar las notas del informe BID a Scribe.

Convierte los archivos Markdown a JSON de Tiptap y los envía a la API de Scribe.

Uso:
    python scripts/import_bid_notes.py [--api-url URL]

Prerequisitos:
    - Scribe corriendo (docker-compose up)
    - requests instalado (pip install requests)
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)


# Configuración por defecto
DEFAULT_API_URL = "http://localhost:8000/api/v1/notes"
DOCS_DIR = Path(__file__).parent.parent / "docs"


def markdown_to_tiptap(markdown: str) -> dict:
    """
    Convierte Markdown a JSON de Tiptap.

    Esta es una conversión simplificada que maneja:
    - Encabezados (# ## ###)
    - Párrafos
    - Listas (- *)
    - Listas ordenadas (1. 2. 3.)
    - Texto en negrita (**texto**)
    - Texto en cursiva (*texto* o _texto_)
    - Blockquotes (>)
    - Tablas (básico)
    - Separadores (---)
    """
    content = []
    lines = markdown.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Saltar líneas vacías
        if not line:
            i += 1
            continue

        # Encabezados
        if line.startswith('# '):
            content.append(create_heading(line[2:], 1))
            i += 1
            continue
        elif line.startswith('## '):
            content.append(create_heading(line[3:], 2))
            i += 1
            continue
        elif line.startswith('### '):
            content.append(create_heading(line[4:], 3))
            i += 1
            continue

        # Blockquotes
        if line.startswith('> '):
            quote_lines = []
            while i < len(lines) and lines[i].startswith('> '):
                quote_lines.append(lines[i][2:])
                i += 1
            content.append(create_blockquote(' '.join(quote_lines)))
            continue

        # Listas no ordenadas
        if line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                list_items.append(lines[i][2:])
                i += 1
            content.append(create_bullet_list(list_items))
            continue

        # Listas ordenadas
        if re.match(r'^\d+\. ', line):
            list_items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                list_items.append(re.sub(r'^\d+\. ', '', lines[i]))
                i += 1
            content.append(create_ordered_list(list_items))
            continue

        # Separadores (horizontal rule)
        if line == '---':
            content.append({"type": "horizontalRule"})
            i += 1
            continue

        # Tablas
        if '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            content.append(create_table(table_lines))
            continue

        # Code blocks
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            content.append(create_code_block('\n'.join(code_lines)))
            i += 1  # Skip closing ```
            continue

        # Párrafo normal
        para_lines = []
        while i < len(lines) and lines[i] and not lines[i].startswith('#') and not lines[i].startswith('- ') and not lines[i].startswith('* ') and not lines[i].startswith('> ') and not lines[i].startswith('```') and lines[i] != '---':
            para_lines.append(lines[i])
            i += 1

        if para_lines:
            content.append(create_paragraph(' '.join(para_lines)))

    return {
        "type": "doc",
        "content": content
    }


def parse_inline_formatting(text: str) -> list:
    """Parsea formato inline (negrita, cursiva) a nodos de Tiptap."""
    nodes = []

    # Patrón para negrita e itálica
    pattern = r'(\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_)'
    last_end = 0

    for match in re.finditer(pattern, text):
        # Añadir texto antes del match
        if match.start() > last_end:
            nodes.append({"type": "text", "text": text[last_end:match.start()]})

        # Determinar tipo de formato
        if match.group(2):  # Negrita (**)
            nodes.append({
                "type": "text",
                "marks": [{"type": "bold"}],
                "text": match.group(2)
            })
        elif match.group(3) or match.group(4):  # Itálica (* o _)
            nodes.append({
                "type": "text",
                "marks": [{"type": "italic"}],
                "text": match.group(3) or match.group(4)
            })

        last_end = match.end()

    # Añadir texto restante
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})

    # Si no hay formato, devolver texto simple
    if not nodes:
        return [{"type": "text", "text": text}] if text else []

    return nodes


def create_heading(text: str, level: int) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": parse_inline_formatting(text)
    }


def create_paragraph(text: str) -> dict:
    content = parse_inline_formatting(text)
    if not content:
        return {"type": "paragraph"}
    return {
        "type": "paragraph",
        "content": content
    }


def create_blockquote(text: str) -> dict:
    return {
        "type": "blockquote",
        "content": [create_paragraph(text)]
    }


def create_bullet_list(items: list) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [create_paragraph(item)]
            }
            for item in items
        ]
    }


def create_ordered_list(items: list) -> dict:
    return {
        "type": "orderedList",
        "content": [
            {
                "type": "listItem",
                "content": [create_paragraph(item)]
            }
            for item in items
        ]
    }


def create_code_block(code: str) -> dict:
    return {
        "type": "codeBlock",
        "content": [{"type": "text", "text": code}] if code else []
    }


def create_table(lines: list) -> dict:
    """Crea una tabla simple (como párrafos formateados)."""
    # Las tablas de Tiptap requieren extensión específica
    # Por ahora, las convertimos a texto formateado
    return create_paragraph('\n'.join(lines))


def import_note(api_url: str, title: str, slug: str, markdown: str, tags: list, note_type: str = "summary") -> dict:
    """Importa una nota a Scribe via API."""

    # Convertir Markdown a Tiptap JSON
    content = markdown_to_tiptap(markdown)

    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "markdown": markdown,
        "note_type": note_type,
        "tags": tags
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"Error: No se pudo conectar a {api_url}")
        print("Asegúrate de que Scribe esté corriendo (docker-compose up)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
        print(f"Response: {response.text}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Importar notas BID a Scribe")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="URL de la API de notas")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se importaría")
    args = parser.parse_args()

    # Definir notas a importar
    notes = [
        {
            "file": "bid-resumen-ejecutivo.md",
            "title": "Informe BID - Resumen Ejecutivo (15 págs)",
            "slug": "bid-resumen-ejecutivo",
            "tags": ["BID", "seguridad", "gasto-publico", "resumen"],
            "note_type": "summary"
        },
        {
            "file": "bid-presentacion-final.md",
            "title": "Informe BID - Presentación Final (~50 slides)",
            "slug": "bid-presentacion-final",
            "tags": ["BID", "seguridad", "presentacion"],
            "note_type": "summary"
        }
    ]

    print("=" * 60)
    print("Importador de Notas BID a Scribe")
    print("=" * 60)
    print(f"API URL: {args.api_url}")
    print(f"Directorio docs: {DOCS_DIR}")
    print()

    for note_info in notes:
        file_path = DOCS_DIR / note_info["file"]

        if not file_path.exists():
            print(f"⚠️  Archivo no encontrado: {file_path}")
            continue

        markdown = file_path.read_text(encoding='utf-8')

        print(f"📄 {note_info['title']}")
        print(f"   Archivo: {note_info['file']}")
        print(f"   Slug: {note_info['slug']}")
        print(f"   Tags: {', '.join(note_info['tags'])}")
        print(f"   Tamaño: {len(markdown):,} caracteres")

        if args.dry_run:
            print("   [DRY RUN - No se importó]")
        else:
            result = import_note(
                api_url=args.api_url,
                title=note_info["title"],
                slug=note_info["slug"],
                markdown=markdown,
                tags=note_info["tags"],
                note_type=note_info["note_type"]
            )

            if result:
                print(f"   ✅ Importado correctamente (ID: {result.get('id', 'N/A')})")
            else:
                print("   ❌ Error al importar")

        print()

    print("=" * 60)
    if args.dry_run:
        print("Dry run completado. Ejecuta sin --dry-run para importar.")
    else:
        print("Importación completada.")
        print(f"Abre Scribe en el navegador para ver las notas.")


if __name__ == "__main__":
    main()
