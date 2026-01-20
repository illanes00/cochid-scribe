"""Tests for Google Docs sync functionality."""

import json
import pytest

from app.services.google_docs_transform import (
    TipTapToGoogleDocs,
    GoogleDocsToTipTap,
    compute_content_hash,
    CLAIM_MARKER,
    CITATION_MARKER,
    MARKER_END,
)


class TestContentHash:
    """Tests for content hash computation."""

    def test_identical_content_same_hash(self):
        """Same content should produce the same hash."""
        content1 = {"type": "doc", "content": [{"type": "paragraph"}]}
        content2 = {"type": "doc", "content": [{"type": "paragraph"}]}

        assert compute_content_hash(content1) == compute_content_hash(content2)

    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        content1 = {"type": "doc", "content": [{"type": "paragraph"}]}
        content2 = {"type": "doc", "content": [{"type": "heading"}]}

        assert compute_content_hash(content1) != compute_content_hash(content2)

    def test_key_order_independent(self):
        """Hash should be independent of key ordering."""
        content1 = {"type": "doc", "content": []}
        content2 = {"content": [], "type": "doc"}

        assert compute_content_hash(content1) == compute_content_hash(content2)

    def test_empty_content(self):
        """Empty content should produce a consistent hash."""
        hash1 = compute_content_hash({})
        hash2 = compute_content_hash({})

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters


