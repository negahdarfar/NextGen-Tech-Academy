"""Plan-only workflow; no network calls or media generation occur here."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProductionPlan:
    topic: str
    audience: str
    format: str
    narration_language: str
    subtitle_language: str
    stages: tuple[str, ...]


def build_plan(topic: str, audience: str = "curious general audience") -> ProductionPlan:
    clean_topic = topic.strip()
    if not clean_topic:
        raise ValueError("topic is required")

    return ProductionPlan(
        topic=clean_topic,
        audience=audience,
        format="standard long-form YouTube video",
        narration_language="English",
        subtitle_language="Persian",
        stages=(
            "Research the topic and collect primary sources",
            "Verify claims, dates, and source reliability",
            "Create an outline and English narration script",
            "Prepare Persian subtitles (SRT)",
            "Create a visual and shot plan",
            "Generate or source licensed media",
            "Assemble and render the video",
            "Run quality, factual, and copyright checks",
            "Prepare title, description, chapters, and thumbnail",
            "Request human approval before publishing",
        ),
    )


def plan_as_dict(plan: ProductionPlan) -> dict[str, object]:
    result = asdict(plan)
    result["stages"] = list(plan.stages)
    return result
