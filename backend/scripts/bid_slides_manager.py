#!/usr/bin/env python3
"""
BID Slides Manager - Tool for managing BID presentation slides in Google Slides.

Features:
- Get presentation structure and slide titles
- Reorder slides to correct sequence
- Insert images from URLs
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.google import build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"


def get_presentation_structure():
    """Get the current presentation structure with slide IDs and titles."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected. Please authorize first.")
            return None

        presentation = slides_service.presentations().get(
            presentationId=PRESENTATION_ID
        ).execute()

        slides = presentation.get("slides", [])
        print(f"Presentation: {presentation.get('title')}")
        print(f"Total slides: {len(slides)}")
        print("-" * 80)

        slide_data = []
        for i, slide in enumerate(slides):
            slide_id = slide.get("objectId")
            title = extract_slide_title(slide)
            slide_data.append({
                "index": i,
                "id": slide_id,
                "title": title
            })
            print(f"{i:3d}. [{slide_id[:12]}...] {title}")

        return slide_data
    finally:
        db.close()


def extract_slide_title(slide):
    """Extract the title from a slide."""
    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        placeholder = shape.get("placeholder", {})
        if placeholder.get("type") in ("TITLE", "CENTERED_TITLE"):
            text_elements = shape.get("text", {}).get("textElements", [])
            for te in text_elements:
                if "textRun" in te:
                    content = te["textRun"].get("content", "").strip()
                    if content:
                        return content[:60]
    # Fallback: search for largest text
    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        text_elements = shape.get("text", {}).get("textElements", [])
        for te in text_elements:
            if "textRun" in te:
                content = te["textRun"].get("content", "").strip()
                if content and len(content) > 3:
                    return content[:60]
    return "(sin titulo)"


def find_slides_by_pattern(slide_data, pattern):
    """Find slides matching a pattern in their title."""
    matches = []
    for slide in slide_data:
        if pattern.lower() in slide["title"].lower():
            matches.append(slide)
    return matches


def reorder_slides(new_order):
    """
    Reorder slides by moving them to new positions.
    new_order: list of tuples (slide_id, target_index)
    """
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        requests = []
        for slide_id, target_index in new_order:
            requests.append({
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": target_index
                }
            })

        if requests:
            body = {"requests": requests}
            response = slides_service.presentations().batchUpdate(
                presentationId=PRESENTATION_ID,
                body=body
            ).execute()
            print(f"Successfully reordered {len(requests)} slides")
            return True
        return False
    finally:
        db.close()


def move_slide_to_position(slide_id, target_index):
    """Move a single slide to a new position."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        body = {
            "requests": [{
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": target_index
                }
            }]
        }
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"Moved slide {slide_id} to position {target_index}")
        return True
    finally:
        db.close()


def insert_image(slide_id, image_url, position=None, size=None):
    """
    Insert an image into a slide.

    Args:
        slide_id: The ID of the slide to insert the image into
        image_url: Public URL of the image
        position: dict with 'x' and 'y' in EMUs (optional)
        size: dict with 'width' and 'height' in EMUs (optional)
    """
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        # Default position and size if not provided
        if position is None:
            position = {"x": 1000000, "y": 1500000}  # 1 inch from left, 1.5 inch from top
        if size is None:
            size = {"width": 7000000, "height": 4000000}  # ~7x4 inches

        requests = [{
            "createImage": {
                "url": image_url,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": position["x"],
                        "translateY": position["y"],
                        "unit": "EMU"
                    },
                    "size": {
                        "width": {"magnitude": size["width"], "unit": "EMU"},
                        "height": {"magnitude": size["height"], "unit": "EMU"}
                    }
                }
            }
        }]

        body = {"requests": requests}
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"Inserted image into slide {slide_id}")
        return True
    except Exception as e:
        print(f"ERROR inserting image: {e}")
        return False
    finally:
        db.close()


def analyze_slide_order():
    """Analyze the current slide order and identify issues."""
    slide_data = get_presentation_structure()
    if not slide_data:
        return

    print("\n" + "=" * 80)
    print("ANALYSIS: Identifying order issues")
    print("=" * 80)

    # Find specific section slides
    latam_slides = find_slides_by_pattern(slide_data, "LATAM")
    hallazgos_slides = find_slides_by_pattern(slide_data, "Hallazgo")
    rec_slides = find_slides_by_pattern(slide_data, "Recomendaci")
    propuesta_slides = find_slides_by_pattern(slide_data, "Propuesta BID")

    print(f"\nLATAM slides: {len(latam_slides)}")
    for s in latam_slides:
        print(f"  {s['index']:3d}. {s['title']}")

    print(f"\nHallazgos slides: {len(hallazgos_slides)}")
    for s in hallazgos_slides:
        print(f"  {s['index']:3d}. {s['title']}")

    print(f"\nRecomendaciones slides: {len(rec_slides)}")
    for s in rec_slides:
        print(f"  {s['index']:3d}. {s['title']}")

    print(f"\nPropuesta BID slides: {len(propuesta_slides)}")
    for s in propuesta_slides:
        print(f"  {s['index']:3d}. {s['title']}")

    return slide_data


def delete_slide(slide_id):
    """Delete a slide by ID."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        body = {
            "requests": [{
                "deleteObject": {
                    "objectId": slide_id
                }
            }]
        }
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"Deleted slide {slide_id}")
        return True
    except Exception as e:
        print(f"ERROR deleting slide: {e}")
        return False
    finally:
        db.close()


def update_slide_text(slide_id, old_text, new_text):
    """Replace text in a specific slide."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        body = {
            "requests": [{
                "replaceAllText": {
                    "containsText": {
                        "text": old_text,
                        "matchCase": True
                    },
                    "replaceText": new_text,
                    "pageObjectIds": [slide_id]
                }
            }]
        }
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"Replaced '{old_text}' with '{new_text}' in slide {slide_id}")
        return True
    except Exception as e:
        print(f"ERROR updating text: {e}")
        return False
    finally:
        db.close()


def batch_update_requests(requests):
    """Execute a batch of update requests."""
    db = SessionLocal()
    try:
        slides_service = build_slides_service(db)
        if not slides_service:
            print("ERROR: Google integration not connected.")
            return False

        body = {"requests": requests}
        response = slides_service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body=body
        ).execute()
        print(f"Executed {len(requests)} batch requests")
        return response
    except Exception as e:
        print(f"ERROR in batch update: {e}")
        return None
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BID Slides Manager")
    parser.add_argument("command", choices=["structure", "analyze", "move", "delete", "insert-image"],
                        help="Command to execute")
    parser.add_argument("--slide-id", help="Slide ID for move/delete/insert operations")
    parser.add_argument("--target-index", type=int, help="Target index for move operation")
    parser.add_argument("--image-url", help="Image URL for insert-image operation")

    args = parser.parse_args()

    if args.command == "structure":
        get_presentation_structure()
    elif args.command == "analyze":
        analyze_slide_order()
    elif args.command == "move":
        if args.slide_id and args.target_index is not None:
            move_slide_to_position(args.slide_id, args.target_index)
        else:
            print("ERROR: --slide-id and --target-index required for move command")
    elif args.command == "delete":
        if args.slide_id:
            delete_slide(args.slide_id)
        else:
            print("ERROR: --slide-id required for delete command")
    elif args.command == "insert-image":
        if args.slide_id and args.image_url:
            insert_image(args.slide_id, args.image_url)
        else:
            print("ERROR: --slide-id and --image-url required for insert-image command")