class TestTipTapToGoogleDocs:
    """Tests for TipTap to Google Docs transformation."""

    def test_transform_empty_document(self):
        """Empty document should produce minimal requests."""
        transformer = TipTapToGoogleDocs()
        result = transformer.transform({"type": "doc", "content": []})

        assert result.requests == []
        assert result.warnings == []

    def test_transform_simple_paragraph(self):
        """Simple paragraph should produce insertText and updateParagraphStyle."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello, world!"}],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Should have at least insertText and updateParagraphStyle
        insert_requests = [r for r in result.requests if "insertText" in r]
        style_requests = [r for r in result.requests if "updateParagraphStyle" in r]

        assert len(insert_requests) >= 1
        assert len(style_requests) >= 1

        # Verify text content
        text_inserted = "".join(
            r["insertText"]["text"] for r in insert_requests
        )
        assert "Hello, world!" in text_inserted

    def test_transform_heading(self):
        """Heading should produce updateParagraphStyle with heading type."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "My Title"}],
                }
            ],
        }

        result = transformer.transform(tiptap)

        style_requests = [r for r in result.requests if "updateParagraphStyle" in r]
        assert len(style_requests) >= 1

        # Check for heading style
        heading_styles = [
            r for r in style_requests
            if r["updateParagraphStyle"]["paragraphStyle"].get("namedStyleType", "").startswith("HEADING")
        ]
        assert len(heading_styles) >= 1

    def test_transform_bold_text(self):
        """Bold text should produce updateTextStyle with bold."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bold text",
                            "marks": [{"type": "bold"}],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        style_requests = [r for r in result.requests if "updateTextStyle" in r]
        bold_requests = [
            r for r in style_requests
            if r["updateTextStyle"]["textStyle"].get("bold") is True
        ]
        assert len(bold_requests) >= 1

    def test_transform_link(self):
        """Link should produce updateTextStyle with link URL."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Click here",
                            "marks": [
                                {
                                    "type": "link",
                                    "attrs": {"href": "https://example.com"},
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        style_requests = [r for r in result.requests if "updateTextStyle" in r]
        link_requests = [
            r for r in style_requests
            if r["updateTextStyle"]["textStyle"].get("link", {}).get("url") == "https://example.com"
        ]
        assert len(link_requests) >= 1

    def test_transform_claim_creates_highlight_and_footnote(self):
        """Claim mark should create yellow highlight and footnote."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a claim.",
                            "marks": [
                                {
                                    "type": "claim",
                                    "attrs": {
                                        "claimId": "C-123",
                                        "claimType": "DATA",
                                        "status": "verified",
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Should have a highlight
        style_requests = [r for r in result.requests if "updateTextStyle" in r]
        highlight_requests = [
            r for r in style_requests
            if "backgroundColor" in r["updateTextStyle"]["textStyle"]
        ]
        assert len(highlight_requests) >= 1

        # Should track claim count
        assert result.claims_count >= 1

    def test_transform_citation(self):
        """Citation node should create citation text and footnote."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "citation",
                            "attrs": {"bibKey": "Smith2024", "locator": "p.42"},
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Should insert citation text
        insert_requests = [r for r in result.requests if "insertText" in r]
        text_inserted = "".join(
            r["insertText"]["text"] for r in insert_requests
        )
        assert "Smith2024" in text_inserted

        # Should track citation count
        assert result.citations_count >= 1


class TestGoogleDocsToTipTap:
    """Tests for Google Docs to TipTap transformation."""

    def test_transform_empty_document(self):
        """Empty Google Doc should produce empty TipTap content."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {"content": []},
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert tiptap_json["type"] == "doc"
        assert tiptap_json["content"] == []

    def test_transform_simple_paragraph(self):
        """Simple paragraph should transform correctly."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Hello, world!\n",
                                        "textStyle": {},
                                    }
                                }
                            ],
                        }
                    }
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert len(tiptap_json["content"]) >= 1
        assert tiptap_json["content"][0]["type"] == "paragraph"
        assert tiptap_json["content"][0]["content"][0]["text"] == "Hello, world!"

    def test_transform_heading(self):
        """Heading should transform with correct level."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "HEADING_2"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Section Title\n",
                                        "textStyle": {},
                                    }
                                }
                            ],
                        }
                    }
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert tiptap_json["content"][0]["type"] == "heading"
        assert tiptap_json["content"][0]["attrs"]["level"] == 2

    def test_transform_bold_text(self):
        """Bold text should have bold mark."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Bold text\n",
                                        "textStyle": {"bold": True},
                                    }
                                }
                            ],
                        }
                    }
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        text_node = tiptap_json["content"][0]["content"][0]
        assert "marks" in text_node
        mark_types = [m["type"] for m in text_node["marks"]]
        assert "bold" in mark_types

    def test_transform_link(self):
        """Link should transform with href attribute."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Click here\n",
                                        "textStyle": {
                                            "link": {"url": "https://example.com"}
                                        },
                                    }
                                }
                            ],
                        }
                    }
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        text_node = tiptap_json["content"][0]["content"][0]
        assert "marks" in text_node
        link_marks = [m for m in text_node["marks"] if m["type"] == "link"]
        assert len(link_marks) >= 1
        assert link_marks[0]["attrs"]["href"] == "https://example.com"

    def test_extract_citation_from_footnote(self):
        """Citation metadata in footnote should be restored."""
        transformer = GoogleDocsToTipTap()
        citation_data = {"bibKey": "Jones2023", "locator": "ch.5"}
        footnote_text = f"{CITATION_MARKER}{json.dumps(citation_data)}{MARKER_END}"

        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Some text ",
                                        "textStyle": {},
                                    }
                                },
                                {
                                    "footnoteReference": {
                                        "footnoteId": "fn1",
                                    }
                                },
                                {
                                    "textRun": {
                                        "content": "\n",
                                        "textStyle": {},
                                    }
                                },
                            ],
                        }
                    }
                ]
            },
            "footnotes": {
                "fn1": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [
                                    {
                                        "textRun": {
                                            "content": footnote_text,
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            },
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert citations >= 1

    def test_transform_table(self):
        """Table should transform to table node."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "table": {
                            "rows": 2,
                            "columns": 2,
                            "tableRows": [
                                {
                                    "tableCells": [
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "paragraphStyle": {},
                                                        "elements": [
                                                            {
                                                                "textRun": {
                                                                    "content": "Cell 1\n",
                                                                    "textStyle": {},
                                                                }
                                                            }
                                                        ],
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "paragraphStyle": {},
                                                        "elements": [
                                                            {
                                                                "textRun": {
                                                                    "content": "Cell 2\n",
                                                                    "textStyle": {},
                                                                }
                                                            }
                                                        ],
                                                    }
                                                }
                                            ]
                                        },
                                    ]
                                },
                                {
                                    "tableCells": [
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "paragraphStyle": {},
                                                        "elements": [
                                                            {
                                                                "textRun": {
                                                                    "content": "Cell 3\n",
                                                                    "textStyle": {},
                                                                }
                                                            }
                                                        ],
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "paragraphStyle": {},
                                                        "elements": [
                                                            {
                                                                "textRun": {
                                                                    "content": "Cell 4\n",
                                                                    "textStyle": {},
                                                                }
                                                            }
                                                        ],
                                                    }
                                                }
                                            ]
                                        },
                                    ]
                                },
                            ],
                        }
                    }
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert tiptap_json["content"][0]["type"] == "table"
        assert len(tiptap_json["content"][0]["content"]) == 2  # 2 rows


