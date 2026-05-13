#!/usr/bin/env python3
"""
BID Executive Deck Restructuring Script

Transforms the 38-slide presentation into a 12-slide executive main deck + appendix.

Target Structure:
- 12 main slides (what gets presented)
- Appendix (technical backup for Q&A)
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"

# EMU conversion (914400 EMU = 1 inch)
EMU_PER_INCH = 914400
SLIDE_WIDTH = 10 * EMU_PER_INCH  # Standard 10 inches
SLIDE_HEIGHT = 5.625 * EMU_PER_INCH  # 16:9 aspect ratio


def get_slides_service():
    """Get Google Slides service."""
    db = SessionLocal()
    slides_service = build_slides_service(db)
    if not slides_service:
        print("ERROR: Google integration not connected")
        sys.exit(1)
    return slides_service, db


def get_presentation_slides(slides_service):
    """Get current slides with IDs and titles."""
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    slides = []
    for i, slide in enumerate(presentation.get("slides", [])):
        slide_id = slide.get("objectId")
        title = extract_title(slide)
        slides.append({"index": i, "id": slide_id, "title": title})

    return slides


def extract_title(slide):
    """Extract title from slide."""
    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        placeholder = shape.get("placeholder", {})
        if placeholder.get("type") in ("TITLE", "CENTERED_TITLE"):
            text_elements = shape.get("text", {}).get("textElements", [])
            for te in text_elements:
                if "textRun" in te:
                    content = te["textRun"].get("content", "").strip()
                    if content:
                        return content[:80]
    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        text_elements = shape.get("text", {}).get("textElements", [])
        for te in text_elements:
            if "textRun" in te:
                content = te["textRun"].get("content", "").strip()
                if content and len(content) > 3:
                    return content[:80]
    return "(sin titulo)"


def generate_unique_id():
    """Generate a unique ID for new elements."""
    return f"exec_{uuid.uuid4().hex[:12]}"


def create_text_box(page_id, text, x_emu, y_emu, width_emu, height_emu,
                    font_size=18, bold=False, element_id=None):
    """Create requests for a text box with text."""
    if element_id is None:
        element_id = generate_unique_id()

    requests = [
        # Create the shape
        {
            "createShape": {
                "objectId": element_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": width_emu, "unit": "EMU"},
                        "height": {"magnitude": height_emu, "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x_emu,
                        "translateY": y_emu,
                        "unit": "EMU"
                    }
                }
            }
        },
        # Insert text
        {
            "insertText": {
                "objectId": element_id,
                "insertionIndex": 0,
                "text": text
            }
        },
        # Style the text
        {
            "updateTextStyle": {
                "objectId": element_id,
                "style": {
                    "fontSize": {"magnitude": font_size, "unit": "PT"},
                    "bold": bold,
                    "fontFamily": "Arial"
                },
                "textRange": {"type": "ALL"},
                "fields": "fontSize,bold,fontFamily"
            }
        }
    ]
    return requests, element_id


def create_title_text_box(page_id, title_text, title_id=None):
    """Create a title text box at standard position."""
    if title_id is None:
        title_id = generate_unique_id()

    return create_text_box(
        page_id=page_id,
        text=title_text,
        x_emu=int(0.5 * EMU_PER_INCH),
        y_emu=int(0.3 * EMU_PER_INCH),
        width_emu=int(9 * EMU_PER_INCH),
        height_emu=int(0.8 * EMU_PER_INCH),
        font_size=32,
        bold=True,
        element_id=title_id
    )


def create_body_text_box(page_id, body_text, body_id=None):
    """Create a body text box at standard position."""
    if body_id is None:
        body_id = generate_unique_id()

    return create_text_box(
        page_id=page_id,
        text=body_text,
        x_emu=int(0.5 * EMU_PER_INCH),
        y_emu=int(1.3 * EMU_PER_INCH),
        width_emu=int(9 * EMU_PER_INCH),
        height_emu=int(4 * EMU_PER_INCH),
        font_size=18,
        bold=False,
        element_id=body_id
    )


def create_new_slide_with_content(slide_id, title, body, insertion_index=None):
    """
    Create requests for a new slide with title and body content.
    Returns list of requests.
    """
    requests = []

    # Create the slide
    create_slide_request = {
        "createSlide": {
            "objectId": slide_id,
            "slideLayoutReference": {
                "predefinedLayout": "BLANK"
            }
        }
    }

    if insertion_index is not None:
        create_slide_request["createSlide"]["insertionIndex"] = insertion_index

    requests.append(create_slide_request)

    # Add title
    title_requests, _ = create_title_text_box(slide_id, title)
    requests.extend(title_requests)

    # Add body
    body_requests, _ = create_body_text_box(slide_id, body)
    requests.extend(body_requests)

    return requests


# ============================================================================
# NEW SLIDES CONTENT - Executive Deck
# ============================================================================

NEW_SLIDES = [
    {
        "id": "exec_slide_02",
        "title": "Qué hay de nuevo desde el informe de avance",
        "body": """• Cierre fiscal 2024: El gasto en seguridad alcanzó $4,47 billones (1,43% del PIB)

