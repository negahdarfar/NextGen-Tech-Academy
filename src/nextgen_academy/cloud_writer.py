"""Draft a bilingual four-scene script from discovered source leads."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm import generate_json


SYSTEM_PROMPT = """You are a careful technology documentary writer. Return JSON only.
Schema: {"scenes":[{"title":"...","scene":"...","narration_en":"...","subtitle_fa":"..."}],
"claims":[{"text":"specific factual claim","source_ids":["src1"]}]}
Write exactly four scenes for a 60-second 16:9 video. Each English narration should be 22-30 spoken words.
Persian subtitles must faithfully translate the narration. Beats: hook, context, how it works, implications.
Use only information supported by the provided source titles and summaries. Do not invent numbers,
dates, quotes, studies, or details missing from the source notes. If the sources are insufficient,
use cautious framing and explicitly say what remains uncertain. Every factual claim must reference
one or more supplied source IDs. The sources are discovery leads, not independently verified evidence."""


def draft_cloud_storyboard(topic: str, sources: list[dict[str, Any]],
                           output_path: str | Path) -> Path:
    if not topic.strip() or len(sources) < 2:
        raise ValueError("A topic and at least two discovered source leads are required.")
    source_notes = [{"id": s["id"], "title": s["title"], "publisher": s["publisher"],
                     "url": s["url"], "published": s.get("published", ""),
                     "summary": s.get("summary", "")[:1000]} for s in sources]
    user_prompt = ("Create the four-scene bilingual script for this topic: " + topic +
                   "\nUse these source notes only:\n" +
                   json.dumps(source_notes, ensure_ascii=False))
    data = generate_json(SYSTEM_PROMPT, user_prompt)
    scenes, claims = data.get("scenes"), data.get("claims")
    if not isinstance(scenes, list) or len(scenes) != 4:
        raise ValueError("Cloud model must return exactly four scenes.")
    source_ids = {s["id"] for s in sources}
    if not isinstance(claims, list):
        raise ValueError("Cloud model must return a claims array.")
    for i, scene in enumerate(scenes, 1):
        for key in ("title", "scene", "narration_en", "subtitle_fa"):
            if not str(scene.get(key, "")).strip():
                raise ValueError(f"Scene {i} is missing {key}.")
        words = len(str(scene["narration_en"]).split())
        if not 18 <= words <= 38:
            raise ValueError(f"Scene {i} narration is {words} words; expected 18-38.")
    for claim in claims:
        refs = claim.get("source_ids", [])
        if not refs or not set(refs).issubset(source_ids):
            raise ValueError("A factual claim refers to missing or invalid source IDs.")
    payload = {
        "topic": topic, "target_duration_seconds": 60, "clip_duration_seconds": 15,
        "language": {"narration": "English", "subtitles": "Persian"},
        "scenes": scenes, "sources": sources, "claims": claims,
        "editorial_note": "Cloud-generated draft. RSS discovery is not source verification; review sources and claims before public release.",
        "automation": {"llm": "cloud-fallback", "human_review_required_for_public": True}
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
