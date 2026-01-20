"""Google Docs Transform Layer.

Bidirectional conversion between TipTap JSON and Google Docs API structures.

TipTap → Google Docs (Push):
  - Converts TipTap document tree to Google Docs batchUpdate requests
  - Maps headings, paragraphs, lists, tables, etc.
  - Encodes claims and citations as footnotes with JSON metadata

Google Docs → TipTap (Pull):
  - Parses Google Docs document structure
  - Reconstructs TipTap JSON tree
  - Extracts claims and citations from footnotes

Supported Elements:
  - Headings (1-6)
  - Paragraphs with text alignment
  - Bullet lists, ordered lists, task lists
  - Blockquotes
  - Code blocks
  - Tables
  - Images
  - Horizontal rules
  - All text marks (bold, italic, underline, strike, code, link, highlight, subscript, superscript)
  - Claims (as highlighted text + footnote)
  - Citations (as footnotes)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

# Marker prefixes for encoding Scribe metadata in Google Docs footnotes
CLAIM_MARKER = "[SCRIBE_CLAIM:"
CITATION_MARKER = "[SCRIBE_CITE:"
TASK_MARKER_CHECKED = "[x]"
TASK_MARKER_UNCHECKED = "[ ]"
MARKER_END = "]"

# Image placeholder format
IMAGE_PLACEHOLDER_START = "[📷 Image: "
IMAGE_PLACEHOLDER_END = "]"

# Google Docs named style mappings
HEADING_STYLES = {
    1: "HEADING_1",
    2: "HEADING_2",
    3: "HEADING_3",
    4: "HEADING_4",
    5: "HEADING_5",
    6: "HEADING_6",
}

# Text alignment mapping
ALIGNMENT_MAP = {
    "left": "START",
    "center": "CENTER",
    "right": "END",
    "justify": "JUSTIFIED",
}

# Highlight color mapping (TipTap color name -> Google Docs RGB)
HIGHLIGHT_COLORS = {
    "yellow": {"red": 1.0, "green": 1.0, "blue": 0.0},
    "green": {"red": 0.6, "green": 1.0, "blue": 0.6},
    "blue": {"red": 0.6, "green": 0.8, "blue": 1.0},
    "red": {"red": 1.0, "green": 0.6, "blue": 0.6},
    "purple": {"red": 0.9, "green": 0.7, "blue": 1.0},
    "orange": {"red": 1.0, "green": 0.8, "blue": 0.4},
    "pink": {"red": 1.0, "green": 0.75, "blue": 0.8},
    "cyan": {"red": 0.4, "green": 1.0, "blue": 1.0},
}

# Claim highlight color (light yellow)
CLAIM_HIGHLIGHT = {"red": 1.0, "green": 0.95, "blue": 0.6}


def compute_content_hash(content: dict) -> str:
    """Compute SHA-256 hash of document content for change detection."""
    serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass
class TransformResult:
    """Result of a transform operation."""

    requests: list[dict] = field(default_factory=list)
    footnotes: list[dict] = field(default_factory=list)
    claims_count: int = 0
    citations_count: int = 0
    warnings: list[str] = field(default_factory=list)


class TipTapToGoogleDocs:
    """Converts TipTap JSON to Google Docs batchUpdate requests.

    The Google Docs API requires building a list of requests that are
    applied in sequence. We track the current cursor position and
    generate insertText, updateParagraphStyle, etc. requests.
    """

    def __init__(self):
        self.requests: list[dict] = []
        self.cursor: int = 1  # Google Docs starts at index 1
        self.claims_count: int = 0
        self.citations_count: int = 0
        self.warnings: list[str] = []
        self._list_counter: int = 0
        self._pending_footnotes: list[dict] = []

    def transform(self, tiptap_json: dict) -> TransformResult:
        """Transform TipTap JSON to Google Docs requests."""
        self.requests = []
        self.cursor = 1
        self.claims_count = 0
        self.citations_count = 0
        self.warnings = []
        self._list_counter = 0
        self._pending_footnotes = []

        content = tiptap_json.get("content", [])
        for node in content:
            self._process_node(node)

        return TransformResult(
            requests=self.requests,
            footnotes=self._pending_footnotes,
            claims_count=self.claims_count,
            citations_count=self.citations_count,
            warnings=self.warnings,
        )

    def _process_node(self, node: dict, list_context: dict | None = None):
        """Process a TipTap node and generate corresponding requests."""
        node_type = node.get("type", "")

        if node_type == "paragraph":
            self._process_paragraph(node)
        elif node_type == "heading":
            self._process_heading(node)
        elif node_type == "bulletList":
            self._process_list(node, ordered=False)
        elif node_type == "orderedList":
            self._process_list(node, ordered=True)
        elif node_type == "taskList":
            self._process_task_list(node)
        elif node_type == "listItem":
            self._process_list_item(node, list_context)
        elif node_type == "taskItem":
            self._process_task_item(node)
        elif node_type == "blockquote":
            self._process_blockquote(node)
        elif node_type == "codeBlock":
            self._process_code_block(node)
        elif node_type == "table":
            self._process_table(node)
        elif node_type == "horizontalRule":
            self._process_horizontal_rule()
        elif node_type == "image":
            self._process_image(node)
        elif node_type == "text":
            self._process_text_node(node)
        elif node_type == "citation":
            self._process_citation(node)
        elif node_type == "hardBreak":
            self._insert_text("\n")
        else:
            # Unknown node type - try to process children
            if "content" in node:
                for child in node.get("content", []):
                    self._process_node(child, list_context)

    def _process_paragraph(self, node: dict):
        """Process a paragraph node with optional text alignment."""
        start_index = self.cursor
        self._process_inline_content(node.get("content", []))
        end_index = self.cursor

        # Insert newline
        self._insert_text("\n")

        # Build paragraph style
        para_style: dict[str, Any] = {"namedStyleType": "NORMAL_TEXT"}
        fields = ["namedStyleType"]

        # Check for text alignment
        attrs = node.get("attrs", {})
        text_align = attrs.get("textAlign")
        if text_align and text_align in ALIGNMENT_MAP:
            para_style["alignment"] = ALIGNMENT_MAP[text_align]
            fields.append("alignment")

        # Apply paragraph style
        self.requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index + 1},
                "paragraphStyle": para_style,
                "fields": ",".join(fields),
            }
        })

    def _process_heading(self, node: dict):
        """Process a heading node with level and optional alignment."""
        attrs = node.get("attrs", {})
        level = attrs.get("level", 1)
        style = HEADING_STYLES.get(level, "HEADING_1")

        start_index = self.cursor
        self._process_inline_content(node.get("content", []))
        end_index = self.cursor

        # Insert newline
        self._insert_text("\n")

        # Build heading style
        para_style: dict[str, Any] = {"namedStyleType": style}
        fields = ["namedStyleType"]

        # Check for text alignment
        text_align = attrs.get("textAlign")
        if text_align and text_align in ALIGNMENT_MAP:
            para_style["alignment"] = ALIGNMENT_MAP[text_align]
            fields.append("alignment")

        # Apply heading style
        self.requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index + 1},
                "paragraphStyle": para_style,
                "fields": ",".join(fields),
            }
        })

    def _process_list(self, node: dict, ordered: bool = False):
        """Process a bullet or ordered list."""
        self._list_counter += 1

        for item in node.get("content", []):
            if item.get("type") == "listItem":
                self._process_list_item(item, {"ordered": ordered, "level": 0})

    def _process_list_item(self, node: dict, list_context: dict | None):
        """Process a list item."""
        if list_context is None:
            list_context = {"ordered": False, "level": 0}

        start_index = self.cursor

        # Process the content of the list item
        for child in node.get("content", []):
            child_type = child.get("type", "")
            if child_type == "paragraph":
                self._process_inline_content(child.get("content", []))
                self._insert_text("\n")
            elif child_type in ("bulletList", "orderedList"):
                # Nested list - process recursively with incremented level
                nested_ordered = child_type == "orderedList"
                for nested_item in child.get("content", []):
                    if nested_item.get("type") == "listItem":
                        self._process_list_item(
                            nested_item,
                            {"ordered": nested_ordered, "level": list_context.get("level", 0) + 1}
                        )
            else:
                self._process_node(child, list_context)

        end_index = self.cursor

        # Apply bullet/number style
        if end_index > start_index:
            preset = "NUMBERED_DECIMAL_ALPHA_ROMAN" if list_context.get("ordered") else "BULLET_DISC_CIRCLE_SQUARE"
            self.requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "bulletPreset": preset,
                }
            })

    def _process_task_list(self, node: dict):
        """Process a task list (checklist)."""
        for item in node.get("content", []):
            if item.get("type") == "taskItem":
                self._process_task_item(item)

    def _process_task_item(self, node: dict):
        """Process a task item (checkbox)."""
        attrs = node.get("attrs", {})
        checked = attrs.get("checked", False)

        start_index = self.cursor

        # Add checkbox indicator
        checkbox = "[x] " if checked else "[ ] "
        self._insert_text(checkbox)

        # Process content
        for child in node.get("content", []):
            if child.get("type") == "paragraph":
                self._process_inline_content(child.get("content", []))
            else:
                self._process_node(child)

        self._insert_text("\n")
        end_index = self.cursor

        # Style as bullet list
        self.requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "bulletPreset": "BULLET_CHECKBOX",
            }
        })

    def _process_blockquote(self, node: dict):
        """Process a blockquote node with proper margins and styling."""
        start_index = self.cursor

        for child in node.get("content", []):
            self._process_node(child)

        end_index = self.cursor

        # Apply blockquote styling: indentation, left border, italic, spacing
        if end_index > start_index:
            # Paragraph style: indentation and border
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "paragraphStyle": {
                        "indentFirstLine": {"magnitude": 36, "unit": "PT"},
                        "indentStart": {"magnitude": 36, "unit": "PT"},
                        "indentEnd": {"magnitude": 36, "unit": "PT"},
                        "spaceAbove": {"magnitude": 12, "unit": "PT"},
                        "spaceBelow": {"magnitude": 12, "unit": "PT"},
                        "borderLeft": {
                            "color": {"color": {"rgbColor": {"red": 0.6, "green": 0.6, "blue": 0.6}}},
                            "width": {"magnitude": 3, "unit": "PT"},
                            "padding": {"magnitude": 12, "unit": "PT"},
                            "dashStyle": "SOLID",
                        },
                    },
                    "fields": "indentFirstLine,indentStart,indentEnd,spaceAbove,spaceBelow,borderLeft",
                }
            })
            # Text style: italic for blockquote content
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": {
                        "italic": True,
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.3, "green": 0.3, "blue": 0.3}}},
                    },
                    "fields": "italic,foregroundColor",
                }
            })

    def _process_code_block(self, node: dict):
        """Process a code block node with monospace font and background."""
        start_index = self.cursor

        # Extract text from code block
        text_parts = []
        for child in node.get("content", []):
            if child.get("type") == "text":
                text_parts.append(child.get("text", ""))

        text = "".join(text_parts)
        if text:
            self._insert_text(text)

        self._insert_text("\n")
        end_index = self.cursor

        # Apply code block styling: monospace font, background, indentation
        if end_index > start_index:
            # Paragraph style: indentation and spacing
            self.requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "paragraphStyle": {
                        "indentFirstLine": {"magnitude": 18, "unit": "PT"},
                        "indentStart": {"magnitude": 18, "unit": "PT"},
                        "indentEnd": {"magnitude": 18, "unit": "PT"},
                        "spaceAbove": {"magnitude": 8, "unit": "PT"},
                        "spaceBelow": {"magnitude": 8, "unit": "PT"},
                        "lineSpacing": 115,  # Tighter line spacing for code
                    },
                    "fields": "indentFirstLine,indentStart,indentEnd,spaceAbove,spaceBelow,lineSpacing",
                }
            })
            # Text style: monospace font and gray background
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Consolas", "weight": 400},
                        "fontSize": {"magnitude": 10, "unit": "PT"},
                        "backgroundColor": {"color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}},
                    },
                    "fields": "weightedFontFamily,fontSize,backgroundColor",
                }
            })

    def _process_table(self, node: dict):
        """Process a table node with cell content.

        Google Docs table structure after insertTable:
        - Table header: 3 indices
        - For each row:
          - Each cell: 2 indices (paragraph start + newline)
          - After each row (except last): 1 index (row boundary)

        Cell index formula (verified by testing):
        cell[row][col] = table_start + 3 + row * (num_cols * 2 + 1) + col * 2

        Table structural size (empty):
        size = 2 + num_rows * (num_cols * 2 + 1)

        We insert content in REVERSE order to maintain correct indices
        (inserting text shifts all subsequent indices).
        """
        rows = node.get("content", [])
        if not rows:
            self.warnings.append("Empty table skipped")
            return

        # Count rows and find max columns
        num_rows = len(rows)
        num_cols = 0
        for row in rows:
            row_type = row.get("type", "")
            if row_type in ("tableRow", "tableHeader"):
                cells = row.get("content", [])
                num_cols = max(num_cols, len(cells))

        if num_rows == 0 or num_cols == 0:
            self.warnings.append("Empty table skipped")
            return

        # Record table insertion point
        table_insert_index = self.cursor

        # Insert empty table structure first
        self.requests.append({
            "insertTable": {
                "rows": num_rows,
                "columns": num_cols,
                "location": {"index": table_insert_index},
            }
        })

        # Google Docs places the table starting at insert_index + 1
        # (the insert index itself becomes a paragraph before the table)
        table_actual_start = table_insert_index + 1

        # Extract all cell content
        cell_contents: list[list[str]] = []
        for row in rows:
            row_cells = []
            row_type = row.get("type", "")
            if row_type in ("tableRow", "tableHeader"):
                for cell in row.get("content", []):
                    cell_text = self._extract_text_from_node(cell)
                    row_cells.append(cell_text)
            # Pad row to have num_cols cells
            while len(row_cells) < num_cols:
                row_cells.append("")
            cell_contents.append(row_cells)

        # Collect all cell insertions with their calculated indices
        # Formula: cell[row][col] = table_start + 3 + row * (cols * 2 + 1) + col * 2
        cell_insertions = []
        for row_idx, row_content in enumerate(cell_contents):
            for col_idx, cell_text in enumerate(row_content):
                if cell_text:
                    cell_index = (
                        table_actual_start
                        + 3
                        + row_idx * (num_cols * 2 + 1)
                        + col_idx * 2
                    )
                    cell_insertions.append({
                        "index": cell_index,
                        "text": cell_text,
                    })

        # Insert cell contents in REVERSE order
        # This ensures indices remain valid (inserting text shifts subsequent indices)
        for insertion in reversed(cell_insertions):
            self.requests.append({
                "insertText": {
                    "location": {"index": insertion["index"]},
                    "text": insertion["text"],
                }
            })

        # Calculate total text inserted
        total_text_len = sum(len(cell) for row in cell_contents for cell in row)

        # Update cursor to position after table
        # Table structural size (empty) = 2 + num_rows * (num_cols * 2 + 1)
        # Final cursor = table_insert_index + 1 (paragraph before table)
        #              + table_structural_size + total_text_len
        table_structural_size = 2 + num_rows * (num_cols * 2 + 1)
        self.cursor = table_insert_index + 1 + table_structural_size + total_text_len

    def _extract_text_from_node(self, node: dict) -> str:
        """Extract plain text from a node (recursive)."""
        if node.get("type") == "text":
            return node.get("text", "")

        text_parts = []
        for child in node.get("content", []):
            text_parts.append(self._extract_text_from_node(child))

        return "".join(text_parts)

    def _process_horizontal_rule(self):
        """Process a horizontal rule."""
        # Insert a horizontal line using repeated dashes
        self._insert_text("─" * 50 + "\n")

    def _process_image(self, node: dict):
        """Process an image node."""
        attrs = node.get("attrs", {})
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        width = attrs.get("width", "")

        if not src:
            self.warnings.append("Image without src skipped")
            return

        # Handle base64/data URLs with placeholder
        if src.startswith("data:"):
            placeholder = f"{IMAGE_PLACEHOLDER_START}embedded image"
            if alt:
                placeholder += f" - {alt}"
            placeholder += f"{IMAGE_PLACEHOLDER_END}\n"
            self._insert_text(placeholder)
            self.warnings.append("Base64 image converted to placeholder")
            return

        # Try to insert inline image from URL
        try:
            # Calculate dimensions
            img_width = 300  # Default width in PT
            if width:
                try:
                    if isinstance(width, str):
                        if width.endswith("%"):
                            percent = int(width.rstrip("%"))
                            img_width = int(468 * percent / 100)
                        elif width.endswith("px"):
                            img_width = int(int(width.rstrip("px")) * 0.75)
                        else:
                            img_width = int(float(width))
                    else:
                        img_width = int(width)
                except (ValueError, TypeError):
                    pass

            self.requests.append({
                "insertInlineImage": {
                    "location": {"index": self.cursor},
                    "uri": src,
                    "objectSize": {
                        "width": {"magnitude": img_width, "unit": "PT"},
                    },
                }
            })
            self.cursor += 1
        except Exception as e:
            # Fallback to placeholder with URL
            placeholder = f"{IMAGE_PLACEHOLDER_START}{src}{IMAGE_PLACEHOLDER_END}\n"
            self._insert_text(placeholder)
            self.warnings.append(f"Image converted to placeholder: {str(e)}")

    def _process_inline_content(self, content: list[dict]):
        """Process inline content (text, marks, etc.)."""
        for node in content:
            node_type = node.get("type", "")
            if node_type == "text":
                self._process_text_node(node)
            elif node_type == "citation":
                self._process_citation(node)
            elif node_type == "hardBreak":
                self._insert_text("\n")
            elif node_type == "image":
                self._process_image(node)
            else:
                # Try to process as inline element
                self._process_node(node)

    def _process_text_node(self, node: dict):
        """Process a text node with marks."""
        text = node.get("text", "")
        if not text:
            return

        marks = node.get("marks", [])
        start_index = self.cursor

        # Check for claim mark (needs special handling)
        claim_mark = None
        for mark in marks:
            if mark.get("type") == "claim":
                claim_mark = mark
                break

        # Insert the text
        self._insert_text(text)
        end_index = self.cursor

        # Build text style from marks
        text_style: dict[str, Any] = {}
        fields: list[str] = []

        for mark in marks:
            mark_type = mark.get("type", "")
            mark_attrs = mark.get("attrs", {})

            if mark_type == "bold":
                text_style["bold"] = True
                fields.append("bold")
            elif mark_type == "italic":
                text_style["italic"] = True
                fields.append("italic")
            elif mark_type == "underline":
                text_style["underline"] = True
                fields.append("underline")
            elif mark_type == "strike":
                text_style["strikethrough"] = True
                fields.append("strikethrough")
            elif mark_type == "code":
                text_style["weightedFontFamily"] = {"fontFamily": "Consolas", "weight": 400}
                text_style["backgroundColor"] = {
                    "color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}
                }
                fields.extend(["weightedFontFamily", "backgroundColor"])
            elif mark_type == "link":
                url = mark_attrs.get("href", "")
                if url:
                    text_style["link"] = {"url": url}
                    fields.append("link")
            elif mark_type == "highlight":
                color_name = mark_attrs.get("color", "yellow")
                rgb = HIGHLIGHT_COLORS.get(color_name, HIGHLIGHT_COLORS["yellow"])
                text_style["backgroundColor"] = {"color": {"rgbColor": rgb}}
                if "backgroundColor" not in fields:
                    fields.append("backgroundColor")
            elif mark_type == "subscript":
                text_style["baselineOffset"] = "SUBSCRIPT"
                fields.append("baselineOffset")
            elif mark_type == "superscript":
                text_style["baselineOffset"] = "SUPERSCRIPT"
                fields.append("baselineOffset")
            # Skip claim, comment, changeMark - handled separately

        # Apply claim highlight (yellow background)
        if claim_mark:
            text_style["backgroundColor"] = {"color": {"rgbColor": CLAIM_HIGHLIGHT}}
            if "backgroundColor" not in fields:
                fields.append("backgroundColor")
            self.claims_count += 1

            # Create footnote with claim metadata AND text for restoration
            # This is the "git-like" anchor - we store the claim text so we can
            # find and reapply the claim mark when pulling from Google Docs
            claim_attrs = claim_mark.get("attrs", {})
            self._pending_footnotes.append({
                "index": end_index,
                "type": "claim",
                "data": {
                    "claimId": claim_attrs.get("claimId", ""),
                    "claimType": claim_attrs.get("claimType", "DATA"),
                    "status": claim_attrs.get("status", "draft"),
                    # Store the claim text as anchor for pull restoration
                    "text": text,
                    "textHash": hashlib.md5(text.encode()).hexdigest()[:8],
                },
            })

        # Apply text style
        if text_style and fields:
            # Deduplicate fields
            fields = list(dict.fromkeys(fields))
            self.requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": text_style,
                    "fields": ",".join(fields),
                }
            })

    def _process_citation(self, node: dict):
        """Process a citation node."""
        attrs = node.get("attrs", {})
        bib_key = attrs.get("bibKey", "")
        locator = attrs.get("locator", "")

        if not bib_key:
            return

        # Insert citation marker text
        citation_text = f"({bib_key}"
        if locator:
            citation_text += f", {locator}"
        citation_text += ")"

        start_index = self.cursor
        self._insert_text(citation_text)
        end_index = self.cursor

        self.citations_count += 1

        # Store for footnote creation
        self._pending_footnotes.append({
            "index": end_index,
            "type": "citation",
            "data": {
                "bibKey": bib_key,
                "locator": locator,
            },
        })

        # Style as citation (small, gray)
        self.requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start_index, "endIndex": end_index},
                "textStyle": {
                    "foregroundColor": {"color": {"rgbColor": {"red": 0.4, "green": 0.4, "blue": 0.4}}},
                },
                "fields": "foregroundColor",
            }
        })

    def _insert_text(self, text: str):
        """Insert text at the current cursor position."""
        if not text:
            return

        self.requests.append({
            "insertText": {
                "location": {"index": self.cursor},
                "text": text,
            }
        })
        self.cursor += len(text)


class GoogleDocsToTipTap:
    """Converts Google Docs document structure to TipTap JSON.

    Parses the document body, extracts styles, and reconstructs
    the TipTap node tree. Also extracts claim and citation metadata
    from footnotes.
    """

    def __init__(self):
        self.claims_restored: int = 0
        self.citations_restored: int = 0
        self.warnings: list[str] = []
        self._footnote_data: dict[str, dict] = {}
        self._inline_objects: dict[str, dict] = {}

    def transform(self, google_doc: dict) -> tuple[dict, int, int, list[str]]:
        """Transform Google Docs structure to TipTap JSON.

        Args:
            google_doc: The Google Docs document response from documents.get()

        Returns:
            Tuple of (tiptap_json, claims_restored, citations_restored, warnings)
        """
        self.claims_restored = 0
        self.citations_restored = 0
        self.warnings = []

        # Extract footnote metadata first
        self._extract_footnote_metadata(google_doc)

        # Extract inline objects (images)
        self._inline_objects = google_doc.get("inlineObjects", {})

        # Parse the body content
        body = google_doc.get("body", {})
        content = body.get("content", [])

        tiptap_content = []
        i = 0
        while i < len(content):
            element = content[i]
            nodes, consumed = self._process_structural_element(element, content, i)
            if nodes:
                if isinstance(nodes, list):
                    tiptap_content.extend(nodes)
                else:
                    tiptap_content.append(nodes)
            i += consumed

        return (
            {"type": "doc", "content": tiptap_content},
            self.claims_restored,
            self.citations_restored,
            self.warnings,
        )

    def _extract_footnote_metadata(self, google_doc: dict):
        """Extract Scribe metadata from footnotes."""
        footnotes = google_doc.get("footnotes", {})

        for footnote_id, footnote in footnotes.items():
            content = footnote.get("content", [])
            text = self._extract_text_from_elements(content)

            # Check for claim marker
            if CLAIM_MARKER in text:
                match = re.search(
                    rf"{re.escape(CLAIM_MARKER)}(.+?){re.escape(MARKER_END)}",
                    text
                )
                if match:
                    try:
                        data = json.loads(match.group(1))
                        self._footnote_data[footnote_id] = {"type": "claim", "data": data}
                    except json.JSONDecodeError:
                        self.warnings.append(f"Invalid claim JSON in footnote {footnote_id}")

            # Check for citation marker
            elif CITATION_MARKER in text:
                match = re.search(
                    rf"{re.escape(CITATION_MARKER)}(.+?){re.escape(MARKER_END)}",
                    text
                )
                if match:
                    try:
                        data = json.loads(match.group(1))
                        self._footnote_data[footnote_id] = {"type": "citation", "data": data}
                    except json.JSONDecodeError:
                        self.warnings.append(f"Invalid citation JSON in footnote {footnote_id}")

    def _extract_text_from_elements(self, elements: list[dict]) -> str:
        """Extract plain text from Google Docs elements."""
        text = ""
        for element in elements:
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        text += elem["textRun"].get("content", "")
        return text

    def _process_structural_element(
        self, element: dict, all_elements: list[dict], index: int
    ) -> tuple[dict | list | None, int]:
        """Process a structural element from Google Docs.

        Returns (node(s), number_of_elements_consumed)
        """
        if "paragraph" in element:
            return self._process_paragraph(element["paragraph"], all_elements, index)
        elif "table" in element:
            return self._process_table(element["table"]), 1
        elif "sectionBreak" in element:
            return {"type": "horizontalRule"}, 1
        elif "tableOfContents" in element:
            # Skip TOC
            return None, 1
        return None, 1

    def _process_paragraph(
        self, paragraph: dict, all_elements: list[dict], index: int
    ) -> tuple[dict | list | None, int]:
        """Process a Google Docs paragraph."""
        style = paragraph.get("paragraphStyle", {})
        named_style = style.get("namedStyleType", "NORMAL_TEXT")
        bullet = paragraph.get("bullet")

        elements = paragraph.get("elements", [])
        inline_content = self._process_paragraph_elements(elements)

        # Skip empty paragraphs (often just newlines)
        if not inline_content:
            return None, 1

        # Check for text alignment
        alignment = style.get("alignment", "")
        text_align = None
        if alignment == "CENTER":
            text_align = "center"
        elif alignment == "END":
            text_align = "right"
        elif alignment == "JUSTIFIED":
            text_align = "justify"

        # Determine node type based on style
        if named_style.startswith("HEADING_"):
            try:
                level = int(named_style.split("_")[1])
            except (IndexError, ValueError):
                level = 1

            node = {
                "type": "heading",
                "attrs": {"level": min(level, 3)},  # TipTap only supports 1-3
                "content": inline_content,
            }
            if text_align:
                node["attrs"]["textAlign"] = text_align
            return node, 1

        elif bullet:
            # This is a list item - collect consecutive list items
            return self._collect_list_items(all_elements, index)

        else:
            node = {
                "type": "paragraph",
                "content": inline_content,
            }
            if text_align:
                node["attrs"] = {"textAlign": text_align}
            return node, 1

    def _collect_list_items(
        self, all_elements: list[dict], start_index: int
    ) -> tuple[dict, int]:
        """Collect consecutive list items into a list node.

        Detects task lists by looking for [ ] or [x] prefixes.
        """
        items = []
        consumed = 0
        is_ordered = False
        is_task_list = False
        task_states: list[bool] = []

        i = start_index
        while i < len(all_elements):
            element = all_elements[i]
            if "paragraph" not in element:
                break

            paragraph = element["paragraph"]
            bullet = paragraph.get("bullet")
            if not bullet:
                break

            elements = paragraph.get("elements", [])
            inline_content = self._process_paragraph_elements(elements)

            if inline_content:
                # Check if this is a task item by looking at the first text node
                first_text = ""
                if inline_content and inline_content[0].get("type") == "text":
                    first_text = inline_content[0].get("text", "")

                # Detect task list markers
                is_checked = False
                if first_text.startswith(TASK_MARKER_CHECKED + " "):
                    is_task_list = True
                    is_checked = True
                    # Remove the marker from text
                    inline_content[0]["text"] = first_text[4:]  # len("[x] ")
                    if not inline_content[0]["text"]:
                        inline_content.pop(0)
                elif first_text.startswith(TASK_MARKER_UNCHECKED + " "):
                    is_task_list = True
                    is_checked = False
                    # Remove the marker from text
                    inline_content[0]["text"] = first_text[4:]  # len("[ ] ")
                    if not inline_content[0]["text"]:
                        inline_content.pop(0)

                task_states.append(is_checked)

                items.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": inline_content}] if inline_content else [],
                })

            consumed += 1
            i += 1

        if not items:
            return None, 1

        # If task list detected, convert to taskList/taskItem structure
        if is_task_list:
            task_items = []
            for idx, item in enumerate(items):
                checked = task_states[idx] if idx < len(task_states) else False
                task_items.append({
                    "type": "taskItem",
                    "attrs": {"checked": checked},
                    "content": item.get("content", []),
                })
            return {"type": "taskList", "content": task_items}, consumed

        # Determine list type (heuristic based on first character)
        first_text = ""
        if items and items[0].get("content"):
            first_para = items[0]["content"][0]
            if first_para.get("content"):
                first_node = first_para["content"][0]
                if first_node.get("type") == "text":
                    first_text = first_node.get("text", "")

        # Simple heuristic: if starts with number followed by period/paren, it's ordered
        is_ordered = bool(re.match(r"^\d+[.)]", first_text.strip()))

        list_type = "orderedList" if is_ordered else "bulletList"
        return {"type": list_type, "content": items}, consumed

    def _process_paragraph_elements(self, elements: list[dict]) -> list[dict]:
        """Process inline elements within a paragraph.

        Handles claim restoration using the git-like text anchor approach:
        - When a footnote with claim metadata is found
        - Look at the preceding text and match it against the stored claim text
        - Apply the claim mark to the matching text
        """
        result = []
        pending_claim_footnote = None  # Track claim footnotes to apply to preceding text

        for idx, element in enumerate(elements):
            if "textRun" in element:
                node = self._process_text_run(element["textRun"])
                if node:
                    # Check if there's a pending claim to apply to this text
                    if pending_claim_footnote:
                        claim_data = pending_claim_footnote["data"]
                        stored_text = claim_data.get("text", "")
                        stored_hash = claim_data.get("textHash", "")
                        node_text = node.get("text", "")

                        # Try to match: exact match, contains, or hash match
                        should_apply_claim = False
                        if stored_text and stored_text == node_text:
                            should_apply_claim = True
                        elif stored_text and stored_text in node_text:
                            should_apply_claim = True
                        elif stored_hash:
                            node_hash = hashlib.md5(node_text.encode()).hexdigest()[:8]
                            if node_hash == stored_hash:
                                should_apply_claim = True

                        if should_apply_claim:
                            # Apply claim mark to this text node
                            marks = node.get("marks", [])
                            marks.append({
                                "type": "claim",
                                "attrs": {
                                    "claimId": claim_data.get("claimId", ""),
                                    "claimType": claim_data.get("claimType", "DATA"),
                                    "status": claim_data.get("status", "draft"),
                                },
                            })
                            node["marks"] = marks
                            self.claims_restored += 1

                        pending_claim_footnote = None

                    result.append(node)

            elif "inlineObjectElement" in element:
                node = self._process_inline_object(element["inlineObjectElement"])
                if node:
                    result.append(node)

            elif "footnoteReference" in element:
                footnote_id = element["footnoteReference"].get("footnoteId", "")
                footnote_info = self._footnote_data.get(footnote_id)

                if footnote_info:
                    if footnote_info["type"] == "citation":
                        # Restore citation node
                        data = footnote_info["data"]
                        result.append({
                            "type": "citation",
                            "attrs": {
                                "bibKey": data.get("bibKey", ""),
                                "locator": data.get("locator", ""),
                            },
                        })
                        self.citations_restored += 1

                    elif footnote_info["type"] == "claim":
                        # Claims need to be applied to PRECEDING text
                        # Look backwards in result to find text to mark
                        claim_data = footnote_info["data"]
                        stored_text = claim_data.get("text", "")
                        stored_hash = claim_data.get("textHash", "")
                        claim_applied = False

                        # Search backwards through result for matching text
                        for i in range(len(result) - 1, -1, -1):
                            prev_node = result[i]
                            if prev_node.get("type") == "text":
                                prev_text = prev_node.get("text", "")

                                # Check for match
                                should_apply = False
                                if stored_text and (stored_text == prev_text or stored_text in prev_text):
                                    should_apply = True
                                elif stored_hash:
                                    prev_hash = hashlib.md5(prev_text.encode()).hexdigest()[:8]
                                    if prev_hash == stored_hash:
                                        should_apply = True

                                # Also match by highlight color (claim highlight is distinctive)
                                if not should_apply:
                                    marks = prev_node.get("marks", [])
                                    for mark in marks:
                                        if mark.get("type") == "highlight":
                                            color = mark.get("attrs", {}).get("color", "")
                                            if color == "yellow":
                                                should_apply = True
                                                break

                                if should_apply:
                                    # Apply claim mark
                                    marks = prev_node.get("marks", [])
                                    # Remove highlight mark if present (claim has its own)
                                    marks = [m for m in marks if m.get("type") != "highlight"]
                                    marks.append({
                                        "type": "claim",
                                        "attrs": {
                                            "claimId": claim_data.get("claimId", ""),
                                            "claimType": claim_data.get("claimType", "DATA"),
                                            "status": claim_data.get("status", "draft"),
                                        },
                                    })
                                    prev_node["marks"] = marks
                                    self.claims_restored += 1
                                    claim_applied = True
                                    break

                        if not claim_applied:
                            self.warnings.append(
                                f"Could not restore claim {claim_data.get('claimId', 'unknown')}: "
                                f"text anchor not found"
                            )

        return result

    def _process_text_run(self, text_run: dict) -> dict | list | None:
        """Process a text run element.

        Returns a single node, a list of nodes (if splitting is needed), or None.
        """
        content = text_run.get("content", "")

        # Skip pure whitespace/newlines at the end of paragraphs
        if content == "\n":
            return None

        # Strip trailing newline but preserve internal content
        if content.endswith("\n"):
            content = content[:-1]

        if not content:
            return None

        # Check for image placeholder and convert back to image node
        if IMAGE_PLACEHOLDER_START in content:
            match = re.search(
                rf"{re.escape(IMAGE_PLACEHOLDER_START)}(.+?){re.escape(IMAGE_PLACEHOLDER_END)}",
                content
            )
            if match:
                placeholder_content = match.group(1)
                # Extract URL or description
                if placeholder_content.startswith("http"):
                    return {
                        "type": "image",
                        "attrs": {"src": placeholder_content},
                    }
                else:
                    # It's a description (e.g., "embedded image - alt text")
                    self.warnings.append(f"Image placeholder found: {placeholder_content}")
                    return None

        text_style = text_run.get("textStyle", {})
        marks = []

        # Check for bold
        if text_style.get("bold"):
            marks.append({"type": "bold"})

        # Check for italic
        if text_style.get("italic"):
            marks.append({"type": "italic"})

        # Check for underline
        if text_style.get("underline"):
            marks.append({"type": "underline"})

        # Check for strikethrough
        if text_style.get("strikethrough"):
            marks.append({"type": "strike"})

        # Check for code (monospace font)
        font_family = text_style.get("weightedFontFamily", {}).get("fontFamily", "")
        if any(mono in font_family.lower() for mono in ["courier", "mono", "consolas"]):
            marks.append({"type": "code"})

        # Check for link
        link = text_style.get("link", {})
        if link.get("url"):
            marks.append({"type": "link", "attrs": {"href": link["url"]}})

        # Check for subscript/superscript
        baseline_offset = text_style.get("baselineOffset", "")
        if baseline_offset == "SUBSCRIPT":
            marks.append({"type": "subscript"})
        elif baseline_offset == "SUPERSCRIPT":
            marks.append({"type": "superscript"})

        # Check for highlight (background color)
        bg_color = text_style.get("backgroundColor", {}).get("color", {}).get("rgbColor", {})
        if bg_color:
            red = bg_color.get("red", 0)
            green = bg_color.get("green", 0)
            blue = bg_color.get("blue", 0)

            # Determine highlight color based on RGB values
            color_name = self._rgb_to_highlight_color(red, green, blue)
            if color_name:
                marks.append({"type": "highlight", "attrs": {"color": color_name}})

        node = {"type": "text", "text": content}
        if marks:
            node["marks"] = marks

        return node

    def _rgb_to_highlight_color(self, red: float, green: float, blue: float) -> str | None:
        """Convert RGB values to a highlight color name."""
        # Check if it's close to any known highlight color
        for name, rgb in HIGHLIGHT_COLORS.items():
            if (
                abs(red - rgb["red"]) < 0.2 and
                abs(green - rgb["green"]) < 0.2 and
                abs(blue - rgb["blue"]) < 0.2
            ):
                return name

        # Check for claim highlight
        if (
            abs(red - CLAIM_HIGHLIGHT["red"]) < 0.2 and
            abs(green - CLAIM_HIGHLIGHT["green"]) < 0.2 and
            abs(blue - CLAIM_HIGHLIGHT["blue"]) < 0.2
        ):
            return "yellow"

        # Generic highlight detection (any non-white background)
        if red > 0.7 or green > 0.7 or blue > 0.7:
            if red > green and red > blue:
                return "red" if red > 0.8 else "orange"
            elif green > red and green > blue:
                return "green"
            elif blue > red and blue > green:
                return "blue"
            else:
                return "yellow"

        return None

    def _process_inline_object(self, inline_object_elem: dict) -> dict | None:
        """Process an inline object (usually an image)."""
        object_id = inline_object_elem.get("inlineObjectId", "")

        # Look up the actual object
        inline_obj = self._inline_objects.get(object_id, {})
        embedded = inline_obj.get("inlineObjectProperties", {}).get("embeddedObject", {})

        # Try to get image URI
        image_uri = embedded.get("imageProperties", {}).get("contentUri", "")
        if not image_uri:
            image_uri = embedded.get("imageProperties", {}).get("sourceUri", "")

        if image_uri:
            # Get size if available
            size = embedded.get("size", {})
            width = size.get("width", {}).get("magnitude")

            attrs = {"src": image_uri}
            if width:
                attrs["width"] = str(int(width))

            return {
                "type": "image",
                "attrs": attrs,
            }

        return None

    def _process_table(self, table: dict) -> dict:
        """Process a Google Docs table."""
        rows = table.get("tableRows", [])
        content = []

        for row_idx, row in enumerate(rows):
            cells = row.get("tableCells", [])
            row_content = []

            for cell in cells:
                cell_content = []
                for element in cell.get("content", []):
                    node, _ = self._process_structural_element(element, [element], 0)
                    if node:
                        if isinstance(node, list):
                            cell_content.extend(node)
                        else:
                            cell_content.append(node)

                # Determine cell type (header vs regular)
                cell_type = "tableHeader" if row_idx == 0 else "tableCell"

                row_content.append({
                    "type": cell_type,
                    "content": cell_content if cell_content else [{"type": "paragraph"}],
                })

            content.append({
                "type": "tableRow",
                "content": row_content,
            })

        return {
            "type": "table",
            "content": content,
        }


class HeaderFooterTransform:
    """Transform headers and footers between Scribe and Google Docs.

    Google Docs headers/footers are separate segments with their own content.
    Scribe stores header/footer as TipTap JSON in front_matter.
    """

    @staticmethod
    def create_header_footer_requests(
        header_content: dict | None,
        footer_content: dict | None,
        page_margins: dict | None = None,
    ) -> list[dict]:
        """Create Google Docs API requests for header/footer.

        Args:
            header_content: TipTap JSON for header (or None to skip)
            footer_content: TipTap JSON for footer (or None to skip)
            page_margins: Optional page margins dict {top, bottom, left, right}

        Returns:
            List of batchUpdate requests
        """
        requests = []

        # Create header if content provided
        if header_content:
            # First create the header
            requests.append({
                "createHeader": {
                    "type": "DEFAULT",
                    "sectionBreakLocation": {"index": 0},
                }
            })

        # Create footer if content provided
        if footer_content:
            requests.append({
                "createFooter": {
                    "type": "DEFAULT",
                    "sectionBreakLocation": {"index": 0},
                }
            })

        # Update page margins if provided
        if page_margins:
            margin_top = page_margins.get("top", 72)
            margin_bottom = page_margins.get("bottom", 72)
            margin_left = page_margins.get("left", 72)
            margin_right = page_margins.get("right", 72)

            requests.append({
                "updateDocumentStyle": {
                    "documentStyle": {
                        "marginTop": {"magnitude": margin_top, "unit": "PT"},
                        "marginBottom": {"magnitude": margin_bottom, "unit": "PT"},
                        "marginLeft": {"magnitude": margin_left, "unit": "PT"},
                        "marginRight": {"magnitude": margin_right, "unit": "PT"},
                    },
                    "fields": "marginTop,marginBottom,marginLeft,marginRight",
                }
            })

        return requests

    @staticmethod
    def create_header_content_requests(
        header_id: str,
        content: dict,
        variables: dict | None = None,
    ) -> list[dict]:
        """Create requests to insert content into a header.

        Args:
            header_id: The Google Docs header ID
            content: TipTap JSON content for the header
            variables: Optional dict with {pageNumber, totalPages, documentTitle}

        Returns:
            List of batchUpdate requests
        """
        # Extract text from TipTap content
        text = HeaderFooterTransform._extract_text_with_variables(content, variables or {})

        if not text:
            return []

        return [{
            "insertText": {
                "location": {"segmentId": header_id, "index": 0},
                "text": text,
            }
        }]

    @staticmethod
    def create_footer_content_requests(
        footer_id: str,
        content: dict,
        variables: dict | None = None,
    ) -> list[dict]:
        """Create requests to insert content into a footer.

        Args:
            footer_id: The Google Docs footer ID
            content: TipTap JSON content for the footer
            variables: Optional dict with {pageNumber, totalPages, documentTitle}

        Returns:
            List of batchUpdate requests
        """
        text = HeaderFooterTransform._extract_text_with_variables(content, variables or {})

        if not text:
            return []

        return [{
            "insertText": {
                "location": {"segmentId": footer_id, "index": 0},
                "text": text,
            }
        }]

    @staticmethod
    def _extract_text_with_variables(content: dict, variables: dict) -> str:
        """Extract text from TipTap content, replacing variable placeholders.

        Variables: {pageNumber}, {totalPages}, {documentTitle}, {date}
        """
        text_parts = []

        def extract_from_node(node: dict):
            if node.get("type") == "text":
                text = node.get("text", "")
                # Replace variables
                text = text.replace("{pageNumber}", str(variables.get("pageNumber", "1")))
                text = text.replace("{totalPages}", str(variables.get("totalPages", "1")))
                text = text.replace("{documentTitle}", variables.get("documentTitle", ""))
                text = text.replace("{date}", variables.get("date", ""))
                text_parts.append(text)
            elif "content" in node:
                for child in node.get("content", []):
                    extract_from_node(child)

        extract_from_node(content)
        return "".join(text_parts)

    @staticmethod
    def extract_header_footer_from_doc(google_doc: dict) -> tuple[dict | None, dict | None]:
        """Extract header and footer content from Google Docs response.

        Args:
            google_doc: The Google Docs document response

        Returns:
            Tuple of (header_content, footer_content) as TipTap JSON
        """
        header_content = None
        footer_content = None

        # Extract headers
        headers = google_doc.get("headers", {})
        for header_id, header in headers.items():
            text = HeaderFooterTransform._extract_text_from_segment(header)
            if text:
                header_content = {
                    "type": "doc",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
                }
                break  # Use first header found

        # Extract footers
        footers = google_doc.get("footers", {})
        for footer_id, footer in footers.items():
            text = HeaderFooterTransform._extract_text_from_segment(footer)
            if text:
                footer_content = {
                    "type": "doc",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
                }
                break  # Use first footer found

        return header_content, footer_content

    @staticmethod
    def _extract_text_from_segment(segment: dict) -> str:
        """Extract plain text from a Google Docs segment (header/footer)."""
        text_parts = []
        for element in segment.get("content", []):
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        content = elem["textRun"].get("content", "")
                        if content and content != "\n":
                            text_parts.append(content.rstrip("\n"))
        return " ".join(text_parts)

    @staticmethod
    def extract_page_margins_from_doc(google_doc: dict) -> dict | None:
        """Extract page margins from Google Docs response.

        Args:
            google_doc: The Google Docs document response

        Returns:
            Dict with {top, bottom, left, right} in pixels, or None
        """
        doc_style = google_doc.get("documentStyle", {})

        margin_top = doc_style.get("marginTop", {})
        margin_bottom = doc_style.get("marginBottom", {})
        margin_left = doc_style.get("marginLeft", {})
        margin_right = doc_style.get("marginRight", {})

        if not any([margin_top, margin_bottom, margin_left, margin_right]):
            return None

        def get_pixels(margin: dict) -> int:
            magnitude = margin.get("magnitude", 72)
            unit = margin.get("unit", "PT")
            # Convert to pixels (assuming 96 DPI)
            if unit == "PT":
                return int(magnitude * 96 / 72)
            elif unit == "IN":
                return int(magnitude * 96)
            return int(magnitude)

        return {
            "top": get_pixels(margin_top),
            "bottom": get_pixels(margin_bottom),
            "left": get_pixels(margin_left),
            "right": get_pixels(margin_right),
        }


def apply_claim_marks_from_footnotes(
    tiptap_json: dict,
    google_doc: dict,
) -> tuple[dict, int]:
    """Post-process TipTap JSON to apply claim marks from footnote metadata.

    This function looks at the positions of footnote references in the Google Doc
    and applies claim marks to the corresponding text in TipTap JSON.

    Returns:
        Tuple of (modified_tiptap_json, claims_applied)
    """
    claims_applied = 0

    # Extract footnote metadata
    footnotes = google_doc.get("footnotes", {})
    claim_footnotes = {}

    for footnote_id, footnote in footnotes.items():
        content = footnote.get("content", [])
        text = ""
        for element in content:
            if "paragraph" in element:
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        text += elem["textRun"].get("content", "")

        if CLAIM_MARKER in text:
            match = re.search(
                rf"{re.escape(CLAIM_MARKER)}(.+?){re.escape(MARKER_END)}",
                text
            )
            if match:
                try:
                    data = json.loads(match.group(1))
                    claim_footnotes[footnote_id] = data
                except json.JSONDecodeError:
                    pass

    # TODO: Map footnote references to text positions and apply claim marks
    # This requires tracking positions during the parse phase

    return tiptap_json, claims_applied