• Composición estable: La estructura del gasto permanece rígida—44% policías, 32% justicia, 20% prisiones

• Limitaciones metodológicas: COFOG no captura prevención ni transferencias a municipios

• Agenda de calidad: El foco cambia de "cuánto" a "cómo" se gasta

Fuente: DIPRES, Ley de Presupuestos 2024"""
    },
    {
        "id": "exec_slide_03",
        "title": "5 mensajes clave del informe",
        "body": """1. El gasto en seguridad muestra convergencia parcial post-2019, no recuperación completa

2. La composición del gasto está congelada: inercia asignativa de más de una década

3. Chile gasta comparable a OCDE en % PIB, pero la comparación es limitada por definiciones

4. No existe vínculo verificable entre gasto y resultados—faltan datos y evaluaciones

5. El desafío no es subinversión, es calidad y asignación del gasto

Fuente: Elaboración propia en base a DIPRES, OCDE, Eurostat"""
    },
    {
        "id": "exec_slide_04",
        "title": "El giro: no es cuánto, es cómo",
        "body": """TESIS CENTRAL

El problema del gasto en seguridad en Chile no es de nivel—es de composición, evaluación y resultados.

• No hay evidencia de subinversión comparada con OCDE
• Pero tampoco hay evidencia de que el gasto actual sea efectivo
• La agenda debe migrar de "más recursos" a "mejor asignación"

Implicancia: Las recomendaciones se centran en calidad del gasto, no en aumentos presupuestarios.

Fuente: Análisis Espacio Público 2024"""
    },
    {
        "id": "exec_slide_09",
        "title": "El cuello de botella: no podemos ligar gasto a resultados",
        "body": """DIAGNÓSTICO DE INFORMACIÓN

• COFOG 703 no captura gasto en prevención ni transferencias municipales
• No existe diccionario de datos integrado entre instituciones
• Evaluaciones de impacto son escasas y no sistemáticas

CONSECUENCIA
Sin trazabilidad presupuestaria, no se puede optimizar la asignación.

OPORTUNIDAD
Chile tiene capacidad técnica para construir este sistema—falta decisión política.

Fuente: Revisión de clasificadores presupuestarios DIPRES"""
    },
    {
        "id": "exec_slide_10",
        "title": "Agenda de calidad del gasto: 4 desafíos",
        "body": """1. MEDICIÓN
   Construir sistema de indicadores que vincule presupuesto con resultados

2. EVALUACIÓN
   Implementar evaluaciones de impacto sistemáticas para programas de seguridad

3. COORDINACIÓN
   Integrar información entre Carabineros, PDI, Gendarmería y Fiscalía

