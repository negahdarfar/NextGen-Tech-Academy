"""Plan chained short clips for a coherent long-form video."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VideoSegment:
    index: int
    duration_seconds: int
    title: str
    narration: str
    prompt: str
    continuity_in: str
    continuity_out: str
    subtitle: str = ""


def build_segments(
    topic: str,
    scenes: list[str],
    visual_style: str = "cinematic documentary, realistic detail, natural motion",
    duration_seconds: int = 15,
) -> list[VideoSegment]:
    """Build prompt-linked clips from an ordered scene list.

    Scene descriptions should be authored from the approved script/storyboard.
    The provider may impose model-specific duration limits; duration_seconds is
    a planning target, not a guarantee that every model renders that duration.
    """
    clean_topic = topic.strip()
    clean_scenes = [scene.strip() for scene in scenes if scene.strip()]
    if not clean_topic:
        raise ValueError("topic is required")
    if not clean_scenes:
        raise ValueError("at least one scene is required")
    if not 1 <= duration_seconds <= 15:
        raise ValueError("duration_seconds must be between 1 and 15")

    segments: list[VideoSegment] = []
    for index, scene in enumerate(clean_scenes, start=1):
        continuity_in = (
            "Opening shot: establish the visual world consistently."
            if index == 1
            else f"Continue directly from clip {index - 1}; preserve the same subjects, "
                 "wardrobe, location, lighting, color grade, and camera language."
        )
        continuity_out = (
            "End with a clear visual composition that can lead into the next shot."
            if index < len(clean_scenes)
            else "End on a stable, intentional closing composition."
        )
        prompt = (
            f"Create a {duration_seconds}-second 16:9 documentary video clip about: "
            f"{clean_topic}. Scene {index}: {scene}. "
            f"Visual bible: {visual_style}. {continuity_in} {continuity_out} "
            "Use natural movement, coherent physics, no captions, no logos, "
            "no watermarks, and no sudden style changes."
        )
        segments.append(
            VideoSegment(
                index=index,
                duration_seconds=duration_seconds,
                title=f"Scene {index:03d}",
                narration="",
                prompt=prompt,
                continuity_in=continuity_in,
                continuity_out=continuity_out,
            )
        )
    return segments


def segments_as_dicts(segments: list[VideoSegment]) -> list[dict[str, object]]:
    return [asdict(segment) for segment in segments]
