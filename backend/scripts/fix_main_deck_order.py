#!/usr/bin/env python3
"""
Fix Main Deck Order

After initial restructure, the main deck needs refinement:
- Move data slides (Foto fiscal, Tendencia, etc.) INTO main deck positions 4-7
- Move context detail slides TO appendix
- Create consolidated recommendations slide
- Ensure final 12-slide main deck structure
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"

EMU_PER_INCH = 914400


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


def find_slide_by_title_pattern(slides, pattern):
    """Find slide matching pattern."""
    pattern_lower = pattern.lower()
    for s in slides:
        if pattern_lower in s["title"].lower():
            return s
    return None


def move_slide(slides_service, slide_id, target_index, description):
    """Move a single slide to target index."""
    print(f"  Moving: {description} -> position {target_index}")

    body = {
        "requests": [{
            "updateSlidesPosition": {
                "slideObjectIds": [slide_id],
                "insertionIndex": target_index
            }
        }]
    }

    try:
        slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"    ✓ Success")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def generate_unique_id():
    """Generate a unique ID for new elements."""
    return f"cons_{uuid.uuid4().hex[:12]}"


def create_consolidated_recommendations_slide(slides_service, insertion_index, dry_run=True):
    """Create a consolidated 5-recommendations slide."""

    slide_id = "exec_slide_recs_consolidated"
    title_id = f"{slide_id}_title"
    body_id = f"{slide_id}_body"

    title = "5 recomendaciones implementables"
    body = """1. SISTEMA DE EVALUACIÓN
   Crear unidad de evaluación de impacto en DIPRES

2. PRESUPUESTO POR RESULTADOS
   Vincular partidas de seguridad a indicadores verificables

3. COORDINACIÓN INTERAGENCIAL
   Tablero de gestión integrado (Carabineros, PDI, Gendarmería, Fiscalía)

4. INVERSIÓN TECNOLÓGICA ESTRATÉGICA
   Priorizar interoperabilidad sobre adquisiciones aisladas

5. BALANCE PREVENCIÓN/REACCIÓN
   Rediseñar clasificadores para capturar y medir gasto preventivo

