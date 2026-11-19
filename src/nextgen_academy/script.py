"""Utilities for a one-minute four-scene documentary script package."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def default_storyboard(topic: str) -> list[dict[str, str]]:
    """Create editable scene briefs; these are prompts, not verified narration."""
    topic = topic.strip()
    if not topic:
        raise ValueError("topic is required")
    beats = [
        ("The hook", f"Open with a striking real-world visual that introduces {topic}."),
        ("The context", f"Show the key background and explain why {topic} matters."),
        ("The mechanism", f"Visualize how {topic} works, with clear close-up details."),
        ("The future", f"Show realistic implications and end with a memorable wide shot about {topic}."),
    ]
    return [{"title": title, "scene": scene, "narration": ""} for title, scene in beats]


def save_script_package(topic: str, scenes: list[dict[str, str]], target: str | Path) -> Path:
    import json
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "topic": topic,
        "target_duration_seconds": 60,
        "clip_duration_seconds": 15,
        "language": {"narration": "English", "subtitles": "Persian"},
        "scenes": scenes,
        "editorial_note": "Replace empty narration with fact-checked English lines and Persian subtitle translations before production.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