class TestMarkerFormats:
    """Tests for marker format constants."""

    def test_claim_marker_format(self):
        """Claim marker should be parseable."""
        data = {"claimId": "C-test", "claimType": "DATA", "status": "draft"}
        marker = f"{CLAIM_MARKER}{json.dumps(data)}{MARKER_END}"

        assert CLAIM_MARKER in marker
        assert MARKER_END in marker

        # Extract and parse
        import re
        match = re.search(
            rf"{re.escape(CLAIM_MARKER)}(.+?){re.escape(MARKER_END)}",
            marker
        )
        assert match is not None
        parsed = json.loads(match.group(1))
        assert parsed["claimId"] == "C-test"

    def test_citation_marker_format(self):
        """Citation marker should be parseable."""
        data = {"bibKey": "Test2024", "locator": "p.1"}
        marker = f"{CITATION_MARKER}{json.dumps(data)}{MARKER_END}"

        assert CITATION_MARKER in marker
        assert MARKER_END in marker

        # Extract and parse
        import re
        match = re.search(
            rf"{re.escape(CITATION_MARKER)}(.+?){re.escape(MARKER_END)}",
            marker
        )
        assert match is not None
        parsed = json.loads(match.group(1))
        assert parsed["bibKey"] == "Test2024"


# ==================== Google Slides Transform Tests ====================

from app.services.google_slides_transform import (
    ScribeToGoogleSlides,
    GoogleSlidesToScribe,
    delete_all_slides_requests,
    LAYOUT_MAPPING,
)


class TestScribeToGoogleSlides:
    """Tests for Scribe slides_data to Google Slides transformation."""

    def test_transform_empty_presentation(self):
        """Empty slides_data should produce no requests."""
        transformer = ScribeToGoogleSlides()
        slides_data = {"slides": [], "theme": {}}

        requests, warnings = transformer.transform(slides_data, "pres-123")

        assert requests == []
        assert warnings == []

    def test_transform_single_slide(self):
        """Single slide should produce createSlide and text requests."""
        transformer = ScribeToGoogleSlides()
        slides_data = {
            "slides": [
                {
                    "id": "slide-1",
                    "slideNumber": 1,
                    "layout": "content",
                    "title": "My Title",
                    "content": "Some content here",
                    "notes": "",
                }
            ],
            "theme": {},
        }

        requests, warnings = transformer.transform(slides_data, "pres-123")

        # Should have createSlide request
        create_requests = [r for r in requests if "createSlide" in r]
        assert len(create_requests) >= 1

        # Should have text box creation
        shape_requests = [r for r in requests if "createShape" in r]
        assert len(shape_requests) >= 1

    def test_transform_title_slide(self):
        """Title layout should create centered title."""
        transformer = ScribeToGoogleSlides()
        slides_data = {
            "slides": [
                {
                    "id": "slide-1",
                    "slideNumber": 1,
                    "layout": "title",
                    "title": "Presentation Title",
                    "content": "Subtitle text",
                    "notes": "",
                }
            ],
            "theme": {},
        }

        requests, warnings = transformer.transform(slides_data, "pres-123")

        # Should have createSlide with TITLE layout
        create_requests = [r for r in requests if "createSlide" in r]
        assert len(create_requests) == 1

    def test_transform_with_markdown_content(self):
        """Content with markdown should be parsed correctly."""
        transformer = ScribeToGoogleSlides()
        slides_data = {
            "slides": [
                {
                    "id": "slide-1",
                    "slideNumber": 1,
                    "layout": "content",
                    "title": "Bullet Points",
                    "content": "- First point\n- Second point\n- Third point",
                    "notes": "",
                }
            ],
            "theme": {},
        }

        requests, warnings = transformer.transform(slides_data, "pres-123")

        # Should have insertText with bullet markers
        insert_requests = [r for r in requests if "insertText" in r]
        assert len(insert_requests) >= 1

        # Check bullet conversion
        all_text = "".join(r["insertText"]["text"] for r in insert_requests)
        assert "•" in all_text

    def test_transform_two_column_layout(self):
        """Two-column layout should create two text boxes."""
        transformer = ScribeToGoogleSlides()
        slides_data = {
            "slides": [
                {
                    "id": "slide-1",
                    "slideNumber": 1,
                    "layout": "two-column",
                    "title": "Comparison",
                    "content": "Left column content|||Right column content",
                    "notes": "",
                }
            ],
            "theme": {},
        }

        requests, warnings = transformer.transform(slides_data, "pres-123")

        # Should have multiple text boxes (title + 2 columns)
        shape_requests = [r for r in requests if "createShape" in r]
        assert len(shape_requests) >= 2

    def test_transform_with_image(self):
        """Slide with image URL should create image element."""
        transformer = ScribeToGoogleSlides()
        slides_data = {
            "slides": [
                {
                    "id": "slide-1",
                    "slideNumber": 1,
                    "layout": "image-full",
                    "title": "Image Slide",
                    "content": "",
                    "imageUrl": "https://example.com/image.png",
                    "notes": "",
                }
            ],
            "theme": {},
        }

        requests, warnings = transformer.transform(slides_data, "pres-123")

        # Should have createImage request
        image_requests = [r for r in requests if "createImage" in r]
        assert len(image_requests) >= 1
        assert image_requests[0]["createImage"]["url"] == "https://example.com/image.png"


