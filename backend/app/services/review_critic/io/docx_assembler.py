"""DOCX assembler: takes the source docx + edits + replies and produces
a new docx with <w:ins>/<w:del> track changes and comment threads with replies.

Uses lxml directly to manipulate the WordprocessingML XML.
"""

from __future__ import annotations

import logging
import re
import zipfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from lxml import etree

from app.services.review_critic.io.state import load_stage
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    QAReport,
    ReplyEntry,
    ResolvedDecision,
)

_log = logging.getLogger(__name__)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {"w": W}

SOURCE_DOCX = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/informe-final-comentarios-FINAL.docx"
)
OUTPUT_DOCX = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/output/informe-final-revisado.docx"
)

AUTHOR = "Corrector"
DATE = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def w_tag(name: str) -> str:
    return f"{{{W}}}{name}"


def find_run_with_text(body: etree._Element, target_text: str) -> tuple[etree._Element, etree._Element, str] | None:
    """Find first run whose <w:t> contains target_text. Returns (run, t_element, full_text)."""
    for run in body.iter(w_tag("r")):
        t = run.find(w_tag("t"))
        if t is not None and t.text and target_text in t.text:
            return run, t, t.text
    return None


def split_run_with_replacement(
    parent: etree._Element,
    run: etree._Element,
    t_elem: etree._Element,
    full_text: str,
    target: str,
    replacement: str,
    edit_id: int,
) -> bool:
    """Replace `target` in `t_elem` with: keep `before`, w:del(target), w:ins(replacement), keep `after`.

    Returns True if successful.
    """
    pos = full_text.find(target)
    if pos < 0:
        return False

    before = full_text[:pos]
    after = full_text[pos + len(target) :]

    rpr = run.find(w_tag("rPr"))
    rpr_xml = etree.tostring(rpr) if rpr is not None else None

    run_idx = list(parent).index(run)

    # Update existing run with `before` text
    t_elem.text = before
    if not before:
        # Empty t — keep but mark space-preserve
        t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    insert_offset = 1

    # w:del element
    if target:
        del_elem = etree.Element(w_tag("del"))
        del_elem.set(w_tag("id"), str(edit_id))
        del_elem.set(w_tag("author"), AUTHOR)
        del_elem.set(w_tag("date"), DATE)
        del_run = etree.SubElement(del_elem, w_tag("r"))
        if rpr_xml:
            del_run.append(etree.fromstring(rpr_xml))
        del_t = etree.SubElement(del_run, w_tag("delText"))
        del_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        del_t.text = target
        parent.insert(run_idx + insert_offset, del_elem)
        insert_offset += 1
        edit_id += 1

    # w:ins element
    if replacement:
        ins_elem = etree.Element(w_tag("ins"))
        ins_elem.set(w_tag("id"), str(edit_id))
        ins_elem.set(w_tag("author"), AUTHOR)
        ins_elem.set(w_tag("date"), DATE)
        ins_run = etree.SubElement(ins_elem, w_tag("r"))
        if rpr_xml:
            ins_run.append(etree.fromstring(rpr_xml))
        ins_t = etree.SubElement(ins_run, w_tag("t"))
        ins_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        ins_t.text = replacement
        parent.insert(run_idx + insert_offset, ins_elem)
        insert_offset += 1

    # `after` text
    if after:
        after_run = etree.Element(w_tag("r"))
        if rpr_xml:
            after_run.append(etree.fromstring(rpr_xml))
        after_t = etree.SubElement(after_run, w_tag("t"))
        after_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        after_t.text = after
        parent.insert(run_idx + insert_offset, after_run)

    return True


def apply_edit(body: etree._Element, edit: EditPatch, base_id: int) -> tuple[bool, int]:
    """Apply one edit to the body. Returns (success, next_id)."""
    if edit.scope in ("local", "structural"):
        if not edit.original_text:
            return False, base_id
        result = find_run_with_text(body, edit.original_text)
        if result is None:
            _log.warning("Edit %s: original_text not found", edit.edit_id)
            return False, base_id
        run, t_elem, full_text = result
        parent = run.getparent()
        success = split_run_with_replacement(
            parent,
            run,
            t_elem,
            full_text,
            edit.original_text,
            edit.replacement_text,
            base_id,
        )
        return success, base_id + 2

    elif edit.scope == "consistent":
        if not edit.find_pattern:
            return False, base_id
        try:
            pattern = re.compile(edit.find_pattern)
        except re.error:
            _log.warning("Edit %s: invalid regex %s", edit.edit_id, edit.find_pattern)
            return False, base_id

        # Apply to ALL runs whose text matches
        applied_count = 0
        next_id = base_id
        # We need to iterate over a snapshot since we mutate
        runs_with_match = []
        for run in body.iter(w_tag("r")):
            # Skip runs inside w:ins/w:del already (avoid double-application)
            parent = run.getparent()
            if parent is not None and parent.tag in (w_tag("ins"), w_tag("del")):
                continue
            t = run.find(w_tag("t"))
            if t is not None and t.text and pattern.search(t.text):
                runs_with_match.append((run, t))

        for run, t_elem in runs_with_match:
            parent = run.getparent()
            if parent is None:
                continue
            full_text = t_elem.text
            match = pattern.search(full_text)
            if not match:
                continue
            target = match.group()
            replacement = edit.replace_with or ""
            success = split_run_with_replacement(
                parent, run, t_elem, full_text, target, replacement, next_id
            )
            if success:
                applied_count += 1
                next_id += 2
        _log.info("Edit %s (consistent): %d hits applied", edit.edit_id, applied_count)
        return applied_count > 0, next_id

    return False, base_id


