"""Shared LLM wrapper using Claude CLI subprocess.

Same pattern as review_respond.py: subprocess to /home/illanes00/.local/bin/claude
with -p flag for headless mode.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path

_log = logging.getLogger(__name__)

CLAUDE_BIN = "/home/illanes00/.local/bin/claude"
CWD = "/srv/projects/cochid/cochid-scribe"


def call_claude(
    user_content: str,
    system_prompt: str,
    model: str = "sonnet",
    timeout: int = 240,
) -> str:
    """Call Claude CLI in headless mode and return stdout text."""
    result = subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            "--output-format", "text",
            "--append-system-prompt", system_prompt,
            "--model", model,
        ],
        input=user_content,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=CWD,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed (code {result.returncode}): {result.stderr[:500]}")

    out = result.stdout.strip()
    if not out:
        raise RuntimeError(f"Empty Claude CLI response. Stderr: {result.stderr[:500]}")
    return out


def extract_json_array(text: str) -> list:
    """Extract a JSON array from text. Tolerates markdown fences and prose."""
    # Try fenced code blocks first
    fence = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Try first [ to last ]
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        raise ValueError(f"No JSON array found in response. Sample: {text[:300]}")

    snippet = text[start : end + 1]
    return json.loads(snippet)


def extract_json_object(text: str) -> dict:
    """Extract a JSON object from text."""
    fence = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"No JSON object found in response. Sample: {text[:300]}")

    return json.loads(text[start : end + 1])
