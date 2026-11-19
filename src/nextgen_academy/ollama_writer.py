"""Optional local Ollama script drafting; factual review remains mandatory."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


class DraftError(RuntimeError):
    """Raised when local Ollama cannot produce a valid storyboard."""


SYSTEM_PROMPT = """You are a careful technology documentary script editor.
Return JSON only, with exactly this schema:
{"scenes":[{"title":"...","scene":"...","narration_en":"...","subtitle_fa":"..."}]}
Create exactly four scenes for a 60-second video. Each scene is designed for 15 seconds.
Write clear spoken English narration of 25 to 32 words per scene. Write a faithful,
natural Persian translation in subtitle_fa. The four beats are hook, context, mechanism,
and implications. Do not invent statistics, dates, named studies, quotations, or precise
claims. If a fact is uncertain, phrase it cautiously. This is a draft, not verified research."""


def draft_storyboard(topic: str, output_path: str | Path,
                     base_url: str = "http://127.0.0.1:11434",
                     model: str = "qwen2.5:3b", timeout: int = 180) -> Path:
    topic = topic.strip()
    if not topic:
        raise DraftError("Topic cannot be empty.")
    endpoint = base_url.rstrip("/") + "/api/chat"
    body = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Draft a one-minute technology documentary about: {topic}"},
        ],
        "options": {"temperature": 0.35},
    }
    request = Request(endpoint, data=json.dumps(body).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise DraftError(f"Could not reach local Ollama at {endpoint}: {exc}") from exc

    content = result.get("message", {}).get("content", "")
    try:
        draft = json.loads(content)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DraftError("Ollama response was not valid JSON.") from exc
    scenes = draft.get("scenes", [])
    if len(scenes) != 4:
        raise DraftError("Ollama must return exactly four scenes.")
    for i, scene in enumerate(scenes, 1):
        for field in ("title", "scene", "narration_en", "subtitle_fa"):
            if not str(scene.get(field, "")).strip():
                raise DraftError(f"Scene {i} is missing {field}.")
        words = len(str(scene["narration_en"]).split())
        if not 18 <= words <= 38:
            raise DraftError(f"Scene {i} narration has {words} words; target is 25–32.")

    payload = {
        "topic": topic,
        "target_duration_seconds": 60,
        "clip_duration_seconds": 15,
        "language": {"narration": "English", "subtitles": "Persian"},
        "scenes": scenes,
        "sources": [],
        "claims": [],
        "editorial_note": (
            "AI-generated draft only. Add manually verified HTTPS sources and map every "
            "factual claim to source_ids, then run script-check before production."
        ),
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