class TestGoogleSlidesToScribe:
    """Tests for Google Slides to Scribe slides_data transformation."""

    def test_transform_empty_presentation(self):
        """Empty presentation should produce empty slides array."""
        transformer = GoogleSlidesToScribe()
        presentation = {"slides": [], "masters": []}

        slides_data, warnings = transformer.transform(presentation)

        assert slides_data["slides"] == []
        assert "theme" in slides_data

    def test_transform_single_slide(self):
        """Single slide should extract title and content."""
        transformer = GoogleSlidesToScribe()
        presentation = {
            "slides": [
                {
                    "objectId": "slide-abc",
                    "slideProperties": {"layoutObjectId": "title_and_body"},
                    "pageElements": [
                        {
                            "shape": {
                                "placeholder": {"type": "TITLE"},
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "My Title"}}
                                    ]
                                },
                            }
                        },
                        {
                            "shape": {
                                "placeholder": {"type": "BODY"},
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Body content"}}
                                    ]
                                },
                            }
                        },
                    ],
                }
            ],
            "masters": [],
        }

        slides_data, warnings = transformer.transform(presentation)

        assert len(slides_data["slides"]) == 1
        assert slides_data["slides"][0]["title"] == "My Title"
        assert "Body content" in slides_data["slides"][0]["content"]

    def test_extract_bold_text_as_markdown(self):
        """Bold text should be converted to markdown."""
        transformer = GoogleSlidesToScribe()
        presentation = {
            "slides": [
                {
                    "objectId": "slide-abc",
                    "slideProperties": {},
                    "pageElements": [
                        {
                            "shape": {
                                "placeholder": {"type": "BODY"},
                                "text": {
                                    "textElements": [
                                        {
                                            "textRun": {
                                                "content": "Bold text",
                                                "style": {"bold": True},
                                            }
                                        }
                                    ]
                                },
                            }
                        },
                    ],
                }
            ],
            "masters": [],
        }

        slides_data, warnings = transformer.transform(presentation)

        content = slides_data["slides"][0]["content"]
        assert "**Bold text**" in content

    def test_extract_speaker_notes(self):
        """Speaker notes should be extracted."""
        transformer = GoogleSlidesToScribe()
        presentation = {
            "slides": [
                {
                    "objectId": "slide-abc",
                    "slideProperties": {
                        "notesPage": {
                            "pageElements": [
                                {
                                    "shape": {
                                        "placeholder": {"type": "BODY"},
                                        "text": {
                                            "textElements": [
                                                {"textRun": {"content": "Speaker notes here"}}
                                            ]
                                        },
                                    }
                                }
                            ]
                        }
                    },
                    "pageElements": [],
                }
            ],
            "masters": [],
        }

        slides_data, warnings = transformer.transform(presentation)

        assert slides_data["slides"][0]["notes"] == "Speaker notes here"

    def test_extract_image_url(self):
        """Image URLs should be extracted."""
        transformer = GoogleSlidesToScribe()
        presentation = {
            "slides": [
                {
                    "objectId": "slide-abc",
                    "slideProperties": {},
                    "pageElements": [
                        {
                            "image": {
                                "contentUrl": "https://example.com/image.png",
                            }
                        }
                    ],
                }
            ],
            "masters": [],
        }

        slides_data, warnings = transformer.transform(presentation)

        assert slides_data["slides"][0]["imageUrl"] == "https://example.com/image.png"

    def test_extract_theme_colors(self):
        """Theme colors should be extracted from master."""
        transformer = GoogleSlidesToScribe()
        presentation = {
            "slides": [],
            "masters": [
                {
                    "pageProperties": {
                        "colorScheme": {
                            "colors": [
                                {"type": "DARK1", "color": {"rgbColor": {"red": 0.1, "green": 0.2, "blue": 0.3}}},
                                {"type": "ACCENT1", "color": {"rgbColor": {"red": 0.8, "green": 0.2, "blue": 0.2}}},
                            ]
                        }
                    }
                }
            ],
        }

        slides_data, warnings = transformer.transform(presentation)

        assert slides_data["theme"]["primaryColor"] == "#19334c"
        assert slides_data["theme"]["secondaryColor"] == "#cc3333"


