"""Deterministic long-form documentary production planning.

This module creates a production blueprint only. It does not generate narration,
media, or uploads, and therefore cannot consume provider credits.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

CHAPTERS = (
    ("Opening hook", 0.06),
    ("Why this matters", 0.12),
    ("Background and history", 0.16),
    ("How it works", 0.20),
    ("Evidence and real-world examples", 0.20),
    ("Risks, limits and counterarguments", 0.14),
    ("What happens next", 0.08),
    ("Conclusion", 0.04),
)


def build_documentary_plan(topic: str, minutes: int = 15,
                           clip_seconds: int = 12) -> dict[str, Any]:
    clean_topic = topic.strip()
    if not clean_topic:
        raise ValueError("topic is required")
    if minutes not in (15, 30, 60):
        raise ValueError("minutes must be one of 15, 30, or 60")
    if clip_seconds not in (4, 6, 8, 10, 12):
        raise ValueError("clip_seconds must be 4, 6, 8, 10, or 12")

    total_seconds = minutes * 60
    total_words = minutes * 135
    chapters = []
    cursor = 0
    for index, (name, share) in enumerate(CHAPTERS, start=1):
        duration = (total_seconds - cursor if index == len(CHAPTERS)
                    else round(total_seconds * share / 5) * 5)
        duration = max(5, duration)
        words = round(total_words * duration / total_seconds)
        chapters.append({
            "chapter": index,
            "title": name,
            "start_seconds": cursor,
            "end_seconds": cursor + duration,
            "duration_seconds": duration,
            "target_narration_words": words,
            "research_requirements": [
                "At least two credible sources; prioritize primary sources.",
                "Record publication date, author or organization, and source URL.",
                "Separate established facts, estimates, and forecasts.",
            ],
            "script_status": "not_written",
            "fact_check_status": "not_checked",
        })
        cursor += duration

    shots = []
    global_shot = 0
    for chapter in chapters:
        local_start = 0
        chapter_shot = 0
        while local_start < chapter["duration_seconds"]:
            global_shot += 1
            chapter_shot += 1
            duration = min(clip_seconds, chapter["duration_seconds"] - local_start)
            start_seconds = chapter["start_seconds"] + local_start
            shots.append({
                "shot": global_shot,
                "chapter_shot": chapter_shot,
                "start_seconds": start_seconds,
                "duration_seconds": duration,
                "chapter": chapter["chapter"],
                "visual_brief": "",
                "generation_status": "not_started",
                "asset_path": None,
                "source_or_license": None,
            })
            local_start += duration
    shot_count = len(shots)

    return {
        "topic": clean_topic,
        "target_duration_seconds": total_seconds,
        "target_duration_minutes": minutes,
        "format": "16:9",
        "resolution_target": "1920x1080",
        "frame_rate_target": 30,
        "narration_language": "English",
        "subtitle_language": "Persian",
        "target_narration_words": total_words,
        "estimated_narration_words_per_minute": 135,
        "visual_clip_target_seconds": clip_seconds,
        "required_visual_slots": shot_count,
        "chapters": chapters,
        "shots": shots,
        "quality_gates": [
            "Research sources reviewed and claim ledger completed",
            "English narration drafted and fact-checked",
            "Persian translation reviewed and timed",
            "Visual rights and provenance recorded for every asset",
            "Narration and visual timeline synchronized",
            "Audio, subtitle, resolution and duration checks passed",
            "Human review completed before upload",
        ],
        "pipeline_status": "blueprint_only",
        "warning": "This plan does not generate scripts, media, or uploads.",
    }


def save_documentary_plan(plan: dict[str, Any], target: str | Path) -> Path:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
