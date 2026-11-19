"""Utilities for one-minute documentary storyboards and subtitle files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_storyboard(topic: str) -> list[dict[str, str]]:
    topic = topic.strip()
    if not topic:
        raise ValueError("topic is required")
    beats = [
        ("The hook", f"Open with a striking real-world visual that introduces {topic}."),
        ("The context", f"Show the key background and explain why {topic} matters."),
        ("The mechanism", f"Visualize how {topic} works, with clear close-up details."),
        ("The future", f"Show realistic implications and end with a memorable wide shot about {topic}."),
    ]
    return [{"title": title, "scene": scene, "narration_en": "", "subtitle_fa": ""}
            for title, scene in beats]


def save_script_package(topic: str, scenes: list[dict[str, str]], target: str | Path) -> Path:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "topic": topic,
        "target_duration_seconds": 60,
        "clip_duration_seconds": 15,
        "language": {"narration": "English", "subtitles": "Persian"},
        "scenes": scenes,
        "editorial_note": "Write and fact-check narration_en, then provide a faithful Persian translation in subtitle_fa. Each scene is targeted at 15 seconds.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def storyboard_subtitles(storyboard_path: str | Path, target: str | Path) -> Path:
    payload = json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    scenes = payload.get("scenes", [])
    if len(scenes) != 4:
        raise ValueError("The one-minute preset requires exactly four scenes.")
    rows = []
    for index, scene in enumerate(scenes):
        text = str(scene.get("subtitle_fa", "")).strip()
        if not text:
            raise ValueError(f"Scene {index + 1}: subtitle_fa is empty.")
        start, end = _stamp(index * 15), _stamp((index + 1) * 15)
        rows.append(f"{index + 1}\n{start} --> {end}\n{text}\n")
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows), encoding="utf-8-sig")
    return path


def _stamp(seconds: int) -> str:
    return f"00:00:{seconds:02d},000"
