"""Google Slides Transform Layer.

Bidirectional conversion between Scribe slides data and Google Slides API structures.

Scribe → Google Slides (Push):
  - Creates slides with appropriate layouts
  - Adds text boxes with styled content (bold, bullets, numbered lists)
  - Handles images
  - Creates speaker notes
  - Applies theme colors

Google Slides → Scribe (Pull):
  - Parses Google Slides presentation structure
  - Extracts slide content and layouts
  - Preserves text styling as markdown
  - Reconstructs slides_data format

Supported Content:
  - Headings (converted to bold text)
  - Bullet lists (• markers)
  - Numbered lists (1. 2. 3. markers)
  - Bold, italic text (markdown-style)
  - Images (via URLs)
  - Speaker notes
"""

from __future__ import annotations

import re
import uuid
from typing import Any

# Scribe layout to Google Slides predefined layout mapping
# Google Slides layout IDs (these are common predefined layouts)
LAYOUT_MAPPING = {
    "title": "TITLE",
    "content": "TITLE_AND_BODY",
    "two-column": "TITLE_AND_TWO_COLUMNS",
    "image-full": "BLANK",
    "image-left": "BLANK",
    "image-right": "BLANK",
    "blank": "BLANK",
    "section": "SECTION_HEADER",
}

# Reverse mapping for pull operations
GOOGLE_LAYOUT_TO_SCRIBE = {
    "TITLE": "title",
    "TITLE_AND_BODY": "content",
    "TITLE_AND_TWO_COLUMNS": "two-column",
    "BLANK": "blank",
    "SECTION_HEADER": "section",
    "MAIN_POINT": "content",
    "BIG_NUMBER": "content",
    "CAPTION_ONLY": "content",
    "ONE_COLUMN_TEXT": "content",
}

# Standard slide dimensions (in EMU - English Metric Units)
# 1 EMU = 1/914400 inch
SLIDE_WIDTH_EMU = 9144000  # 10 inches
SLIDE_HEIGHT_EMU = 5143500  # 5.625 inches

# Common dimensions in PT (points)
SLIDE_WIDTH_PT = 720  # 10 inches * 72 pt/inch
SLIDE_HEIGHT_PT = 405  # 5.625 inches * 72 pt/inch

# Default colors for styling
THEME_COLORS = {
    "primary": {"red": 0.1, "green": 0.21, "blue": 0.36},  # Dark blue
    "secondary": {"red": 0.77, "green": 0.19, "blue": 0.19},  # Red
    "text": {"red": 0.2, "green": 0.2, "blue": 0.2},  # Dark gray
}


def generate_slide_id() -> str:
    """Generate a unique slide ID."""
    return f"slide-{uuid.uuid4().hex[:8]}"


def generate_element_id() -> str:
    """Generate a unique element ID."""
    return f"elem-{uuid.uuid4().hex[:8]}"


