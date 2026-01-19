"""Tests for PPTX export endpoint."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

_ONE_BY_ONE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestPptxExport:
    """Test branded PPTX export endpoint."""

    def test_export_pptx_stream(self, client):
        create = client.post(
            "/api/v1/documents",
            json={
                "title": "My Presentation",
                "doc_type": "presentation",
                "content": {},
                "front_matter": {
                    "slides_data": {
                        "slides": [
                            {
                                "id": "slide-1",
                                "slideNumber": 1,
                                "layout": "title",
                                "title": "Hello",
                                "content": "Subtitle",
                                "notes": "",
                            },
                            {
                                "id": "slide-2",
                                "slideNumber": 2,
                                "layout": "content",
                                "title": "Body",
                                "content": "<ul><li>One</li><li>Two</li></ul>",
                                "notes": "",
                            },
                        ],
                        "theme": {
                            "primaryColor": "#1a365d",
                            "secondaryColor": "#c53030",
                            "fontFamily": "IBM Plex Sans",
                        },
                    }
                },
            },
        )
        assert create.status_code == 201
        slug = create.json()["slug"]

        response = client.post(f"/api/v1/exports/{slug}/export-pptx")
        assert response.status_code == 200
        assert (
            response.headers.get("content-type")
            == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        # PPTX is a ZIP container
        assert response.content[:2] == b"PK"

    def test_export_pptx_embeds_images(self, client):
        backend_dir = Path(__file__).resolve().parents[1]
        image_path = backend_dir / "uploads" / "assets" / "test-export-image.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(_ONE_BY_ONE_PNG)
        try:
            create = client.post(
                "/api/v1/documents",
                json={
                    "title": "Presentation With Images",
                    "doc_type": "presentation",
                    "content": {},
                    "front_matter": {
                        "slides_data": {
                            "slides": [
                                {
                                    "id": "slide-1",
                                    "slideNumber": 1,
                                    "layout": "image-full",
                                    "title": "Image Slide",
                                    "content": '<img src="/uploads/assets/test-export-image.png" />',
                                    "notes": "",
                                }
                            ],
                            "theme": {
                                "primaryColor": "#1a365d",
                                "secondaryColor": "#c53030",
                                "fontFamily": "IBM Plex Sans",
                            },
                        }
                    },
                },
            )
            assert create.status_code == 201
            slug = create.json()["slug"]

            response = client.post(f"/api/v1/exports/{slug}/export-pptx")
            assert response.status_code == 200
            assert response.content[:2] == b"PK"

            with ZipFile(BytesIO(response.content)) as zf:
                media_files = [name for name in zf.namelist() if name.startswith("ppt/media/")]
                assert media_files
                assert any(name.lower().endswith(".png") for name in media_files)
        finally:
            image_path.unlink(missing_ok=True)

    def test_export_pptx_embeds_multiple_images(self, client):
        backend_dir = Path(__file__).resolve().parents[1]
        image_path_1 = backend_dir / "uploads" / "assets" / "test-export-image-1.png"
        image_path_2 = backend_dir / "uploads" / "assets" / "test-export-image-2.png"
        image_path_1.parent.mkdir(parents=True, exist_ok=True)
        image_path_1.write_bytes(_ONE_BY_ONE_PNG)
        image_path_2.write_bytes(_ONE_BY_ONE_PNG)

        try:
            create = client.post(
                "/api/v1/documents",
                json={
                    "title": "Presentation With Multiple Images",
                    "doc_type": "presentation",
                    "content": {},
                    "front_matter": {
                        "slides_data": {
                            "slides": [
                                {
                                    "id": "slide-1",
                                    "slideNumber": 1,
                                    "layout": "image-full",
                                    "title": "Two Images",
                                    "content": (
                                        '<img src="/uploads/assets/test-export-image-1.png" />'
                                        '<img src="/uploads/assets/test-export-image-2.png" />'
                                    ),
                                    "notes": "",
                                }
                            ],
                            "theme": {
                                "primaryColor": "#1a365d",
                                "secondaryColor": "#c53030",
                                "fontFamily": "IBM Plex Sans",
                            },
                        }
                    },
                },
            )
            assert create.status_code == 201
            slug = create.json()["slug"]

            response = client.post(f"/api/v1/exports/{slug}/export-pptx")
            assert response.status_code == 200
            assert response.content[:2] == b"PK"

            with ZipFile(BytesIO(response.content)) as zf:
                slide_xml_files = sorted(
                    name
                    for name in zf.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
                assert slide_xml_files
                slide_xml = zf.read(slide_xml_files[0]).decode("utf-8", errors="replace")
                assert slide_xml.count("<p:pic") >= 2
        finally:
            image_path_1.unlink(missing_ok=True)
            image_path_2.unlink(missing_ok=True)

    def test_export_pptx_includes_speaker_notes(self, client):
        create = client.post(
            "/api/v1/documents",
            json={
                "title": "Presentation With Notes",
                "doc_type": "presentation",
                "content": {},
                "front_matter": {
                    "slides_data": {
                        "slides": [
                            {
                                "id": "slide-1",
                                "slideNumber": 1,
                                "layout": "content",
                                "title": "Notes",
                                "content": "<p>Hello</p>",
                                "notes": "Speaker notes here",
                            }
                        ],
                        "theme": {
                            "primaryColor": "#1a365d",
                            "secondaryColor": "#c53030",
                            "fontFamily": "IBM Plex Sans",
                        },
                    }
                },
            },
        )
        assert create.status_code == 201
        slug = create.json()["slug"]

        response = client.post(f"/api/v1/exports/{slug}/export-pptx")
        assert response.status_code == 200
        assert response.content[:2] == b"PK"

        with ZipFile(BytesIO(response.content)) as zf:
            notes_files = sorted(
                name
                for name in zf.namelist()
                if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
            )
            assert notes_files
            notes_xml = "\n".join(
                zf.read(name).decode("utf-8", errors="replace") for name in notes_files
            )
            assert "Speaker notes here" in notes_xml
