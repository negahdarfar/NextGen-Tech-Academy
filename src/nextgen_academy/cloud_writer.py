"""Draft a bilingual long-form documentary from discovered source leads."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .llm import generate_json

SYSTEM_PROMPT = """You are a careful technology documentary writer. Return JSON only.
Schema: {"scenes":[{"title":"...","scene":"...","narration_en":"...","subtitle_fa":"...","source_ids":["src1"]}],
"claims":[{"text":"specific factual claim","source_ids":["src1"]}]}
Create exactly the requested number of sequential scenes for a 16:9 documentary.
Each scene represents 15 seconds. Keep English narration concise: aim for 22-26 spoken words,
and never exceed 30 words so the voiceover is not cut off by the scene duration.
Structure the documentary with a compelling hook, context, explanation, evidence, real-world applications,
risks/limitations, open questions and a thoughtful conclusion. Avoid repetitive filler.
Persian subtitles must faithfully translate each English narration. Every scene must include one or more
source_ids from the supplied source list; every factual claim must also cite source_ids.
Use only information supported by the supplied source titles and summaries. Do not invent numbers, dates,
quotes, studies or details. If sources are insufficient, use cautious framing and state uncertainty.
Sources are discovery leads, not independently verified evidence."""

def draft_cloud_storyboard(topic: str, sources: list[dict[str, Any]], output_path: str | Path,
                           target_duration_seconds: int = 300) -> Path:
    if not topic.strip() or len(sources) < 2:
        raise ValueError("A topic and at least two discovered source leads are required.")
    if target_duration_seconds not in range(180, 601, 60):
        raise ValueError("target_duration_seconds must be 180-600 in 60-second steps.")
    scene_count = target_duration_seconds // 15
    source_ids = {s["id"] for s in sources}
    source_notes = [{"id": s["id"], "title": s["title"], "publisher": s["publisher"],
                     "url": s["url"], "published": s.get("published", ""),
                     "summary": s.get("summary", "")[:1000]} for s in sources]
    user_prompt = (f"Create exactly {scene_count} scenes (15 seconds each, total {target_duration_seconds} seconds) "
                   f"for this documentary: {topic}\nSource notes:\n" +
                   json.dumps(source_notes, ensure_ascii=False))
    data = generate_json(SYSTEM_PROMPT, user_prompt)
    scenes, claims = data.get("scenes"), data.get("claims")
    if not isinstance(scenes, list) or len(scenes) != scene_count:
        raise ValueError(f"Cloud model must return exactly {scene_count} scenes.")
    if not isinstance(claims, list):
        raise ValueError("Cloud model must return a claims array.")
    for i, scene in enumerate(scenes, 1):
        for key in ("title", "scene", "narration_en", "subtitle_fa"):
            if not str(scene.get(key, "")).strip():
                raise ValueError(f"Scene {i} is missing {key}.")
        words = len(str(scene["narration_en"]).split())
        if not 18 <= words <= 30:
            raise ValueError(f"Scene {i} narration is {words} words; expected 18-30.")
        refs = scene.get("source_ids", [])
        if not isinstance(refs, list) or not refs or not set(refs).issubset(source_ids):
            raise ValueError(f"Scene {i} refers to missing or invalid source IDs.")
    for claim in claims:
        refs = claim.get("source_ids", [])
        if not refs or not set(refs).issubset(source_ids):
            raise ValueError("A factual claim refers to missing or invalid source IDs.")
    payload = {"topic": topic, "target_duration_seconds": target_duration_seconds,
        "clip_duration_seconds": 15, "language": {"narration": "English", "subtitles": "Persian"},
        "scenes": scenes, "sources": sources, "claims": claims,
        "editorial_note": "AI-generated draft. RSS discovery is not source verification; fact-check all claims and review the complete video before public release.",
        "automation": {"llm": "cloud-fallback", "human_review_required_for_public": True}}
    path = Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