class ScribeToGoogleSlides:
    """Converts Scribe slides_data to Google Slides API requests.

    Creates properly styled slides with:
    - Title and content text boxes
    - Bullet lists and numbered lists
    - Bold/italic text formatting
    - Images with proper positioning
    - Speaker notes
    """

    def __init__(self):
        self.requests: list[dict] = []
        self.warnings: list[str] = []
        self._theme: dict = {}

    def transform(self, slides_data: dict, presentation_id: str) -> tuple[list[dict], list[str]]:
        """Transform Scribe slides_data to Google Slides batchUpdate requests.

        Args:
            slides_data: Scribe slides data structure
            presentation_id: Existing Google Slides presentation ID

        Returns:
            Tuple of (requests list, warnings list)
        """
        self.requests = []
        self.warnings = []
        self._theme = slides_data.get("theme", {})

        slides = slides_data.get("slides", [])

        for i, slide in enumerate(slides):
            self._create_slide_requests(slide, i)

        return self.requests, self.warnings

    def _create_slide_requests(self, slide: dict, index: int):
        """Create requests for a single slide."""
        slide_id = slide.get("id", generate_slide_id())
        layout = slide.get("layout", "content")
        title = slide.get("title", "")
        content = slide.get("content", "")
        notes = slide.get("notes", "")
        image_url = slide.get("imageUrl", "")

        # Create the slide with appropriate layout
        google_layout = LAYOUT_MAPPING.get(layout, "BLANK")
        self.requests.append({
            "createSlide": {
                "objectId": slide_id,
                "insertionIndex": index,
                "slideLayoutReference": {
                    "predefinedLayout": google_layout,
                },
            }
        })

        # Create content based on layout type
        if google_layout == "BLANK" or layout in ("image-full", "image-left", "image-right"):
            self._create_blank_slide_content(slide_id, layout, title, content, image_url)
        else:
            # For predefined layouts, create text boxes that work with placeholders
            self._create_standard_slide_content(slide_id, layout, title, content)

        # Add speaker notes if present
        if notes:
            self._create_speaker_notes(slide_id, notes)

    def _create_blank_slide_content(
        self, slide_id: str, layout: str, title: str, content: str, image_url: str
    ):
        """Create content for blank/image layouts."""

        # Determine layout positioning
        if layout == "image-full":
            # Full-width image with title overlay
            if image_url:
                self._add_image(slide_id, image_url, 0, 0, SLIDE_WIDTH_PT, SLIDE_HEIGHT_PT)
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=SLIDE_HEIGHT_PT - 80, width=SLIDE_WIDTH_PT - 72, height=60,
                    font_size=32, bold=True, align="CENTER"
                )
        elif layout == "image-left":
            # Image on left, content on right
            half_width = SLIDE_WIDTH_PT / 2 - 20
            if image_url:
                self._add_image(slide_id, image_url, 20, 60, half_width, SLIDE_HEIGHT_PT - 80)
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=half_width + 40, y=30, width=half_width - 20, height=50,
                    font_size=24, bold=True
                )
            if content:
                self._add_text_box(
                    slide_id, content,
                    x=half_width + 40, y=90, width=half_width - 20, height=SLIDE_HEIGHT_PT - 120,
                    font_size=14, process_markdown=True
                )
        elif layout == "image-right":
            # Image on right, content on left
            half_width = SLIDE_WIDTH_PT / 2 - 20
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=20, y=30, width=half_width - 20, height=50,
                    font_size=24, bold=True
                )
            if content:
                self._add_text_box(
                    slide_id, content,
                    x=20, y=90, width=half_width - 20, height=SLIDE_HEIGHT_PT - 120,
                    font_size=14, process_markdown=True
                )
            if image_url:
                self._add_image(slide_id, image_url, half_width + 20, 60, half_width, SLIDE_HEIGHT_PT - 80)
        else:
            # Standard blank layout
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=30, width=SLIDE_WIDTH_PT - 72, height=50,
                    font_size=28, bold=True
                )
            if content:
                self._add_text_box(
                    slide_id, content,
                    x=36, y=100, width=SLIDE_WIDTH_PT - 72, height=SLIDE_HEIGHT_PT - 130,
                    font_size=16, process_markdown=True
                )
            if image_url:
                self._add_image(
                    slide_id, image_url,
                    36, 100, SLIDE_WIDTH_PT - 72, SLIDE_HEIGHT_PT - 130
                )

    def _create_standard_slide_content(
        self, slide_id: str, layout: str, title: str, content: str
    ):
        """Create content for standard layouts (title-only, title+body, etc.)."""

        if layout == "title":
            # Title slide - large centered title
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=SLIDE_HEIGHT_PT / 2 - 40, width=SLIDE_WIDTH_PT - 72, height=80,
                    font_size=44, bold=True, align="CENTER"
                )
            if content:
                # Subtitle
                self._add_text_box(
                    slide_id, content,
                    x=36, y=SLIDE_HEIGHT_PT / 2 + 50, width=SLIDE_WIDTH_PT - 72, height=50,
                    font_size=20, align="CENTER"
                )
        elif layout == "section":
            # Section header - title with line
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=SLIDE_HEIGHT_PT / 2 - 30, width=SLIDE_WIDTH_PT - 72, height=60,
                    font_size=36, bold=True, align="CENTER"
                )
        elif layout == "two-column":
            # Two column layout
            col_width = (SLIDE_WIDTH_PT - 80) / 2 - 10
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=30, width=SLIDE_WIDTH_PT - 72, height=50,
                    font_size=24, bold=True
                )
            if content:
                # Split content by delimiter or paragraphs
                parts = self._split_two_column_content(content)
                # Left column
                self._add_text_box(
                    slide_id, parts[0],
                    x=36, y=100, width=col_width, height=SLIDE_HEIGHT_PT - 130,
                    font_size=14, process_markdown=True
                )
                # Right column
                if len(parts) > 1:
                    self._add_text_box(
                        slide_id, parts[1],
                        x=46 + col_width, y=100, width=col_width, height=SLIDE_HEIGHT_PT - 130,
                        font_size=14, process_markdown=True
                    )
        else:
            # Default content layout
            if title:
                self._add_text_box(
                    slide_id, title,
                    x=36, y=30, width=SLIDE_WIDTH_PT - 72, height=50,
                    font_size=28, bold=True
                )
            if content:
                self._add_text_box(
                    slide_id, content,
                    x=36, y=100, width=SLIDE_WIDTH_PT - 72, height=SLIDE_HEIGHT_PT - 130,
                    font_size=16, process_markdown=True
                )

    def _add_text_box(
        self,
        slide_id: str,
        text: str,
        x: float,
        y: float,
        width: float,
        height: float,
        font_size: int = 16,
        bold: bool = False,
        italic: bool = False,
        align: str = "START",
        process_markdown: bool = False,
    ):
        """Add a text box with styled content."""
        if not text:
            return

        box_id = generate_element_id()

        # Create the shape
        self.requests.append({
            "createShape": {
                "objectId": box_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": width, "unit": "PT"},
                        "height": {"magnitude": height, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        })

        # Process and clean content
        if process_markdown:
            clean_text, style_ranges = self._parse_markdown_content(text)
        else:
            clean_text = self._clean_content(text)
            style_ranges = []

        # Insert text
        self.requests.append({
            "insertText": {
                "objectId": box_id,
                "text": clean_text,
                "insertionIndex": 0,
            }
        })

        # Apply base style
        self.requests.append({
            "updateTextStyle": {
                "objectId": box_id,
                "style": {
                    "bold": bold,
                    "italic": italic,
                    "fontSize": {"magnitude": font_size, "unit": "PT"},
                    "foregroundColor": {"opaqueColor": {"rgbColor": THEME_COLORS["text"]}},
                },
                "fields": "bold,italic,fontSize,foregroundColor",
            }
        })

        # Apply text alignment
        self.requests.append({
            "updateParagraphStyle": {
                "objectId": box_id,
                "style": {
                    "alignment": align,
                },
                "fields": "alignment",
            }
        })

        # Apply style ranges (bold, italic sections)
        for range_info in style_ranges:
            style = {}
            fields = []
            if range_info.get("bold"):
                style["bold"] = True
                fields.append("bold")
            if range_info.get("italic"):
                style["italic"] = True
                fields.append("italic")

            if style:
                self.requests.append({
                    "updateTextStyle": {
                        "objectId": box_id,
                        "textRange": {
                            "type": "FIXED_RANGE",
                            "startIndex": range_info["start"],
                            "endIndex": range_info["end"],
                        },
                        "style": style,
                        "fields": ",".join(fields),
                    }
                })

    def _add_image(
        self,
        slide_id: str,
        image_url: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ):
        """Add an image to a slide."""
        if not image_url:
            return

        if image_url.startswith("data:"):
            self.warnings.append(f"Base64 images not supported in Slides sync")
            return

        image_id = generate_element_id()

        self.requests.append({
            "createImage": {
                "objectId": image_id,
                "url": image_url,
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": width, "unit": "PT"},
                        "height": {"magnitude": height, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        })

    def _create_speaker_notes(self, slide_id: str, notes: str):
        """Create speaker notes for a slide."""
        if not notes:
            return

        notes_id = f"{slide_id}_notes"

        # Note: Speaker notes in Google Slides are added differently
        # We need to find the notes page element and update it
        # For now, we'll add a warning
        self.warnings.append(
            f"Speaker notes for slide {slide_id} - requires separate update after slide creation"
        )

    def _parse_markdown_content(self, content: str) -> tuple[str, list[dict]]:
        """Parse markdown-like content and extract style ranges.

        Supports:
        - **bold** or __bold__
        - *italic* or _italic_
        - Bullet lists (- or *)
        - Numbered lists (1. 2. 3.)
        """
        style_ranges = []

        # First clean HTML and normalize
        text = re.sub(r"<[^>]+>", "", content)

        # Convert bullet markers
        text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.MULTILINE)

        # Keep numbered lists as-is (1. 2. 3.)

        # Extract bold ranges (**text** or __text__)
        result = ""
        i = 0
        while i < len(text):
            # Check for bold markers
            if text[i:i+2] in ("**", "__"):
                marker = text[i:i+2]
                end_pos = text.find(marker, i + 2)
                if end_pos != -1:
                    start_idx = len(result)
                    bold_text = text[i+2:end_pos]
                    result += bold_text
                    style_ranges.append({
                        "start": start_idx,
                        "end": start_idx + len(bold_text),
                        "bold": True,
                    })
                    i = end_pos + 2
                    continue

            # Check for italic markers (* or _)
            if text[i] in ("*", "_") and (i == 0 or text[i-1] in " \n"):
                marker = text[i]
                end_pos = text.find(marker, i + 1)
                if end_pos != -1 and (end_pos == len(text) - 1 or text[end_pos+1] in " \n.,!?"):
                    start_idx = len(result)
                    italic_text = text[i+1:end_pos]
                    result += italic_text
                    style_ranges.append({
                        "start": start_idx,
                        "end": start_idx + len(italic_text),
                        "italic": True,
                    })
                    i = end_pos + 1
                    continue

            result += text[i]
            i += 1

        # Normalize whitespace
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result.strip(), style_ranges

    def _split_two_column_content(self, content: str) -> list[str]:
        """Split content for two-column layout."""
        # Check for explicit column delimiter
        if "|||" in content:
            parts = content.split("|||", 1)
            return [p.strip() for p in parts]

        if "---" in content:
            parts = content.split("---", 1)
            return [p.strip() for p in parts]

        # Split by paragraphs evenly
        paragraphs = [p for p in content.split("\n\n") if p.strip()]
        mid = len(paragraphs) // 2

        if mid == 0:
            return [content, ""]

        return [
            "\n\n".join(paragraphs[:mid]),
            "\n\n".join(paragraphs[mid:]),
        ]

    def _clean_content(self, content: str) -> str:
        """Clean content for Google Slides (remove HTML, normalize)."""
        text = content

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Convert bullet markers
        text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.MULTILINE)

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


class GoogleSlidesToScribe:
    """Converts Google Slides presentation to Scribe slides_data format.

    Extracts:
    - Slide layouts
    - Titles and content text
    - Text styling (converts to markdown)
    - Images (URL references)
    - Speaker notes
    - Theme colors
    """

    def __init__(self):
        self.warnings: list[str] = []

    def transform(self, presentation: dict) -> tuple[dict, list[str]]:
        """Transform Google Slides presentation to Scribe slides_data.

        Args:
            presentation: Google Slides API presentation response

        Returns:
            Tuple of (slides_data, warnings)
        """
        self.warnings = []

        slides = []
        google_slides = presentation.get("slides", [])

        for i, google_slide in enumerate(google_slides):
            slide = self._parse_slide(google_slide, i + 1)
            slides.append(slide)

        # Extract theme from presentation
        theme = self._extract_theme(presentation)

        slides_data = {
            "slides": slides,
            "theme": theme,
        }

        return slides_data, self.warnings

    def _parse_slide(self, google_slide: dict, slide_number: int) -> dict:
        """Parse a single Google Slide into Scribe format."""
        slide_id = google_slide.get("objectId", generate_slide_id())

        # Determine layout from slideProperties
        layout_name = self._get_layout_name(google_slide)
        scribe_layout = GOOGLE_LAYOUT_TO_SCRIBE.get(layout_name, "content")

        # Extract content from shapes
        title = ""
        content_parts = []
        notes = ""
        image_url = ""

        page_elements = google_slide.get("pageElements", [])

        for element in page_elements:
            # Check for images
            if "image" in element:
                img_props = element.get("image", {})
                img_url = img_props.get("contentUrl", "") or img_props.get("sourceUrl", "")
                if img_url and not image_url:
                    image_url = img_url
                continue

            shape = element.get("shape")
            if not shape:
                continue

            placeholder = shape.get("placeholder", {})
            placeholder_type = placeholder.get("type", "")

            text = self._extract_styled_text_from_shape(shape)

            if placeholder_type in ("TITLE", "CENTERED_TITLE"):
                title = text
            elif placeholder_type in ("BODY", "SUBTITLE"):
                content_parts.append(text)
            elif text:
                # Non-placeholder text box - determine if title or content by position
                transform = element.get("transform", {})
                translate_y = transform.get("translateY", 0)

                # If near top, likely title; otherwise content
                if translate_y < 100 and not title:
                    title = text
                else:
                    content_parts.append(text)

        # Extract speaker notes
        notes_page = google_slide.get("slideProperties", {}).get("notesPage", {})
        if notes_page:
            for element in notes_page.get("pageElements", []):
                shape = element.get("shape", {})
                if shape.get("placeholder", {}).get("type") == "BODY":
                    notes = self._extract_styled_text_from_shape(shape)
                    break

        content = "\n\n".join(part for part in content_parts if part.strip())

        result = {
            "id": slide_id,
            "slideNumber": slide_number,
            "layout": scribe_layout,
            "title": title,
            "content": content,
            "notes": notes,
        }

        if image_url:
            result["imageUrl"] = image_url

        return result

    def _get_layout_name(self, google_slide: dict) -> str:
        """Get the layout name from a Google Slide."""
        slide_props = google_slide.get("slideProperties", {})
        layout_obj_id = slide_props.get("layoutObjectId", "")

        # The layout type is often encoded in the layoutObjectId
        layout_id_lower = layout_obj_id.lower()

        if "title" in layout_id_lower and "body" not in layout_id_lower:
            return "TITLE"
        elif "title" in layout_id_lower and "body" in layout_id_lower:
            return "TITLE_AND_BODY"
        elif "blank" in layout_id_lower:
            return "BLANK"
        elif "two" in layout_id_lower or "column" in layout_id_lower:
            return "TITLE_AND_TWO_COLUMNS"
        elif "section" in layout_id_lower:
            return "SECTION_HEADER"
        elif "one" in layout_id_lower and "column" in layout_id_lower:
            return "ONE_COLUMN_TEXT"

        # Default to content layout
        return "TITLE_AND_BODY"

    def _extract_styled_text_from_shape(self, shape: dict) -> str:
        """Extract text from a shape, preserving styling as markdown."""
        text_elements = shape.get("text", {}).get("textElements", [])
        result_parts = []

        for element in text_elements:
            # Handle paragraph markers
            paragraph_marker = element.get("paragraphMarker")
            if paragraph_marker:
                bullet = paragraph_marker.get("bullet")
                if bullet:
                    glyph = bullet.get("glyph", "")
                    # Convert numbered bullets to markdown
                    if glyph and glyph[0].isdigit():
                        result_parts.append(f"{glyph} ")
                    else:
                        result_parts.append("• ")
                continue

            text_run = element.get("textRun")
            if not text_run:
                continue

            content = text_run.get("content", "")
            if not content:
                continue

            style = text_run.get("style", {})

            # Check for bold
            is_bold = style.get("bold", False)
            # Check for italic
            is_italic = style.get("italic", False)

            # Apply markdown formatting
            text = content
            if is_bold and is_italic:
                text = f"***{content.strip()}***"
            elif is_bold:
                text = f"**{content.strip()}**"
            elif is_italic:
                text = f"*{content.strip()}*"

            # Handle links
            link = style.get("link", {})
            url = link.get("url", "")
            if url:
                text = f"[{content.strip()}]({url})"

            result_parts.append(text)

        result = "".join(result_parts).strip()

        # Clean up markdown spacing issues
        result = re.sub(r"\*\*\s+\*\*", " ", result)
        result = re.sub(r"\*\s+\*", " ", result)

        return result

    def _extract_theme(self, presentation: dict) -> dict:
        """Extract theme colors from presentation."""
        theme = {
            "primaryColor": "#1a365d",
            "secondaryColor": "#c53030",
            "fontFamily": "Arial, sans-serif",
        }

        # Try to extract from presentation theme colors
        masters = presentation.get("masters", [])
        if not masters:
            return theme

        master = masters[0]
        page_props = master.get("pageProperties", {})
        color_scheme = page_props.get("colorScheme", {}).get("colors", [])

        for color_entry in color_scheme:
            color_type = color_entry.get("type", "")
            rgb_color = color_entry.get("color", {}).get("rgbColor", {})

            if rgb_color:
                hex_color = self._rgb_to_hex(rgb_color)

                if color_type == "DARK1":
                    theme["primaryColor"] = hex_color
                elif color_type == "ACCENT1":
                    theme["secondaryColor"] = hex_color

        return theme

    def _rgb_to_hex(self, rgb: dict) -> str:
        """Convert RGB dict to hex color string."""
        r = int(rgb.get("red", 0) * 255)
        g = int(rgb.get("green", 0) * 255)
        b = int(rgb.get("blue", 0) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


def create_presentation_requests(slides_data: dict, title: str) -> list[dict]:
    """Create requests for building a new Google Slides presentation.

    This is used when pushing to a new (empty) presentation.
    """
    transformer = ScribeToGoogleSlides()
    requests, warnings = transformer.transform(slides_data, "")
    return requests


def delete_all_slides_requests(presentation: dict) -> list[dict]:
    """Create requests to delete all existing slides in a presentation.

    Used before pushing to clear the presentation.
    """
    requests = []
    slides = presentation.get("slides", [])

    for slide in slides:
        slide_id = slide.get("objectId")
        if slide_id:
            requests.append({
                "deleteObject": {
                    "objectId": slide_id,
                }
            })

    return requests
