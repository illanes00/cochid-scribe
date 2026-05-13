"""CLI for the review_critic pipeline.

Usage:
    python -m app.services.review_critic.cli <command> [args]

Commands:
    seed-ledger       — Initialize verification ledger
    classify          — Run Stage 1 (Classifier)
    critique          — Run Stage 3 (Critic)
    resolve           — Run Stage 4 (Conflict Resolver)
    edits             — Run Stage 5 (Edit Generator)
    replies           — Run Stage 6 (Reply Writer)
    qa                — Run QA gate
    assemble          — Build docx with edits + replies
    deliver           — Upload to Drive + generate outputs
    full              — Run all stages 1-8
    status            — Show current state of pipeline
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.services.review_critic.io.state import STATE_DIR, get_stage_meta, stage_exists


STAGE_FILES = [
    ("10_classified.json", "Stage 1 (Classifier)"),
    ("21_verification_ledger.json", "Verification Ledger"),
    ("30_critic_judgments.json", "Stage 3 (Critic)"),
    ("40_conflict_clusters.json", "Stage 4 (Clusters)"),
    ("41_resolved_decisions.json", "Stage 4 (Resolver)"),
    ("50_edit_patches.json", "Stage 5 (Edits)"),
    ("60_replies.json", "Stage 6 (Replies)"),
    ("70_qa_report.json", "Stage 7 (QA)"),
]


def cmd_status():
    print("\n=== Pipeline State ===\n")
    for fname, label in STAGE_FILES:
        if stage_exists(fname):
            meta = get_stage_meta(fname)
            count = meta.get("count", 0) if meta else 0
            saved = meta.get("saved_at", "?")[:19] if meta else "?"
            print(f"  ✓  {label:35s}  {count:5d} items  ({saved})")
        else:
            print(f"  ✗  {label:35s}  not yet run")


def cmd_seed_ledger():
    from app.services.review_critic.io.verification_ledger import seed_known_facts, save_ledger
    ledger = seed_known_facts()
    save_ledger(ledger)
    print(f"Seeded ledger with {len(ledger.facts)} facts")


def cmd_full():
    from app.services.review_critic.orchestrator import run_pipeline
    run_pipeline(1, 7)
    from app.services.review_critic.deliver import run as deliver_run
    deliver_run()


COMMANDS = {
    "seed-ledger": cmd_seed_ledger,
    "classify": lambda: __import__("app.services.review_critic.agents.classifier", fromlist=["run"]).run(),
    "critique": lambda: __import__("app.services.review_critic.agents.critic", fromlist=["run"]).run(),
    "resolve": lambda: __import__("app.services.review_critic.agents.conflict_resolver", fromlist=["run"]).run(),
    "edits": lambda: __import__("app.services.review_critic.agents.edit_generator", fromlist=["run"]).run(),
    "replies": lambda: __import__("app.services.review_critic.agents.reply_writer", fromlist=["run"]).run(),
    "qa": lambda: __import__("app.services.review_critic.orchestrator", fromlist=["run_qa_stage"]).run_qa_stage(),
    "assemble": lambda: __import__("app.services.review_critic.io.docx_assembler", fromlist=["run"]).run(),
    "deliver": lambda: __import__("app.services.review_critic.deliver", fromlist=["run"]).run(),
    "full": cmd_full,
    "status": cmd_status,
}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"\nAvailable: {', '.join(COMMANDS)}")
        sys.exit(1)

    cmd = COMMANDS[sys.argv[1]]
    cmd()
