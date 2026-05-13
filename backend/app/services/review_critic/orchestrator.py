"""Orchestrator: runs the full critic pipeline.

Usage:
    python -m app.services.review_critic.orchestrator [--from-stage=N] [--to-stage=N]

Stages:
  1 = Classifier
  3 = Critic
  4 = Conflict Resolver
  5 = Edit Generator
  6 = Reply Writer
  7 = QA + DOCX assembly
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Callable

from app.services.review_critic.agents import (
    classifier,
    conflict_resolver,
    critic,
    edit_generator,
    reply_writer,
)
from app.services.review_critic.io import docx_assembler
from app.services.review_critic.io.state import save_stage, load_stage, stage_exists
from app.services.review_critic.qa.rule_checks import run_qa
from app.services.review_critic.schemas import (
    ClassifiedComment,
    EditPatch,
    ReplyEntry,
    ResolvedDecision,
)


STAGES: list[tuple[int, str, Callable]] = [
    (1, "Classifier", classifier.run),
    (3, "Critic", critic.run),
    (4, "Conflict Resolver", conflict_resolver.run),
    (5, "Edit Generator", edit_generator.run),
    (6, "Reply Writer", reply_writer.run),
]


def run_qa_stage():
    classified = load_stage("10_classified.json", ClassifiedComment)
    decisions = load_stage("41_resolved_decisions.json", ResolvedDecision)
    edits = load_stage("50_edit_patches.json", EditPatch)
    replies = load_stage("60_replies.json", ReplyEntry)
    report = run_qa(classified, decisions, edits, replies)
    save_stage("70_qa_report.json", report)
    print(f"QA: {len(report.findings)} findings, passed={report.passed}")
    print(f"  Errors: {sum(1 for f in report.findings if f.severity == 'error')}")
    print(f"  Warnings: {sum(1 for f in report.findings if f.severity == 'warning')}")
    return report


def run_assembly_stage():
    output = docx_assembler.run()
    print(f"Assembled docx → {output}")
    return output


def run_pipeline(from_stage: int = 1, to_stage: int = 7) -> None:
    """Run the pipeline from `from_stage` through `to_stage`."""
    for num, name, fn in STAGES:
        if num < from_stage or num > to_stage:
            continue
        print(f"\n{'='*60}\nSTAGE {num}: {name}\n{'='*60}")
        fn()

    if 7 >= from_stage and 7 <= to_stage:
        print(f"\n{'='*60}\nSTAGE 7: QA + DOCX Assembly\n{'='*60}")
        run_qa_stage()
        run_assembly_stage()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-stage", type=int, default=1)
    parser.add_argument("--to-stage", type=int, default=7)
    args = parser.parse_args()
    run_pipeline(args.from_stage, args.to_stage)
