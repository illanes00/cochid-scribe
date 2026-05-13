"""Rule-based QA checks for the pipeline output."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.qa.benja_predicate import benja_alignment
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    QAFinding,
    QAReport,
    ReplyEntry,
    ResolvedDecision,
)

DOC_FILE = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/informe-final-text.md")


def check_uniqueness(edits: list[EditPatch], doc_text: str) -> list[QAFinding]:
    findings = []
    for e in edits:
        if e.scope in ("local", "structural") and e.original_text:
            count = doc_text.count(e.original_text)
            if count == 0:
                findings.append(
                    QAFinding(
                        rule="uniqueness",
                        severity="error",
                        target_id=e.edit_id,
                        message=f"original_text not found (0 matches)",
                    )
                )
            elif count > 1:
                findings.append(
                    QAFinding(
                        rule="uniqueness",
                        severity="error",
                        target_id=e.edit_id,
                        message=f"original_text appears {count} times (not unique)",
                    )
                )
    return findings


NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|millones?|mil|US\$|CLP|MM\$)?\b")


def extract_numbers(text: str) -> set[str]:
    return set(m.group() for m in NUMBER_RE.finditer(text))


def check_no_unverified_numbers(edits: list[EditPatch]) -> list[QAFinding]:
    """Numbers in replacement_text should appear somewhere in ledger or original_text."""
    ledger = load_ledger()
    ledger_text = " ".join(f.evidence + " " + f.claim_text for f in ledger.facts)
    ledger_numbers = extract_numbers(ledger_text)

    findings = []
    for e in edits:
        repl = e.replacement_text or e.replace_with or ""
        orig = e.original_text or ""
        new_numbers = extract_numbers(repl) - extract_numbers(orig) - ledger_numbers
        # Filter very common numbers
        new_numbers = {n for n in new_numbers if n not in {"1", "2", "3", "4", "5", "10", "100"}}
        if new_numbers:
            findings.append(
                QAFinding(
                    rule="unverified_numbers",
                    severity="warning",
                    target_id=e.edit_id,
                    message=f"Edit introduces numbers not in ledger: {new_numbers}",
                )
            )
    return findings


def check_benja_alignment(edits: list[EditPatch]) -> list[QAFinding]:
    findings = []
    for e in edits:
        repl = e.replacement_text or e.replace_with or ""
        if len(repl) < 50:
            continue
        score = benja_alignment(repl)
        if score < 2:
            findings.append(
                QAFinding(
                    rule="benja_alignment",
                    severity="error",
                    target_id=e.edit_id,
                    message=f"Edit violates editorial line (score {score}/5): {repl[:80]}",
                )
            )
        elif score < 3:
            findings.append(
                QAFinding(
                    rule="benja_alignment",
                    severity="warning",
                    target_id=e.edit_id,
                    message=f"Edit borderline (score {score}/5)",
                )
            )
    return findings


def check_decisions_have_replies(
    decisions: list[ResolvedDecision], replies: list[ReplyEntry]
) -> list[QAFinding]:
    reply_ids = {r.comment_id for r in replies}
    findings = []
    for d in decisions:
        if d.comment_id not in reply_ids:
            findings.append(
                QAFinding(
                    rule="completeness",
                    severity="error",
                    target_id=d.comment_id,
                    message="Decision has no reply",
                )
            )
    return findings


def check_replies_in_spanish(replies: list[ReplyEntry]) -> list[QAFinding]:
    findings = []
    for r in replies:
        ascii_only = sum(1 for ch in r.reply_text if ord(ch) < 128 and ch.isalpha())
        spanish_chars = sum(1 for ch in r.reply_text if ch in "áéíóúñÁÉÍÓÚÑ¿¡")
        if len(r.reply_text) > 50 and ascii_only > 0 and spanish_chars == 0:
            findings.append(
                QAFinding(
                    rule="spanish_only",
                    severity="warning",
                    target_id=r.comment_id,
                    message="Reply has no Spanish-specific chars (might be in English)",
                )
            )
    return findings


def run_qa(
    classified: list[ClassifiedComment],
    decisions: list[ResolvedDecision],
    edits: list[EditPatch],
    replies: list[ReplyEntry],
) -> QAReport:
    doc_text = DOC_FILE.read_text() if DOC_FILE.exists() else ""

    findings = []
    findings.extend(check_uniqueness(edits, doc_text))
    findings.extend(check_no_unverified_numbers(edits))
    findings.extend(check_benja_alignment(edits))
    findings.extend(check_decisions_have_replies(decisions, replies))
    findings.extend(check_replies_in_spanish(replies))

    severity_count = Counter(f.severity for f in findings)
    blocked = [f.target_id for f in findings if f.severity == "error" and f.rule in ("uniqueness", "benja_alignment")]
    flagged = [f.target_id for f in findings if f.severity == "warning"]

    return QAReport(
        findings=findings,
        edits_blocked=list(set(blocked)),
        edits_flagged=list(set(flagged)),
        passed=severity_count.get("error", 0) == 0,
    )