class TestDeleteSlidesRequests:
    """Tests for delete slides helper function."""

    def test_delete_all_slides(self):
        """Should create delete requests for all slides."""
        presentation = {
            "slides": [
                {"objectId": "slide-1"},
                {"objectId": "slide-2"},
                {"objectId": "slide-3"},
            ]
        }

        requests = delete_all_slides_requests(presentation)

        assert len(requests) == 3
        assert all("deleteObject" in r for r in requests)
        object_ids = [r["deleteObject"]["objectId"] for r in requests]
        assert set(object_ids) == {"slide-1", "slide-2", "slide-3"}

    def test_delete_empty_presentation(self):
        """Empty presentation should produce no delete requests."""
        presentation = {"slides": []}

        requests = delete_all_slides_requests(presentation)

        assert requests == []


# ==================== Additional Feature Tests ====================

class TestTaskListRoundTrip:
    """Tests for task list (checkbox) round-trip."""

    def test_push_task_list_creates_checkbox_markers(self):
        """Task list push should create [ ] and [x] markers."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "taskList",
                    "content": [
                        {
                            "type": "taskItem",
                            "attrs": {"checked": False},
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Unchecked task"}],
                                }
                            ],
                        },
                        {
                            "type": "taskItem",
                            "attrs": {"checked": True},
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Checked task"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Check that text was inserted with markers
        insert_requests = [r for r in result.requests if "insertText" in r]
        all_text = "".join(r["insertText"]["text"] for r in insert_requests)

        assert "[ ]" in all_text
        assert "[x]" in all_text

    def test_pull_task_list_restores_checked_state(self):
        """Task list markers should restore to taskList with correct checked state."""
        transformer = GoogleDocsToTipTap()
        google_doc = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "bullet": {"listId": "list1"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "[ ] Unchecked task\n",
                                        "textStyle": {},
                                    }
                                }
                            ],
                        }
                    },
                    {
                        "paragraph": {
                            "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                            "bullet": {"listId": "list1"},
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "[x] Checked task\n",
                                        "textStyle": {},
                                    }
                                }
                            ],
                        }
                    },
                ]
            },
            "footnotes": {},
        }

        tiptap_json, claims, citations, warnings = transformer.transform(google_doc)

        assert len(tiptap_json["content"]) >= 1
        task_list = tiptap_json["content"][0]
        assert task_list["type"] == "taskList"
        assert len(task_list["content"]) == 2

        # First item unchecked
        assert task_list["content"][0]["type"] == "taskItem"
        assert task_list["content"][0]["attrs"]["checked"] is False

        # Second item checked
        assert task_list["content"][1]["type"] == "taskItem"
        assert task_list["content"][1]["attrs"]["checked"] is True


class TestClaimMapping:
    """Tests for claim mapping with text anchors."""

    def test_push_claim_stores_text_anchor(self):
        """Claims should store text content for restoration."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This claim text",
                            "marks": [
                                {
                                    "type": "claim",
                                    "attrs": {
                                        "claimId": "C-test",
                                        "claimType": "DATA",
                                        "status": "verified",
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Check that footnote contains text anchor
        assert len(result.footnotes) >= 1
        claim_footnote = result.footnotes[0]
        assert claim_footnote["type"] == "claim"
        assert claim_footnote["data"]["text"] == "This claim text"
        assert "textHash" in claim_footnote["data"]


class TestImagePlaceholders:
    """Tests for image placeholder handling."""

    def test_push_base64_image_creates_placeholder(self):
        """Base64 images should be converted to placeholders."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "image",
                    "attrs": {
                        "src": "data:image/png;base64,iVBORw0KGgo=",
                        "alt": "Test image",
                    },
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Should have inserted placeholder text
        insert_requests = [r for r in result.requests if "insertText" in r]
        all_text = "".join(r["insertText"]["text"] for r in insert_requests)

        assert "[📷 Image:" in all_text
        assert len(result.warnings) >= 1


class TestBlockquoteStyles:
    """Tests for blockquote styling."""

    def test_blockquote_has_border_and_indentation(self):
        """Blockquotes should have left border and indentation."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "blockquote",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Quoted text"}],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Check for paragraph style with border
        style_requests = [r for r in result.requests if "updateParagraphStyle" in r]
        border_requests = [
            r for r in style_requests
            if "borderLeft" in r["updateParagraphStyle"]["paragraphStyle"]
        ]

        assert len(border_requests) >= 1


class TestTableContent:
    """Tests for table content handling."""

    def test_table_cells_have_content(self):
        """Table cells should have their content inserted."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {
                                    "type": "tableCell",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Cell A"}],
                                        }
                                    ],
                                },
                                {
                                    "type": "tableCell",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Cell B"}],
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Should have insertTable and insertText for cells
        table_requests = [r for r in result.requests if "insertTable" in r]
        insert_requests = [r for r in result.requests if "insertText" in r]

        assert len(table_requests) >= 1
        all_text = "".join(r["insertText"]["text"] for r in insert_requests)
        assert "Cell A" in all_text
        assert "Cell B" in all_text

    def test_table_index_calculation_2x3(self):
        """Test that table cell indices are calculated correctly for 2x3 table."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "A1"}]}]},
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "B1"}]}]},
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "C1"}]}]},
                            ],
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "A2"}]}]},
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "B2"}]}]},
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "C2"}]}]},
                            ],
                        },
                    ],
                }
            ],
        }

        result = transformer.transform(tiptap)

        # Find table insert
        table_requests = [r for r in result.requests if "insertTable" in r]
        assert len(table_requests) == 1

        table_req = table_requests[0]["insertTable"]
        assert table_req["rows"] == 2
        assert table_req["columns"] == 3

        # Find cell insertions (should be in reverse order)
        cell_inserts = [r for r in result.requests if "insertText" in r and r["insertText"]["text"] in ["A1", "B1", "C1", "A2", "B2", "C2"]]

        # All 6 cells should have inserts
        assert len(cell_inserts) == 6

        # Verify indices use the correct formula
        # Formula: table_start + 1 + 3 + row * (cols * 2 + 1) + col * 2
        # For table at index 1: cell[0][0] should be at 1 + 1 + 3 + 0 + 0 = 5
        # But we insert in reverse, so check that indices are in descending order
        indices = [r["insertText"]["location"]["index"] for r in cell_inserts]
        assert indices == sorted(indices, reverse=True), "Cell inserts should be in reverse index order"

    def test_table_with_content_before_and_after(self):
        """Test table with paragraph before and after."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Before table"}],
                },
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "X"}]}]},
                            ],
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "After table"}],
                },
            ],
        }

        result = transformer.transform(tiptap)

        # Should have 3 main content areas
        all_text = "".join(
            r["insertText"]["text"]
            for r in result.requests
            if "insertText" in r
        )

        assert "Before table" in all_text
        assert "X" in all_text
        assert "After table" in all_text

        # "After table" insert should have an index greater than all table content
        after_table_req = [
            r for r in result.requests
            if "insertText" in r and "After table" in r["insertText"]["text"]
        ]
        assert len(after_table_req) == 1

    def test_multiple_tables(self):
        """Test document with multiple tables."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Table1"}]}]},
                            ],
                        },
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Between"}],
                },
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Table2"}]}]},
                            ],
                        },
                    ],
                },
            ],
        }

        result = transformer.transform(tiptap)

        # Should have 2 insertTable requests
        table_requests = [r for r in result.requests if "insertTable" in r]
        assert len(table_requests) == 2

        # All content should be present
        all_text = "".join(
            r["insertText"]["text"]
            for r in result.requests
            if "insertText" in r
        )
        assert "Table1" in all_text
        assert "Between" in all_text
        assert "Table2" in all_text

    def test_empty_table_skipped(self):
        """Empty tables should be skipped with a warning."""
        transformer = TipTapToGoogleDocs()
        tiptap = {
            "type": "doc",
            "content": [
                {
                    "type": "table",
                    "content": [],  # Empty table
                },
            ],
        }

        result = transformer.transform(tiptap)

        # No table should be inserted
        table_requests = [r for r in result.requests if "insertTable" in r]
        assert len(table_requests) == 0

        # Should have warning
        assert any("Empty table" in w for w in result.warnings)


