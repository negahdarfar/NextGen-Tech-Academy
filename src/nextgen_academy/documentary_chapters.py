"""Chapter-at-a-time research and bilingual script drafting for long documentaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .documentary_state import STAGES, load_run_state, update_chapter_state
from .llm import generate_json
from .research import discover_sources

SYSTEM_PROMPT = """You are a rigorous long-form technology documentary writer.
Return one JSON object with exactly these keys:
{"narration_en":"...","subtitle_fa":"...","claims":[{"text":"...","source_ids":["src1"]}]}
Write a coherent documentary chapter, not a short summary. Aim for the requested spoken-word count.
The English narration must be natural voiceover prose. The Persian text must faithfully translate
the complete English narration, not summarize it. Do not invent facts, numbers, dates, quotations,
or study findings. Every verifiable factual claim must cite one or more supplied source IDs.
Sources are discovery leads, not independently verified evidence. Clearly qualify uncertainty.
Do not include headings, markdown fences, or production directions in narration."""


def process_documentary_chapter(state_path: str | Path, chapter_number: int,
                                output_dir: str | Path = "output/documentary",
                                force: bool = False) -> dict[str, Any]:
    """Research and draft one chapter; saved chapters are skipped unless force is explicit."""
    state = load_run_state(state_path)
    chapter = next((item for item in state["chapters"]
                    if item["chapter"] == chapter_number), None)
    if chapter is None:
        raise ValueError(f"Unknown chapter number: {chapter_number}")
    current = chapter["status"]
    if current in ("scripted", "narrated", "assembled", "reviewed") and not force:
        return {"chapter": chapter_number, "status": current, "skipped": True,
                "reason": "Chapter already has a saved script."}
    if current not in ("planned", "researched") and not force:
        raise ValueError(f"Chapter status {current!r} cannot be processed here.")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    stem = f"chapter-{chapter_number:02d}"
    research_path = root / f"{stem}-research.json"
    script_path = root / f"{stem}-script.json"

    if current == "planned" or force:
        topic_query = f"{state['topic']} — {chapter['title']}"
        sources = discover_sources(topic_query, limit=12)
        if len(sources) < 2:
            raise RuntimeError("At least two source leads are required before drafting a chapter.")
        research_payload = {
            "topic": state["topic"], "chapter": chapter_number,
            "chapter_title": chapter["title"], "query": topic_query,
            "sources": sources,
            "verification_note": "RSS discovery leads only; sources and claims require human verification.",
        }
        _write_json(research_path, research_payload)
        update_chapter_state(state_path, chapter_number, status="researched",
                             outputs={"research": str(research_path)})
    else:
        research_payload = json.loads(research_path.read_text(encoding="utf-8"))
        sources = research_payload["sources"]

    source_notes = [
        {"id": item["id"], "title": item["title"], "publisher": item["publisher"],
         "url": item["url"], "published": item.get("published", ""),
         "summary": item.get("summary", "")[:1200]}
        for item in sources
    ]
    words = int(chapter["target_narration_words"])
    user_prompt = (
        f"Documentary topic: {state['topic']}\n"
        f"Chapter {chapter_number}: {chapter['title']}\n"
        f"Target duration: {chapter['duration_seconds']} seconds.\n"
        f"Target English narration: approximately {words} words (acceptable range "
        f"{max(50, int(words * 0.8))}–{int(words * 1.2)} words).\n"
        "Write this chapter as part of one continuous documentary. Avoid repeating a generic "
        "introduction or conclusion unless this is the opening or final chapter.\n"
        "Source notes (use only these for factual claims):\n"
        + json.dumps(source_notes, ensure_ascii=False)
    )
    data = generate_json(SYSTEM_PROMPT, user_prompt)
    narration = str(data.get("narration_en", "")).strip()
    translation = str(data.get("subtitle_fa", "")).strip()
    claims = data.get("claims")
    if not narration or not translation or not isinstance(claims, list):
        raise ValueError("Model output must include narration_en, subtitle_fa and claims.")
    word_count = len(narration.split())
    if not max(50, int(words * 0.65)) <= word_count <= int(words * 1.35):
        raise ValueError(f"Chapter narration has {word_count} words; target is about {words}.")
    source_ids = {item["id"] for item in sources}
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("Each claim must be an object.")
        refs = claim.get("source_ids")
        if not isinstance(refs, list) or not refs or not set(refs).issubset(source_ids):
            raise ValueError("A factual claim refers to missing or invalid source IDs.")

    payload = {
        "topic": state["topic"], "chapter": chapter_number,
        "title": chapter["title"], "duration_seconds": chapter["duration_seconds"],
        "target_narration_words": words, "actual_narration_words": word_count,
        "narration_en": narration, "subtitle_fa": translation,
        "claims": claims, "sources": sources,
        "review_required": True,
    }
    _write_json(script_path, payload)
    update_chapter_state(state_path, chapter_number, status="scripted",
                         outputs={"script": str(script_path)})
    return {"chapter": chapter_number, "status": "scripted", "skipped": False,
            "research_path": str(research_path), "script_path": str(script_path),
            "word_count": word_count, "source_count": len(sources)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
