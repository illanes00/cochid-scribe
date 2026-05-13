"""Pydantic models for the multi-stage critic pipeline.

Each model represents the output of a specific pipeline stage.
The invariant `comment_id` correlates a comment across all stages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Stage 0: Input
# ============================================================================


class CommentInput(BaseModel):
    """Normalized input from comment-mapping.json."""

    id: str
    author: str
    initials: str
    date: str
    source: str
    comment_text: str
    search_phrase: str
    section_hint: str | None = None
    confidence: Literal["high", "medium", "low"]
    notes: str = ""


# ============================================================================
# Stage 1: Classifier
# ============================================================================


CommentType = Literal[
    "factual",  # Asserts or questions a specific fact
    "structural",  # About document structure (sections, order, headings)
    "stylistic",  # About wording, jargon, tone
    "methodological",  # About how analysis was done (selection, sources)
    "strategic",  # About overall direction (prescriptive vs descriptive)
    "question",  # Reviewer asking a question
    "general",  # General observation about the document as a whole
]

Specificity = Literal[
    "local",  # Affects a specific text span
    "section",  # Affects a section
    "document",  # Affects the document as a whole
]

Verifiability = Literal[
    "factual_claim",  # Reviewer asserts something checkable
    "opinion",  # Subjective preference
    "suggestion",  # Proposed change without factual claim
]


class ClassifiedComment(BaseModel):
    """Output of Stage 1 (Classifier)."""

    id: str
    author: str
    comment_text: str
    quoted_text: str | None = None
    section_hint: str | None = None

    # Classification
    type: CommentType
    specificity: Specificity
    verifiability: Verifiability
    touches_sections: list[str] = Field(default_factory=list)
    has_embedded_claim: bool = False
    raw_claims: list[str] = Field(default_factory=list)

    # For style edits: hint whether the rule should apply globally
    style_consistency_hint: Literal["consistent_rule", "local_substitution", "n/a"] = (
        "n/a"
    )


# ============================================================================
# Stage 2: Verifier
# ============================================================================


VerificationStatus = Literal["confirmed", "refuted", "inconclusive", "needs_data"]


class VerificationResult(BaseModel):
    """A single verified or attempted-to-verify claim."""

    claim_id: str  # e.g. "V-CIF1-a"
    source_comment_id: str | None = None  # None if pre-seeded
    claim_text: str
    status: VerificationStatus
    evidence: str
    authoritative_source: str | None = None
    confidence: float = Field(ge=0, le=1)
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class BibliographyAuditEntry(BaseModel):
    """Verification status for a single bibliography entry."""

    bib_key: str
    title: str
    author: str
    year: int | None
    url: str | None
    doi: str | None
    url_status: Literal["ok", "broken", "redirect", "not_checked"] = "not_checked"
    title_match: Literal["exact", "fuzzy", "mismatch", "not_checked"] = "not_checked"
    author_match: Literal["exact", "fuzzy", "mismatch", "not_checked"] = "not_checked"
    year_match: Literal["exact", "off_by_one", "mismatch", "not_checked"] = "not_checked"
    issues: list[str] = Field(default_factory=list)


class VerificationLedger(BaseModel):
    """The full verification state."""

    facts: list[VerificationResult] = Field(default_factory=list)
    bibliography: list[BibliographyAuditEntry] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Stage 3: Critic
# ============================================================================


Recommendation = Literal[
    "ACCEPT",
    "ACCEPT_PARTIAL",
    "REJECT",
    "DEFER",
    "NEEDS_DATA",
]


ProposedAction = Literal[
    "apply_local_edit",
    "apply_consistent_edit",
    "restructure_section",
    "add_content",
    "delete_content",
    "none_reply_only",
]


class CriticJudgment(BaseModel):
    """Output of Stage 3 (Critic) for one comment."""

    comment_id: str
    recommendation: Recommendation
    reasoning: str  # 2-4 sentences

    # Scores (0..5) for arbitration
    improvement_score: int = Field(ge=0, le=5)
    preference_score: int = Field(ge=0, le=5)
    benja_alignment: int = Field(ge=0, le=5)
    correctness_score: int = Field(ge=0, le=5)

    # Cross-references
    conflicts_with: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)
    verification_refs: list[str] = Field(default_factory=list)

    # Action plan (Critic suggests, Edit Generator implements)
    proposed_action: ProposedAction
    requires_director_approval: bool = False  # True if DEFER → ACCEPT_PARTIAL


# ============================================================================
# Stage 4: Conflict Resolver
# ============================================================================


class ConflictCluster(BaseModel):
    """A group of comments that interact (overlap, conflict, support)."""

    cluster_id: str
    comment_ids: list[str]
    cluster_type: Literal["overlap", "section", "explicit_conflict"]
    section: str | None = None


class ResolvedDecision(BaseModel):
    """Final decision after conflict resolution. May override Critic."""

    comment_id: str
    final_recommendation: Recommendation
    proposed_action: ProposedAction
    requires_director_approval: bool = False
    cluster_id: str | None = None
    override_reason: str | None = None  # If different from Critic's recommendation
    final_reasoning: str


# ============================================================================
# Stage 5: Edit Generator
# ============================================================================


EditScope = Literal["local", "consistent", "structural"]


class EditPatch(BaseModel):
    """An edit to apply to the document."""

    edit_id: str
    source_comment_ids: list[str]  # Often >1 for consistent edits
    scope: EditScope
    section_anchor: str | None = None

    # For local/structural: exact text replacement
    original_text: str = ""
    replacement_text: str = ""

    # For consistent: regex pattern
    find_pattern: str | None = None
    replace_with: str | None = None
    context_filter: str | None = None  # e.g. "exclude_bibliography"

    # Realized hits (for consistent edits, computed at apply time)
    realized_locations: list[dict] = Field(default_factory=list)

    rationale: str
    confidence: float = Field(ge=0, le=1)


# ============================================================================
# Stage 6: Reply Writer
# ============================================================================


class ReplyEntry(BaseModel):
    """A reply to a comment, attributed to the author of the doc."""

    comment_id: str
    reply_text: str  # Spanish, 2-4 sentences
    decision_label: Literal[
        "ACEPTADO",
        "ACEPTADO_PARCIAL",
        "RECHAZADO",
        "PENDIENTE_DIRECTORES",
        "PENDIENTE_DATOS",
        "RESPUESTA",  # for reply_only
    ]
    references_edit_ids: list[str] = Field(default_factory=list)


# ============================================================================
# QA
# ============================================================================


class QAFinding(BaseModel):
    """A single QA issue."""

    rule: str
    severity: Literal["error", "warning", "info"]
    target_id: str  # comment_id or edit_id
    message: str


class QAReport(BaseModel):
    """Output of the QA gate."""

    findings: list[QAFinding] = Field(default_factory=list)
    edits_blocked: list[str] = Field(default_factory=list)
    edits_flagged: list[str] = Field(default_factory=list)
    spotcheck_results: dict[str, dict] = Field(default_factory=dict)
    passed: bool = True


# ============================================================================
# Pipeline state
# ============================================================================


class StageMetadata(BaseModel):
    """Hash + timestamp tracking for a stage output."""

    stage_name: str
    completed_at: datetime
    input_hash: str  # SHA256 of stage's inputs
    output_count: int
    duration_seconds: float
