#!/usr/bin/env python3
"""
Upload graph PNGs to Google Drive and insert them into BID presentation.

This script:
1. Uploads PNG files from illanes00-graphs/static to Google Drive
2. Makes them publicly accessible
3. Inserts them into the appropriate slides in the BID presentation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from googleapiclient.http import MediaFileUpload

from app.db.session import SessionLocal
from app.services.google import build_drive_service, build_slides_service

PRESENTATION_ID = "1fZTThHJgwm8wJsVoMpuSlmXkphHtDQ3UqTrb1apblr8"
GRAPHS_DIR = Path("/srv/projects/illanes00-graphs/static")

# Mapping of graph files to slide titles (partial match)
GRAPH_SLIDE_MAP = {
    "grafico1_gasto_70x_deflactado.png": "Evolución del gasto",  # slide 0 or data section
    "grafico3_gasto_70x_pctpib.png": "% del PIB",  # slide about % PIB
    "grafico5_gasto_70x_pctgasto.png": "% del",  # slide about % gasto
    "grafico8_cruzada_703.png": "composición",  # composition slide
}


def upload_file_to_drive(drive_service, file_path, folder_id=None):
    """Upload a file to Google Drive and return file ID and web view link."""
    file_metadata = {
        "name": file_path.name,
        "mimeType": "image/png",
    }
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(file_path), mimetype="image/png")

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink, webContentLink"
    ).execute()

    return file


def make_file_public(drive_service, file_id):
    """Make a file publicly accessible."""
    permission = {
        "type": "anyone",
        "role": "reader"
    }
    drive_service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()
    print(f"  Made {file_id} public")


def get_thumbnail_url(file_id):
    """Get a direct image URL from Google Drive file ID."""
    # Direct image URL format for Google Drive
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def find_slide_by_title(slides_service, title_pattern):
    """Find a slide by partial title match."""
    presentation = slides_service.presentations().get(
        presentationId=PRESENTATION_ID
    ).execute()

    for slide in presentation.get("slides", []):
        for element in slide.get("pageElements", []):
            shape = element.get("shape", {})
            text_elements = shape.get("text", {}).get("textElements", [])
            for te in text_elements:
                if "textRun" in te:
                    content = te["textRun"].get("content", "").strip().lower()
                    if title_pattern.lower() in content:
                        return slide.get("objectId")

    return None


def insert_image_to_slide(slides_service, slide_id, image_url, description="Graph"):
    """Insert an image into a slide."""
    # Image dimensions and position (in EMU - 914400 EMU per inch)
    requests = [{
        "createImage": {
            "url": image_url,
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "width": {"magnitude": 6500000, "unit": "EMU"},  # ~7 inches
                    "height": {"magnitude": 4000000, "unit": "EMU"}  # ~4.4 inches
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": 500000,  # ~0.5 inch from left
                    "translateY": 1200000,  # ~1.3 inches from top
                    "unit": "EMU"
                }
            }
        }
    }]

    body = {"requests": requests}
    response = slides_service.presentations().batchUpdate(
        presentationId=PRESENTATION_ID,
        body=body
    ).execute()

    print(f"  ✓ Inserted {description} into slide {slide_id[:15]}...")
    return response


def main():
    """Main function to upload graphs and insert into slides."""
    db = SessionLocal()

    try:
        drive_service = build_drive_service(db)
        slides_service = build_slides_service(db)

        if not drive_service or not slides_service:
            print("ERROR: Google services not available. Please connect first.")
            return

        print("=" * 80)
        print("UPLOADING GRAPHS TO GOOGLE DRIVE")
        print("=" * 80)

        uploaded_files = {}

        for graph_file, slide_pattern in GRAPH_SLIDE_MAP.items():
            file_path = GRAPHS_DIR / graph_file

            if not file_path.exists():
                print(f"  ⚠ File not found: {file_path}")
                continue

            print(f"\nUploading: {graph_file}")

            # Upload to Drive
            result = upload_file_to_drive(drive_service, file_path)
            file_id = result.get("id")
            print(f"  Uploaded: {file_id}")

            # Make public
            make_file_public(drive_service, file_id)

            # Store info
            uploaded_files[graph_file] = {
                "file_id": file_id,
                "url": get_thumbnail_url(file_id),
                "slide_pattern": slide_pattern
            }

        print("\n" + "=" * 80)
        print("UPLOADED FILES")
        print("=" * 80)
        for name, info in uploaded_files.items():
            print(f"  {name}: {info['url']}")

        print("\n" + "=" * 80)
        print("INSERTING IMAGES INTO SLIDES")
        print("=" * 80)

        for graph_name, info in uploaded_files.items():
            slide_id = find_slide_by_title(slides_service, info["slide_pattern"])

            if slide_id:
                try:
                    insert_image_to_slide(
                        slides_service,
                        slide_id,
                        info["url"],
                        description=graph_name
                    )
                except Exception as e:
                    print(f"  ✗ Failed to insert {graph_name}: {e}")
            else:
                print(f"  ⚠ No slide found matching '{info['slide_pattern']}' for {graph_name}")

        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
