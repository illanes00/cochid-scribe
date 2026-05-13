#!/usr/bin/env python3
"""
Fix BID Presentation Slide Order

This script reorders the BID presentation slides to the correct sequence.
The slides were added in reverse order due to duplication API behavior.

Correct target order:
1. Portada + Contexto (slides 0-4)
2. II. Comparación Regional header + LATAM slides (currently reversed)
3. III. Hallazgos header + Hallazgos 1→5 (currently reversed)
4. IV. Recomendaciones header + Recs 1→5 (currently reversed)
5. V. Propuesta BID (currently at wrong position)
6. Data slides (Metodología, Gasto, Composición, etc.)
7. Conclusiones + Próximos Pasos
8. Anexos
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"


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


def move_slides_batch(slides_service, moves):
    """
    Move multiple slides. Each move is (slide_id, target_index).
    Important: Execute one at a time because indices shift after each move.
    """
    for slide_id, target_index, description in moves:
        print(f"Moving: {description} -> position {target_index}")

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
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    return True


def fix_slide_order():
    """Main function to fix slide order."""
    slides_service, db = get_slides_service()

    try:
        print("=" * 80)
        print("BID SLIDE REORDERING")
        print("=" * 80)

        # Get current slide structure
        slides = get_presentation_slides(slides_service)
        print(f"\nTotal slides: {len(slides)}")

        # Map slide IDs by current position
        slide_map = {s["index"]: s for s in slides}

        # Current problematic positions (from previous analysis):
        # 0: Portada
        # 1-4: Contexto
        # 5: V. Propuesta BID (WRONG - should be after Recomendaciones)
        # 6-11: Recomendaciones 5,4,3,2,1, header (REVERSED)
        # 12-17: Hallazgos 5,4,3,2,1, header (REVERSED)
        # 18-22: LATAM Anomalía, Ranking, Paradoja, Chile, header (REVERSED)
        # 23+: Data slides

        print("\nPlan: Reorder new sections to correct sequence")
        print("-" * 80)

        # We need to reorganize slides 5-22 to correct order
        # Strategy: Move slides one by one starting from the last section
        # that needs to be in the correct position

        # Let's identify the IDs first
        propuesta_id = slide_map[5]["id"]  # V. Propuesta BID

        # Recomendaciones: header at 11, then 5,4,3,2,1 at 6-10
        rec_header_id = slide_map[11]["id"]  # IV. Recomendaciones header
        rec_5_id = slide_map[6]["id"]   # Rec 5
        rec_4_id = slide_map[7]["id"]   # Rec 4
        rec_3_id = slide_map[8]["id"]   # Rec 3
        rec_2_id = slide_map[9]["id"]   # Rec 2
        rec_1_id = slide_map[10]["id"]  # Rec 1

        # Hallazgos: header at 17, then 5,4,3,2,1 at 12-16
        hal_header_id = slide_map[17]["id"]  # III. Hallazgos header
        hal_5_id = slide_map[12]["id"]  # Hallazgo 5
        hal_4_id = slide_map[13]["id"]  # Hallazgo 4
        hal_3_id = slide_map[14]["id"]  # Hallazgo 3
        hal_2_id = slide_map[15]["id"]  # Hallazgo 2
        hal_1_id = slide_map[16]["id"]  # Hallazgo 1

        # LATAM: header at 22, then Anomalía(18), Ranking(19), Paradoja(20), Chile(21)
        latam_header_id = slide_map[22]["id"]  # II. Comparación Regional header
        latam_anomalia_id = slide_map[18]["id"]  # Anomalía
        latam_ranking_id = slide_map[19]["id"]   # Ranking
        latam_paradoja_id = slide_map[20]["id"]  # Paradoja
        latam_chile_id = slide_map[21]["id"]     # Chile en Contexto

        print("\nIdentified slide IDs:")
        print(f"  Propuesta BID: {propuesta_id[:15]}...")
        print(f"  Rec header: {rec_header_id[:15]}...")
        print(f"  Hallazgos header: {hal_header_id[:15]}...")
        print(f"  LATAM header: {latam_header_id[:15]}...")

        # TARGET ORDER (after slides 0-4 Contexto):
        # Position 5: II. Comparación Regional (header)
        # Position 6: Chile en Contexto Regional
        # Position 7: Paradoja del Gasto Regional
        # Position 8: Ranking Regional de Gasto
        # Position 9: Anomalía Chilena
        # Position 10: III. Hallazgos (header)
        # Position 11: Hallazgo 1
        # Position 12: Hallazgo 2
        # Position 13: Hallazgo 3
        # Position 14: Hallazgo 4
        # Position 15: Hallazgo 5
        # Position 16: IV. Recomendaciones (header)
        # Position 17: Rec 1
        # Position 18: Rec 2
        # Position 19: Rec 3
        # Position 20: Rec 4
        # Position 21: Rec 5
        # Position 22: V. Propuesta BID

        # Strategy: Build the correct order by moving slides
        # We'll work from position 5 forward

        moves = []

        # Move LATAM header to position 5
        moves.append((latam_header_id, 5, "II. Comparación Regional header"))

        # After this, the header is at 5, everything else shifts
        # Chile (was 21, now 22) should go to position 6
        moves.append((latam_chile_id, 6, "Chile en Contexto Regional"))

        # Paradoja (was 20, now at some position) -> 7
        moves.append((latam_paradoja_id, 7, "Paradoja del Gasto Regional"))

        # Ranking -> 8
        moves.append((latam_ranking_id, 8, "Ranking Regional de Gasto"))

        # Anomalía -> 9
        moves.append((latam_anomalia_id, 9, "Anomalía Chilena"))

        # Now move Hallazgos section starting at position 10
        moves.append((hal_header_id, 10, "III. Hallazgos header"))
        moves.append((hal_1_id, 11, "Hallazgo 1"))
        moves.append((hal_2_id, 12, "Hallazgo 2"))
        moves.append((hal_3_id, 13, "Hallazgo 3"))
        moves.append((hal_4_id, 14, "Hallazgo 4"))
        moves.append((hal_5_id, 15, "Hallazgo 5"))

        # Recomendaciones section starting at position 16
        moves.append((rec_header_id, 16, "IV. Recomendaciones header"))
        moves.append((rec_1_id, 17, "Recomendación 1"))
        moves.append((rec_2_id, 18, "Recomendación 2"))
        moves.append((rec_3_id, 19, "Recomendación 3"))
        moves.append((rec_4_id, 20, "Recomendación 4"))
        moves.append((rec_5_id, 21, "Recomendación 5"))

        # Propuesta at position 22
        moves.append((propuesta_id, 22, "V. Propuesta BID"))

        print(f"\nTotal moves planned: {len(moves)}")
        print("-" * 80)

        # Execute moves
        if not move_slides_batch(slides_service, moves):
            print("\nERROR: Some moves failed")
            return False

        print("\n" + "=" * 80)
        print("REORDERING COMPLETE!")
        print("=" * 80)

        # Show final structure
        print("\nFinal slide structure:")
        final_slides = get_presentation_slides(slides_service)
        for s in final_slides:
            print(f"  {s['index']:3d}. {s['title'][:60]}")

        return True

    finally:
        db.close()


if __name__ == "__main__":
    fix_slide_order()
