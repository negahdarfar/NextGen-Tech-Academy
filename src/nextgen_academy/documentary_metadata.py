"""Create a source- and rights-aware YouTube metadata draft for long documentaries."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .documentary_state import load_run_state


def _timecode(seconds: float) -> str:
    value = max(0, int(seconds))
    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def build_documentary_metadata(
    state_path: str | Path,
    output_path: str | Path,
    chapter_timeline: list[dict[str, Any]],
) -> Path:
    """Write editable title, description, chapters, tags, credits and thumbnail brief."""
    state = load_run_state(state_path)
    topic = str(state.get("topic", "")).strip()
    if not topic:
        raise ValueError("Documentary topic is missing from the run state.")
    if len(chapter_timeline) != len(state["chapters"]):
        raise ValueError("Measured chapter timeline does not match the run manifest.")

    sources: dict[str, dict[str, str]] = {}
    pexels_credits: dict[tuple[str, str], dict[str, str]] = {}
    providers: set[str] = set()
    for chapter in state["chapters"]:
        outputs = chapter.get("outputs", {})
        script_path = outputs.get("script")
        if script_path and Path(script_path).is_file():
            script = json.loads(Path(script_path).read_text(encoding="utf-8"))
            for source in script.get("sources", []):
                url = str(source.get("url", "")).strip()
                if url.startswith("https://"):
                    sources[url] = {
                        "publisher": str(source.get("publisher", "Source")),
                        "title": str(source.get("title", "Untitled source")),
                        "url": url,
                    }
        visual_path = outputs.get("visual_manifest")
        if visual_path and Path(visual_path).is_file():
            manifest = json.loads(Path(visual_path).read_text(encoding="utf-8"))
            for shot in manifest.get("shots", []):
                provider = str(shot.get("provider", "unknown"))
                providers.add(provider)
                if provider == "pexels":
                    photographer = str(shot.get("photographer", "")).strip()
                    url = str(shot.get("source_url", "")).strip()
                    if photographer and url.startswith("https://"):
                        pexels_credits[(photographer, url)] = {
                            "provider": "Pexels",
                            "photographer": photographer,
                            "source_url": url,
                        }

    minutes = int(round(float(state.get("target_duration_seconds", 0)) / 60))
    title = f"{topic}: Full Documentary ({minutes}-Minute Deep Dive)"
    title = title[:100]
    chapters = [
        {
            "chapter": int(item["chapter"]),
            "time": _timecode(float(item["start_seconds"])),
            "title": str(item["title"]),
        }
        for item in chapter_timeline
    ]
    tags = []
    for token in re.findall(r"[A-Za-z0-9]+", topic.lower()):
        if len(token) > 1 and token not in tags:
            tags.append(token[:30])
    for token in ("documentary", "technology", "science", "explained", "education", "research"):
        if token not in tags:
            tags.append(token)
    tags = tags[:20]
    while sum(len(tag) for tag in tags) + max(0, len(tags) - 1) > 450:
        tags.pop()

    source_lines = [
        f"- {item['publisher']}: {item['title']} — {item['url']}"
        for item in list(sources.values())[:30]
    ]
    credit_lines = [
        f"- Pexels footage: {item['photographer']} — {item['source_url']}"
        for item in pexels_credits.values()
    ]
    if "agnes" in providers:
        credit_lines.append("- Some visuals are AI-generated with Agnes AI Video 2.5 Flash.")
    chapter_lines = [f"{item['time']} {item['title']}" for item in chapters]
    description_parts = [
        f"{topic} — a {minutes}-minute documentary with English narration and Persian subtitles.",
        "This episode explores the background, mechanisms, evidence, limitations and possible future developments.",
        "CHAPTERS\n" + "\n".join(chapter_lines),
        "RESEARCH SOURCES (discovery leads; verify before publication)\n"
        + ("\n".join(source_lines) if source_lines else "No source links were recovered from the saved scripts."),
        "VISUAL CREDITS\n" + ("\n".join(credit_lines) if credit_lines else "No third-party stock footage credits recorded."),
    ]
    description = "\n\n".join(description_parts)[:4900]
    payload = {
        "topic": topic,
        "recommended_title": title,
        "title_options": [
            title,
            f"What You Need to Know About {topic}"[:100],
            f"{topic}: Evidence, Risks and What Comes Next"[:100],
        ],
        "description": description,
        "tags": tags,
        "chapters": chapters,
        "thumbnail_prompt": (
            f"Create a high-contrast 16:9 YouTube documentary thumbnail about {topic}. "
            "One clear central subject, cinematic but credible lighting, strong focal hierarchy, "
            "minimal short English title text, accurate visual context, no fake logos, no misleading claims."
        ),
        "research_sources": list(sources.values()),
        "visual_credits": list(pexels_credits.values()),
        "visual_providers_used": sorted(providers),
        "publication_checks": [
            "Open and verify every cited source; discovery feeds are not fact-checking.",
            "Check every factual claim, statistic, date and quotation against the original source.",
            "Confirm the TTS voice/provider permits commercial YouTube use.",
            "Verify stock footage and AI-provider commercial-use terms and keep the asset provenance ledger.",
            "Review the AI/synthetic-content disclosure setting required by YouTube for this specific video.",
            "Watch the complete video and check narration, chapter boundaries and Persian subtitle timing.",
            "Confirm title and thumbnail are accurate and not misleading.",
        ],
        "requires_human_review": True,
        "upload_performed": False,
        "note": "SEO metadata is an editable draft; ranking or views are not guaranteed.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target
