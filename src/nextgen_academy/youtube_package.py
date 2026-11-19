"""Build an editable YouTube publishing package without inventing sources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def build_youtube_package(storyboard_path: str | Path, output_path: str | Path) -> Path:
    payload = json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    topic = str(payload.get("topic", "")).strip()
    scenes = payload.get("scenes", [])
    if not topic or len(scenes) != 4:
        raise ValueError("A topic and exactly four storyboard scenes are required.")

    titles = [
        f"{topic}: The Technology Explained",
        f"How {topic} Could Change the Future",
        f"What You Need to Know About {topic}",
    ]
    chapters = [
        {"time": "00:00", "title": str(scenes[0].get("title", "The Hook"))},
        {"time": "00:15", "title": str(scenes[1].get("title", "The Context"))},
        {"time": "00:30", "title": str(scenes[2].get("title", "How It Works"))},
        {"time": "00:45", "title": str(scenes[3].get("title", "The Future"))},
    ]
    words = re.findall(r"[A-Za-z0-9]+", topic.lower())
    tags = list(dict.fromkeys(words + ["technology", "innovation", "science", "future", "explained"]))
    package: dict[str, Any] = {
        "topic": topic,
        "title_options": titles,
        "recommended_title": titles[0],
        "description_template": (
            f"Explore {topic} in this one-minute technology documentary. "
            "We break down the context, how it works, and what may come next.\n\n"
            "Research sources (add verified URLs before publishing):\n"
            "[ADD PRIMARY SOURCE 1]\n[ADD PRIMARY SOURCE 2]\n\n"
            "Subscribe for more technology explainers."
        ),
        "tags": tags[:20],
        "hashtags": ["#Technology", "#Innovation", "#Science"],
        "chapters": chapters,
        "thumbnail_prompt": (
            f"Create a clean, high-contrast 16:9 documentary thumbnail about {topic}; "
            "one central recognizable subject, cinematic lighting, strong visual hierarchy, "
            "minimal readable English text, no fake logos or misleading claims."
        ),
        "pinned_comment": f"What is the most interesting question you have about {topic}?",
        "publication_checks": [
            "Replace placeholder source URLs with verified primary sources.",
            "Confirm every factual claim and statistic in the narration.",
            "Check voice-model, music, footage and image commercial-use licenses.",
            "Review title and thumbnail for accuracy; avoid misleading claims.",
            "Watch the complete exported video and verify Persian subtitles.",
        ],
        "note": "This is an editable metadata draft, not AI keyword research or a guarantee of ranking.",
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
