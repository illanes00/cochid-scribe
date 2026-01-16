"""Content conversion utilities using Pandoc via pypandoc."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pypandoc

EXPORT_ROOT = Path("exports")
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates" / "pandoc"


def ensure_export_root() -> Path:
    """Ensure export directory exists."""
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return EXPORT_ROOT


def convert_text(text: str, to_format: str, from_format: str) -> str:
    """Convert plain text between formats using Pandoc."""
    return pypandoc.convert_text(text, to_format, format=from_format)


def convert_text_to_file(
    text: str,
    to_format: str,
    from_format: str,
    output_path: Path,
    extra_args: list[str] | None = None,
) -> Path:
    """Convert text and write the result to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pypandoc.convert_text(
        text,
        to_format,
        format=from_format,
        outputfile=str(output_path),
        extra_args=extra_args or [],
    )
    return output_path


def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown."""
    return convert_text(html, to_format="markdown", from_format="html")


def markdown_to_html(markdown: str) -> str:
    """Convert Markdown to HTML."""
    return convert_text(markdown, to_format="html", from_format="markdown")


def html_to_binary(
    html: str,
    to_format: str,
    output_path: Path,
    extra_args: list[str] | None = None,
) -> Path:
    """Convert HTML to a binary format (docx, pptx, pdf, etc.)."""
    return convert_text_to_file(
        html,
        to_format=to_format,
        from_format="html",
        output_path=output_path,
        extra_args=extra_args,
    )


def markdown_to_binary(
    markdown: str,
    to_format: str,
    output_path: Path,
    extra_args: list[str] | None = None,
) -> Path:
    """Convert Markdown to a binary format (docx, pptx, pdf, etc.)."""
    return convert_text_to_file(
        markdown,
        to_format=to_format,
        from_format="markdown",
        output_path=output_path,
        extra_args=extra_args,
    )


def get_default_template() -> Path:
    """Return path to the default Pandoc template."""
    template = TEMPLATE_DIR / "scribe.tex"
    return template


def temp_output_path(suffix: str) -> Path:
    """Create a temp path for output files."""
    ensure_export_root()
    fd, path = tempfile.mkstemp(prefix="scribe_", suffix=suffix, dir=str(EXPORT_ROOT))
    Path(path).unlink(missing_ok=True)
    return Path(path)