4. PREVENCIÓN
   Rediseñar clasificadores para capturar gasto preventivo

Prioridad: Comenzar por medición—sin datos, no hay gestión.

Fuente: Recomendaciones Espacio Público para BID"""
    },
    {
        "id": "exec_slide_12",
        "title": "Próximos pasos: oportunidad para el BID",
        "body": """ÁREAS DE COLABORACIÓN POTENCIAL

• Tablero de indicadores: Diseño de sistema de monitoreo gasto-resultados
• Pilotos de evaluación: Metodologías de evaluación de impacto para programas específicos
• Asistencia técnica: Rediseño de clasificadores presupuestarios
• Capacitación: Formación en presupuesto por resultados

ENTREGABLES SUGERIDOS
→ Diagnóstico de brechas de información (Q2 2026)
→ Diseño de tablero piloto (Q3 2026)
→ Primera evaluación de impacto (Q4 2026)

Fuente: Propuesta Espacio Público"""
    }
]


def create_executive_slides(slides_service, dry_run=True):
    """Create the new executive slides."""

    print("=" * 80)
    print("CREATING EXECUTIVE SLIDES")
    print("=" * 80)

    all_requests = []

    for slide in NEW_SLIDES:
        print(f"\nPreparing: {slide['title'][:50]}...")
        requests = create_new_slide_with_content(
            slide_id=slide["id"],
            title=slide["title"],
            body=slide["body"]
        )
        all_requests.extend(requests)
        print(f"  → {len(requests)} requests")

    print(f"\nTotal requests: {len(all_requests)}")

    if dry_run:
        print("\n[DRY RUN] Would execute these requests. Run with --execute to apply.")
        return True

    # Execute
    try:
        body = {"requests": all_requests}
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"\n✓ Successfully created {len(NEW_SLIDES)} new slides")
        return True
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False


def reorganize_for_executive_deck(slides_service, dry_run=True):
    """
    Reorganize slides into executive main deck + appendix.

    Target order (0-indexed):
    0: Portada (keep)
    1: Qué hay de nuevo (exec_slide_02)
    2: 5 mensajes clave (exec_slide_03)
    3: El giro (exec_slide_04)
    4: Foto fiscal 2024 - adapt existing
    5: Tendencia 2013-2024 - adapt existing
    6: Estructura congelada - adapt existing composición slide
    7: Comparación internacional - adapt existing
    8: Cuello de botella (exec_slide_09)
    9: Agenda calidad (exec_slide_10)
    10: 5 recomendaciones - consolidate existing
    11: Próximos pasos BID (exec_slide_12)
    12+: APÉNDICE (everything else)
    """

    print("\n" + "=" * 80)
    print("REORGANIZING FOR EXECUTIVE DECK")
    print("=" * 80)

    # Get current structure
    slides = get_presentation_slides(slides_service)
    print(f"\nCurrent slides: {len(slides)}")

    # Build slide map by ID prefix for identification
    slide_by_title = {}
    for s in slides:
        slide_by_title[s["title"][:40].lower()] = s

    # The new slides were created at the end, so they're at high indices
    # We need to move them to their correct positions

    # First, let's identify the slides by their IDs/titles
    print("\nIdentifying slides...")

    # Find our newly created slides
    new_slide_ids = {slide["id"]: slide for slide in NEW_SLIDES}

    # Plan the moves
    # We'll move slides one by one to build the correct order

    moves = []

    # After creation, new slides will be at the end
    # We need to:
    # 1. Move exec_slide_02 to position 1
    # 2. Move exec_slide_03 to position 2
    # 3. Move exec_slide_04 to position 3
    # etc.

    target_positions = [
        ("exec_slide_02", 1, "Qué hay de nuevo"),
        ("exec_slide_03", 2, "5 mensajes clave"),
        ("exec_slide_04", 3, "El giro"),
        # Positions 4-7 use existing slides that need to be moved
        ("exec_slide_09", 8, "Cuello de botella"),
        ("exec_slide_10", 9, "Agenda calidad"),
        ("exec_slide_12", 11, "Próximos pasos BID"),
    ]

    print("\nPlanned moves for new slides:")
    for slide_id, pos, desc in target_positions:
        print(f"  {slide_id} -> position {pos} ({desc})")

    if dry_run:
        print("\n[DRY RUN] Would execute these moves. Run with --execute to apply.")
        return True

    # Execute moves one by one (order matters because indices shift)
    for slide_id, target_pos, desc in target_positions:
        print(f"\nMoving {desc} to position {target_pos}...")

        body = {
            "requests": [{
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": target_pos
                }
            }]
        }

        try:
            slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=body
            ).execute()
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    return True


def update_slide_titles_to_conclusions(slides_service, dry_run=True):
    """
    Update existing slide titles to conclusion-style format.
    """

    print("\n" + "=" * 80)
    print("UPDATING TITLES TO CONCLUSION STYLE")
    print("=" * 80)

    title_updates = [
        # (old_text, new_text)
        ("La composición 2024 del 703 confirma un patrón estable.",
         "La estructura del gasto está congelada: 44% policías, 32% justicia, 20% prisiones"),
        ("Gasto público según clasificación funcional como % del PIB",
         "Foto fiscal 2024: $4,47 billones / 1,43% PIB / 5,82% Gasto Total"),
        ("Tendencia del gasto en seguridad entre 2013 y 2018",
         "Tendencia 2013-2024: convergencia parcial post-2019"),
        ("Comparación internacional del gasto per cápita en seguridad",
         "Comparación internacional: Chile ≈ OCDE en % PIB"),
    ]

    if dry_run:
        print("\n[DRY RUN] Would update these titles:")
        for old, new in title_updates:
            print(f"\n  OLD: {old[:50]}...")
            print(f"  NEW: {new[:50]}...")
        return True

    requests = []
    for old_text, new_text in title_updates:
        requests.append({
            "replaceAllText": {
                "containsText": {
                    "text": old_text,
                    "matchCase": False
                },
                "replaceText": new_text
            }
        })

    if requests:
        try:
            body = {"requests": requests}
            response = slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=body
            ).execute()
            print(f"✓ Updated {len(requests)} titles")
            return True
        except Exception as e:
            print(f"✗ ERROR: {e}")
            return False

    return True


def apply_tone_adjustments(slides_service, dry_run=True):
    """
    Apply tone adjustments across all slides.
    """

    print("\n" + "=" * 80)
    print("APPLYING TONE ADJUSTMENTS")
    print("=" * 80)

    replacements = [
        ("normalización", "convergencia parcial"),
        ("Normalización", "Convergencia parcial"),
        ("parece que", "los datos indican que"),
        ("Parece que", "Los datos indican que"),
        ("~55% a personal", "~70% a personal"),
    ]

    if dry_run:
        print("\n[DRY RUN] Would apply these replacements:")
        for old, new in replacements:
            print(f"  '{old}' → '{new}'")
        return True

    requests = []
    for old_text, new_text in replacements:
        requests.append({
            "replaceAllText": {
                "containsText": {
                    "text": old_text,
                    "matchCase": True
                },
                "replaceText": new_text
            }
        })

    if requests:
        try:
            body = {"requests": requests}
            response = slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=body
            ).execute()
            print(f"✓ Applied {len(requests)} text replacements")
            return True
        except Exception as e:
            print(f"✗ ERROR: {e}")
            return False

    return True


def add_appendix_header(slides_service, insertion_index, dry_run=True):
    """Add an APÉNDICE header slide."""

    print("\n" + "=" * 80)
    print("ADDING APPENDIX HEADER")
    print("=" * 80)

    slide_id = "exec_appendix_header"

    requests = create_new_slide_with_content(
        slide_id=slide_id,
        title="APÉNDICE",
        body="""Material técnico de respaldo para preguntas y discusión.