def add_replies_to_comments_xml(
    comments_xml: bytes,
    replies: list[ReplyEntry],
    classified_by_id: dict[str, ClassifiedComment],
) -> bytes:
    """Append reply text to each comment in word/comments.xml.

    Strategy:
    1. If comment text starts with [C-XXX], match by that prefix.
    2. Otherwise, match by content similarity to a ClassifiedComment.
    """
    root = etree.fromstring(comments_xml)
    reply_by_id = {r.comment_id: r for r in replies}

    # Build content → ID lookup for fallback matching
    content_to_id: dict[str, str] = {}
    for cid, c in classified_by_id.items():
        # Use first 60 chars of comment_text (lowercased, stripped) as key
        key = (c.comment_text or "").strip().lower()[:60]
        if key:
            content_to_id[key] = cid

    matched = 0
    unmatched = 0
    for comment in root.iter(w_tag("comment")):
        comment_text = " ".join(t.text for t in comment.iter(w_tag("t")) if t.text)
        cid = None

        # Strategy 1: prefix match
        match = re.match(r"\[([^\]]+)\]", comment_text)
        if match:
            candidate = match.group(1)
            if candidate in reply_by_id:
                cid = candidate

        # Strategy 2: content match for original comments without prefix
        if cid is None:
            # Try to match by first 60 chars of comment text
            stripped = comment_text.strip().lower()
            for key, candidate_id in content_to_id.items():
                if key and key in stripped:
                    if candidate_id in reply_by_id:
                        cid = candidate_id
                        break
            # Also try reverse: comment text contained in classified text
            if cid is None:
                for key, candidate_id in content_to_id.items():
                    if stripped[:50] and stripped[:50] in key:
                        if candidate_id in reply_by_id:
                            cid = candidate_id
                            break

        if cid is None:
            unmatched += 1
            continue

        reply = reply_by_id[cid]

        # Append paragraph with reply
        new_p = etree.SubElement(comment, w_tag("p"))
        new_r = etree.SubElement(new_p, w_tag("r"))
        new_t = etree.SubElement(new_r, w_tag("t"))
        new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        new_t.text = f"\n[{reply.decision_label}] {reply.reply_text}"
        matched += 1

    _log.info("Replies attached: %d matched, %d unmatched", matched, unmatched)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def assemble(
    edits: list[EditPatch],
    replies: list[ReplyEntry],
    classified: list[ClassifiedComment],
    output_path: Path = OUTPUT_DOCX,
) -> Path:
    """Build the final docx with edits + replies."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not SOURCE_DOCX.exists():
        raise FileNotFoundError(f"Source docx not found: {SOURCE_DOCX}")

    classified_by_id = {c.id: c for c in classified}

    with zipfile.ZipFile(SOURCE_DOCX) as zin:
        doc_xml = zin.read("word/document.xml")
        comments_xml = zin.read("word/comments.xml") if "word/comments.xml" in zin.namelist() else None

    # Apply edits to document.xml
    doc_root = etree.fromstring(doc_xml)
    body = doc_root.find(w_tag("body"))
    if body is None:
        body = doc_root

    next_id = 10000
    applied = 0
    skipped = 0
    for edit in edits:
        success, next_id = apply_edit(body, edit, next_id)
        if success:
            applied += 1
        else:
            skipped += 1

    _log.info("Applied %d edits, skipped %d", applied, skipped)

    new_doc_xml = etree.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    # Add replies to comments.xml
    new_comments_xml = comments_xml
    if comments_xml and replies:
        new_comments_xml = add_replies_to_comments_xml(
            comments_xml, replies, classified_by_id
        )

    # Write output zip
    with zipfile.ZipFile(SOURCE_DOCX) as zin:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/comments.xml" and new_comments_xml:
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))

    _log.info("Output written to %s (%d edits applied, %d skipped)", output_path, applied, skipped)
    return output_path


def run() -> Path:
    edits = load_stage("50_edit_patches.json", EditPatch)
    replies = load_stage("60_replies.json", ReplyEntry)
    classified = load_stage("10_classified.json", ClassifiedComment)
    return assemble(edits, replies, classified)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(f"Output: {run()}")
