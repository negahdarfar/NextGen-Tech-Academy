"""Durable, resumable state for long-form documentary production.

This module tracks work only; it does not call paid providers or generate media.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

STAGES = ("planned", "researched", "scripted", "narrated", "assembled", "reviewed")


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def initialize_documentary_run(plan_path: str | Path,
                                state_path: str | Path) -> Path:
    """Create a run manifest from a blueprint, without overwriting an existing run."""
    source = Path(plan_path)
    target = Path(state_path)
    plan = json.loads(source.read_text(encoding="utf-8"))
    chapters = plan.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Blueprint must contain at least one chapter.")
    if target.exists():
        raise FileExistsError(f"Run state already exists: {target}; refusing to overwrite it.")
    run = {
        "schema_version": 1,
        "topic": plan.get("topic", ""),
        "target_duration_seconds": plan.get("target_duration_seconds"),
        "plan_path": str(source),
        "status": "in_progress",
        "chapters": [
            {
                "chapter": int(chapter["chapter"]),
                "title": str(chapter["title"]),
                "status": "planned",
                "attempts": 0,
                "outputs": {},
                "last_error": None,
            }
            for chapter in chapters
        ],
    }
    _atomic_json_write(target, run)
    return target


def load_run_state(state_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(state_path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("chapters"), list):
        raise ValueError("Unsupported or invalid documentary run manifest.")
    return payload


def update_chapter_state(state_path: str | Path, chapter_number: int,
                         status: str | None = None,
                         outputs: dict[str, str] | None = None,
                         error: str | None = None,
                         force: bool = False) -> dict[str, Any]:
    """Advance one chapter; preserve completed outputs and record retryable errors."""
    if status is not None and status not in STAGES:
        raise ValueError(f"status must be one of: {', '.join(STAGES)}")
    path = Path(state_path)
    run = load_run_state(path)
    chapter = next((item for item in run["chapters"]
                    if item.get("chapter") == chapter_number), None)
    if chapter is None:
        raise ValueError(f"Unknown chapter number: {chapter_number}")
    if error:
        chapter["attempts"] = int(chapter.get("attempts", 0)) + 1
        chapter["last_error"] = str(error)[:2000]
    if status is not None:
        old_index = STAGES.index(chapter["status"])
        new_index = STAGES.index(status)
        if new_index < old_index and not force:
            raise ValueError("Stage regression is blocked; use force=True deliberately.")
        if new_index > old_index + 1 and not force:
            raise ValueError("Stages cannot be skipped; complete the preceding stage first.")
        chapter["status"] = status
        chapter["last_error"] = None
    if outputs:
        existing = dict(chapter.get("outputs", {}))
        for key, value in outputs.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Output names and paths must be strings.")
            existing[key] = value
        chapter["outputs"] = existing
    if all(item.get("status") == "reviewed" for item in run["chapters"]):
        run["status"] = "ready_for_human_approval"
    _atomic_json_write(path, run)
    return run
