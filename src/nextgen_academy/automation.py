"""End-to-end cloud automation using free Pexels stock footage."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .config import load_dotenv
from .cloud_tts import synthesize_cloud_narration
from .cloud_writer import draft_cloud_storyboard
from .pexels import download_scene_video
from .research import discover_sources
from .script import storyboard_subtitles
from .video_pipeline import render_video, validate_render_duration
from .video_segments import build_segments, segments_as_dicts
from .youtube_package import build_youtube_package
from .youtube_upload import upload_video, validate_youtube_credentials


def run_automated(topic: str = "", output_dir: str | Path = "output",
                  publish: bool = False) -> dict:
    load_dotenv()
    if not os.getenv("PEXELS_API_KEY", "").strip():
        raise RuntimeError(
            "Missing PEXELS_API_KEY. Pexels offers free stock footage via its API; "
            "add your free API key as a GitHub Actions Secret. No paid video provider is used."
        )
    if publish:
        validate_youtube_credentials()

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if not topic.strip():
        from .topic_discovery import choose_topic
        topic = choose_topic()

    sources = discover_sources(topic, limit=12)
    storyboard_path = draft_cloud_storyboard(topic, sources, root / "storyboard.json")
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    segments = build_segments(topic, [scene["scene"] for scene in scenes], duration_seconds=15)
    segment_data = segments_as_dicts(segments)
    for index, scene in enumerate(scenes):
        segment_data[index]["narration"] = scene["narration_en"]
        segment_data[index]["subtitle"] = scene["subtitle_fa"]

    (root / "video-plan.json").write_text(
        json.dumps({"topic": topic, "target_duration_seconds": 60,
                    "segments": segment_data}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    storyboard_subtitles(storyboard_path, root / "persian.srt")
    synthesize_cloud_narration(
        storyboard_path, root / "narration.wav",
        os.getenv("TTS_VOICE", "en-US-AriaNeural"),
    )

    jobs = []
    for index, segment in enumerate(segments, start=1):
        clip_path = root / "clips" / f"clip_{index:03d}.mp4"
        # Search using the scene itself rather than a generated-video prompt.
        scene_query = scenes[index - 1]["scene"]
        source = download_scene_video(scene_query, clip_path, min_duration=15)
        jobs.append({
            "index": index,
            "title": segment.title,
            "prompt": segment.prompt,
            "status": "downloaded",
            **source,
        })
    jobs_path = root / "pexels-jobs.json"
    jobs_path.write_text(
        json.dumps({"provider": "pexels", "status": "downloaded", "jobs": jobs},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    render_video(jobs_path, root / "final-video.mp4",
                 root / "persian.srt", root / "narration.wav")
    actual_duration = validate_render_duration(root / "final-video.mp4")

    package_path = build_youtube_package(storyboard_path, root / "youtube-package.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["description"] = (
        f"Explore {topic} in this one-minute technology documentary.\n\n"
        "Sources discovered for this episode (review before public release):\n"
        + "\n".join(f"- {source['publisher']}: {source['title']} — {source['url']}"
                     for source in sources[:8])
        + "\n\nStock footage provided by Pexels.\nSubscribe for more technology explainers."
    )
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "topic": topic,
        "video": str(root / "final-video.mp4"),
        "metadata": str(package_path),
        "source_count": len(sources),
        "visual_provider": "Pexels (free stock footage)",
        "render_duration_seconds": actual_duration,
        "youtube_uploaded": False,
        "privacy_status": "not_uploaded",
    }
    if publish:
        uploaded = upload_video(
            root / "final-video.mp4", package_path,
            privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private"),
        )
        result["youtube"] = uploaded
        result["youtube_uploaded"] = True
        result["privacy_status"] = uploaded["privacy_status"]
    return result