# Import HeaderFooterTransform for tests
from app.services.google_docs_transform import HeaderFooterTransform


class TestHeaderFooterTransform:
    """Tests for header/footer transformation."""

    def test_create_header_footer_requests_with_header(self):
        """Header content should create a createHeader request."""
        header_content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Header"}]}],
        }

        requests = HeaderFooterTransform.create_header_footer_requests(
            header_content=header_content,
            footer_content=None,
        )

        assert len(requests) == 1
        assert "createHeader" in requests[0]
        assert requests[0]["createHeader"]["type"] == "DEFAULT"

    def test_create_header_footer_requests_with_footer(self):
        """Footer content should create a createFooter request."""
        footer_content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Footer"}]}],
        }

        requests = HeaderFooterTransform.create_header_footer_requests(
            header_content=None,
            footer_content=footer_content,
        )

        assert len(requests) == 1
        assert "createFooter" in requests[0]
        assert requests[0]["createFooter"]["type"] == "DEFAULT"

    def test_create_header_footer_requests_with_both(self):
        """Both header and footer content should create both requests."""
        header_content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Header"}]}],
        }
        footer_content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Footer"}]}],
        }

        requests = HeaderFooterTransform.create_header_footer_requests(
            header_content=header_content,
            footer_content=footer_content,
        )

        assert len(requests) == 2
        assert "createHeader" in requests[0]
        assert "createFooter" in requests[1]

    def test_create_header_footer_requests_with_margins(self):
        """Page margins should create updateDocumentStyle request."""
        page_margins = {"top": 72, "bottom": 72, "left": 96, "right": 96}

        requests = HeaderFooterTransform.create_header_footer_requests(
            header_content=None,
            footer_content=None,
            page_margins=page_margins,
        )

        assert len(requests) == 1
        assert "updateDocumentStyle" in requests[0]
        style = requests[0]["updateDocumentStyle"]["documentStyle"]
        assert style["marginTop"]["magnitude"] == 72
        assert style["marginLeft"]["magnitude"] == 96

    def test_create_header_footer_requests_empty(self):
        """No content should produce no requests."""
        requests = HeaderFooterTransform.create_header_footer_requests(
            header_content=None,
            footer_content=None,
        )

        assert requests == []

    def test_create_header_content_requests(self):
        """Header content should produce insertText request."""
        content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "My Header"}]}],
        }

        requests = HeaderFooterTransform.create_header_content_requests(
            header_id="header-123",
            content=content,
        )

        assert len(requests) == 1
        assert "insertText" in requests[0]
        assert requests[0]["insertText"]["location"]["segmentId"] == "header-123"
        assert requests[0]["insertText"]["text"] == "My Header"

    def test_create_footer_content_requests(self):
        """Footer content should produce insertText request."""
        content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "My Footer"}]}],
        }

        requests = HeaderFooterTransform.create_footer_content_requests(
            footer_id="footer-456",
            content=content,
        )

        assert len(requests) == 1
        assert "insertText" in requests[0]
        assert requests[0]["insertText"]["location"]["segmentId"] == "footer-456"
        assert requests[0]["insertText"]["text"] == "My Footer"

    def test_header_with_variables(self):
        """Variables should be replaced in header content."""
        content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Page {pageNumber} of {totalPages}"}]}],
        }

        requests = HeaderFooterTransform.create_header_content_requests(
            header_id="header-123",
            content=content,
            variables={"pageNumber": 1, "totalPages": 10},
        )

        assert requests[0]["insertText"]["text"] == "Page 1 of 10"

    def test_footer_with_document_title(self):
        """Document title variable should be replaced."""
        content = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Document: {documentTitle}"}]}],
        }

        requests = HeaderFooterTransform.create_footer_content_requests(
            footer_id="footer-456",
            content=content,
            variables={"documentTitle": "My Test Document"},
        )

        assert requests[0]["insertText"]["text"] == "Document: My Test Document"

    def test_extract_header_footer_from_doc(self):
        """Should extract header/footer content from Google Docs response."""
        google_doc = {
            "headers": {
                "header-1": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [
                                    {"textRun": {"content": "Header text\n"}}
                                ]
                            }
                        }
                    ]
                }
            },
            "footers": {
                "footer-1": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [
                                    {"textRun": {"content": "Footer text\n"}}
                                ]
                            }
                        }
                    ]
                }
            },
        }

        header_content, footer_content = HeaderFooterTransform.extract_header_footer_from_doc(google_doc)

        assert header_content is not None
        assert footer_content is not None
        assert header_content["content"][0]["content"][0]["text"] == "Header text"
        assert footer_content["content"][0]["content"][0]["text"] == "Footer text"

    def test_extract_header_footer_empty(self):
        """Should return None for missing headers/footers."""
        google_doc = {}

        header_content, footer_content = HeaderFooterTransform.extract_header_footer_from_doc(google_doc)

        assert header_content is None
        assert footer_content is None

    def test_extract_page_margins_from_doc(self):
        """Should extract page margins from Google Docs documentStyle."""
        google_doc = {
            "documentStyle": {
                "marginTop": {"magnitude": 72, "unit": "PT"},
                "marginBottom": {"magnitude": 72, "unit": "PT"},
                "marginLeft": {"magnitude": 90, "unit": "PT"},
                "marginRight": {"magnitude": 90, "unit": "PT"},
            }
        }

        margins = HeaderFooterTransform.extract_page_margins_from_doc(google_doc)

        assert margins is not None
        # 72 PT * (96 DPI / 72 PT per inch) = 96 pixels
        assert margins["top"] == 96
        assert margins["bottom"] == 96
        # 90 PT * (96 DPI / 72 PT per inch) = 120 pixels
        assert margins["left"] == 120
        assert margins["right"] == 120

    def test_extract_page_margins_inches(self):
        """Should convert inch margins to pixels."""
        google_doc = {
            "documentStyle": {
                "marginTop": {"magnitude": 1, "unit": "IN"},
                "marginBottom": {"magnitude": 1, "unit": "IN"},
                "marginLeft": {"magnitude": 1, "unit": "IN"},
                "marginRight": {"magnitude": 1, "unit": "IN"},
            }
        }

        margins = HeaderFooterTransform.extract_page_margins_from_doc(google_doc)

        # 1 inch * 96 DPI = 96 pixels
        assert margins["top"] == 96
        assert margins["left"] == 96

    def test_extract_page_margins_empty(self):
        """Should return None for missing margins."""
        google_doc = {}

        margins = HeaderFooterTransform.extract_page_margins_from_doc(google_doc)

        assert margins is None