• Metodología COFOG detallada
• Series históricas completas
• Comparaciones por subfunción
• Clasificación económica
• Gráficos adicionales""",
        insertion_index=insertion_index
    )

    if dry_run:
        print(f"[DRY RUN] Would create appendix header at position {insertion_index}")
        return True

    try:
        body = {"requests": requests}
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"✓ Created appendix header at position {insertion_index}")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def show_final_structure(slides_service):
    """Show the final slide structure."""

    print("\n" + "=" * 80)
    print("FINAL PRESENTATION STRUCTURE")
    print("=" * 80)

    slides = get_presentation_slides(slides_service)

    print(f"\nTotal slides: {len(slides)}")
    print("-" * 80)

    for s in slides:
        marker = ""
        if s["index"] < 12:
            marker = " [MAIN DECK]"
        elif "APÉNDICE" in s["title"] or "Apéndice" in s["title"] or "Anexo" in s["title"]:
            marker = " [APPENDIX HEADER]"
        else:
            marker = " [APPENDIX]"

        print(f"{s['index']:3d}. {s['title'][:60]}{marker}")


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="BID Executive Deck Restructuring")
    parser.add_argument("command",
                        choices=["create-slides", "reorganize", "update-titles",
                                 "tone-adjust", "add-appendix", "full-restructure", "show"],
                        help="Command to execute")
    parser.add_argument("--execute", action="store_true",
                        help="Actually execute (default is dry run)")
    parser.add_argument("--appendix-index", type=int, default=12,
                        help="Index for appendix header")

    args = parser.parse_args()
    dry_run = not args.execute

    slides_service, db = get_slides_service()

    try:
        if args.command == "show":
            show_final_structure(slides_service)

        elif args.command == "create-slides":
            create_executive_slides(slides_service, dry_run)

        elif args.command == "reorganize":
            reorganize_for_executive_deck(slides_service, dry_run)

        elif args.command == "update-titles":
            update_slide_titles_to_conclusions(slides_service, dry_run)

        elif args.command == "tone-adjust":
            apply_tone_adjustments(slides_service, dry_run)

        elif args.command == "add-appendix":
            add_appendix_header(slides_service, args.appendix_index, dry_run)

        elif args.command == "full-restructure":
            print("FULL RESTRUCTURE SEQUENCE")
            print("=" * 80)

            if dry_run:
                print("\n⚠️  DRY RUN MODE - No changes will be made")
                print("    Run with --execute to apply changes\n")

            # Step 1: Create new slides
            print("\n[STEP 1/5] Creating executive slides...")
            if not create_executive_slides(slides_service, dry_run):
                print("Failed at step 1")
                return

            # Step 2: Reorganize
            print("\n[STEP 2/5] Reorganizing slides...")
            if not reorganize_for_executive_deck(slides_service, dry_run):
                print("Failed at step 2")
                return

            # Step 3: Update titles
            print("\n[STEP 3/5] Updating titles to conclusion style...")
            if not update_slide_titles_to_conclusions(slides_service, dry_run):
                print("Failed at step 3")
                return

            # Step 4: Tone adjustments
            print("\n[STEP 4/5] Applying tone adjustments...")
            if not apply_tone_adjustments(slides_service, dry_run):
                print("Failed at step 4")
                return

            # Step 5: Add appendix header
            print("\n[STEP 5/5] Adding appendix header...")
            if not add_appendix_header(slides_service, args.appendix_index, dry_run):
                print("Failed at step 5")
                return

            print("\n" + "=" * 80)
            if dry_run:
                print("DRY RUN COMPLETE - Run with --execute to apply changes")
            else:
                print("RESTRUCTURE COMPLETE!")
                show_final_structure(slides_service)

    finally:
        db.close()


if __name__ == "__main__":
    main()