Fuente: Recomendaciones Espacio Público basadas en análisis 2013-2024"""

    requests = [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
                "insertionIndex": insertion_index
            }
        },
        {
            "createShape": {
                "objectId": title_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": int(9 * EMU_PER_INCH), "unit": "EMU"},
                        "height": {"magnitude": int(0.8 * EMU_PER_INCH), "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": int(0.5 * EMU_PER_INCH),
                        "translateY": int(0.3 * EMU_PER_INCH),
                        "unit": "EMU"
                    }
                }
            }
        },
        {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
        {
            "updateTextStyle": {
                "objectId": title_id,
                "style": {"fontSize": {"magnitude": 28, "unit": "PT"}, "bold": True, "fontFamily": "Arial"},
                "textRange": {"type": "ALL"},
                "fields": "fontSize,bold,fontFamily"
            }
        },
        {
            "createShape": {
                "objectId": body_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": int(9 * EMU_PER_INCH), "unit": "EMU"},
                        "height": {"magnitude": int(4.2 * EMU_PER_INCH), "unit": "EMU"}
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": int(0.5 * EMU_PER_INCH),
                        "translateY": int(1.2 * EMU_PER_INCH),
                        "unit": "EMU"
                    }
                }
            }
        },
        {"insertText": {"objectId": body_id, "insertionIndex": 0, "text": body}},
        {
            "updateTextStyle": {
                "objectId": body_id,
                "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "fontFamily": "Arial"},
                "textRange": {"type": "ALL"},
                "fields": "fontSize,fontFamily"
            }
        }
    ]

    if dry_run:
        print(f"[DRY RUN] Would create consolidated recommendations at position {insertion_index}")
        return True

    try:
        body_req = {"requests": requests}
        slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body_req
        ).execute()
        print(f"✓ Created consolidated recommendations at position {insertion_index}")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def fix_main_deck(dry_run=True):
    """
    Fix the main deck to match the target 12-slide structure.

    TARGET STRUCTURE:
    0: Portada (keep)
    1: Qué hay de nuevo (already there)
    2: 5 mensajes clave (already there)
    3: El giro (already there)
    4: Foto fiscal 2024 (move from appendix)
    5: Tendencia 2013-2024 (move from appendix)
    6: Estructura congelada (move from appendix)
    7: Comparación internacional (move from appendix)
    8: Cuello de botella (already there)
    9: Agenda calidad (already there)
    10: 5 recomendaciones (CREATE consolidated)
    11: Próximos pasos BID (already there)
    12: APÉNDICE header
    13+: Everything else
    """

    slides_service, db = get_slides_service()

    try:
        print("=" * 80)
        print("FIXING MAIN DECK ORDER")
        print("=" * 80)

        if dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")
            print("    Run with --execute to apply changes\n")

        # Get current structure
        slides = get_presentation_slides(slides_service)
        print(f"\nCurrent slides: {len(slides)}")

        # Find key slides by title pattern
        foto_fiscal = find_slide_by_title_pattern(slides, "Foto fiscal 2024")
        tendencia = find_slide_by_title_pattern(slides, "Tendencia 2013-2024")
        estructura = find_slide_by_title_pattern(slides, "estructura del gasto está congelada")
        comparacion = find_slide_by_title_pattern(slides, "Comparación internacional")

        print("\nIdentified data slides to move into main deck:")
        if foto_fiscal:
            print(f"  Foto fiscal: index {foto_fiscal['index']} - {foto_fiscal['title'][:50]}")
        if tendencia:
            print(f"  Tendencia: index {tendencia['index']} - {tendencia['title'][:50]}")
        if estructura:
            print(f"  Estructura: index {estructura['index']} - {estructura['title'][:50]}")
        if comparacion:
            print(f"  Comparación: index {comparacion['index']} - {comparacion['title'][:50]}")

        # Find slides to move to appendix
        contexto_header = find_slide_by_title_pattern(slides, "I. Contexto y metodología")
        seguridad_publica = find_slide_by_title_pattern(slides, "Seguridad Pública")
        fenomeno_delictual = find_slide_by_title_pattern(slides, "fenómeno delictual")
        contexto_institucional = find_slide_by_title_pattern(slides, "Contexto institucional")
        comparacion_regional = find_slide_by_title_pattern(slides, "II. Comparación Regional")

        print("\nIdentified context slides to move to appendix:")
        for s in [contexto_header, seguridad_publica, fenomeno_delictual,
                  contexto_institucional, comparacion_regional]:
            if s:
                print(f"  Index {s['index']}: {s['title'][:50]}")

        if dry_run:
            print("\n[DRY RUN] Would perform the following operations:")
            print("  1. Move Foto fiscal to position 4")
            print("  2. Move Tendencia to position 5")
            print("  3. Move Estructura to position 6")
            print("  4. Move Comparación to position 7")
            print("  5. Move context slides to appendix")
            print("  6. Create consolidated recommendations at position 10")
            print("  7. Adjust APÉNDICE header position")
            return True

        # PHASE 1: Move data slides into main deck
        # Strategy: Move them one at a time to build correct positions
        # Note: Each move shifts indices, so we need to recalculate

        print("\n[PHASE 1] Moving data slides into main deck...")

        # Move Foto fiscal to position 4
        if foto_fiscal:
            move_slide(slides_service, foto_fiscal["id"], 4, "Foto fiscal 2024")
            slides = get_presentation_slides(slides_service)  # Refresh

        # Move Tendencia to position 5
        tendencia = find_slide_by_title_pattern(slides, "Tendencia 2013-2024")
        if tendencia:
            move_slide(slides_service, tendencia["id"], 5, "Tendencia 2013-2024")
            slides = get_presentation_slides(slides_service)

        # Move Estructura to position 6
        estructura = find_slide_by_title_pattern(slides, "estructura del gasto está congelada")
        if estructura:
            move_slide(slides_service, estructura["id"], 6, "Estructura congelada")
            slides = get_presentation_slides(slides_service)

        # Move Comparación to position 7
        comparacion = find_slide_by_title_pattern(slides, "Comparación internacional")
        if comparacion:
            move_slide(slides_service, comparacion["id"], 7, "Comparación internacional")
            slides = get_presentation_slides(slides_service)

        # PHASE 2: Create consolidated recommendations slide at position 10
        print("\n[PHASE 2] Creating consolidated recommendations slide...")
        create_consolidated_recommendations_slide(slides_service, 10, dry_run=False)
        slides = get_presentation_slides(slides_service)

        # PHASE 3: Move context/section slides to appendix (after APÉNDICE header)
        print("\n[PHASE 3] Moving context slides to appendix...")

        # Find the APÉNDICE header position
        appendix_header = find_slide_by_title_pattern(slides, "APÉNDICE")
        if appendix_header:
            appendix_pos = appendix_header["index"]
            print(f"  Appendix header at position {appendix_pos}")

            # Move context slides to just after appendix header
            for pattern in ["I. Contexto y metodología", "Seguridad Pública",
                            "fenómeno delictual", "Contexto institucional",
                            "II. Comparación Regional"]:
                slides = get_presentation_slides(slides_service)
                s = find_slide_by_title_pattern(slides, pattern)
                if s and s["index"] < 12:  # Only if still in main deck
                    # Find current appendix position
                    appendix_header = find_slide_by_title_pattern(slides, "APÉNDICE")
                    target = appendix_header["index"] + 1 if appendix_header else 13
                    move_slide(slides_service, s["id"], target, pattern[:40])

        # Final structure check
        print("\n" + "=" * 80)
        print("FINAL STRUCTURE")
        print("=" * 80)

        slides = get_presentation_slides(slides_service)
        for s in slides[:15]:  # Show first 15
            marker = " [MAIN]" if s["index"] < 12 else " [APPENDIX]"
            print(f"{s['index']:3d}. {s['title'][:60]}{marker}")

        if len(slides) > 15:
            print(f"  ... and {len(slides) - 15} more slides in appendix")

        return True

    finally:
        db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix Main Deck Order")
    parser.add_argument("--execute", action="store_true", help="Execute changes")
    args = parser.parse_args()

    fix_main_deck(dry_run=not args.execute)


if __name__ == "__main__":
    main()
