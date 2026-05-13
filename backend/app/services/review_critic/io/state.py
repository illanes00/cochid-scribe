"""Pipeline state I/O: load/save JSON checkpoints with input hashing.

Each stage writes its output to a JSON file in critic-state/.
Each output also writes a hash of its inputs so re-runs can detect drift.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

STATE_DIR = Path("/srv/projects/cochid/cochid-scribe/docs/cif-review/critic-state")
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _hash_payload(data: Any) -> str:
    """SHA256 of a JSON-serializable payload."""
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    if isinstance(data, list) and data and isinstance(data[0], BaseModel):
        data = [item.model_dump(mode="json") for item in data]
    blob = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def save_stage(
    filename: str,
    payload: list[BaseModel] | BaseModel | dict | list,
    input_hashes: dict[str, str] | None = None,
) -> Path:
    """Save a stage output to JSON.

    Args:
        filename: e.g. "10_classified.json"
        payload: list of Pydantic models, single model, dict, or list
        input_hashes: dict mapping input source name to its hash

    Returns:
        Path to the written file.
    """
    path = STATE_DIR / filename

    if isinstance(payload, BaseModel):
        body = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        if payload and isinstance(payload[0], BaseModel):
            body = [item.model_dump(mode="json") for item in payload]
        else:
            body = payload
    else:
        body = payload

    wrapper = {
        "_meta": {
            "stage": filename,
            "saved_at": datetime.utcnow().isoformat(),
            "input_hashes": input_hashes or {},
            "output_hash": _hash_payload(body),
            "count": len(body) if isinstance(body, list) else 1,
        },
        "data": body,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(wrapper, f, ensure_ascii=False, indent=2, default=str)

    return path


def load_stage(filename: str, model: Type[T] | None = None) -> Any:
    """Load a stage output.

    Args:
        filename: e.g. "10_classified.json"
        model: if provided, parse each item as this Pydantic model

    Returns:
        list of model instances, or raw dict/list if no model provided.
    """
    path = STATE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Stage output not found: {path}")

    with open(path, encoding="utf-8") as f:
        wrapper = json.load(f)

    body = wrapper.get("data", wrapper)

    if model is None:
        return body

    if isinstance(body, list):
        return [model(**item) for item in body]
    return model(**body)


def stage_exists(filename: str) -> bool:
    return (STATE_DIR / filename).exists()


def get_stage_meta(filename: str) -> dict | None:
    path = STATE_DIR / filename
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        wrapper = json.load(f)
    return wrapper.get("_meta")


def hash_file(path: Path | str) -> str:
    """SHA256 hash of a file's contents (truncated to 16 chars)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]
