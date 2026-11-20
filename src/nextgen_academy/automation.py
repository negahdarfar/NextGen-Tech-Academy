"""End-to-end zero-budget cloud automation with explicitly opt-in paid video provider."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .config import load_dotenv
from .agnes_video import generate_scene_video
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
    agnes_key = os.getenv("AGNES_API_KEY", "").strip()
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    allow_agnes = os.getenv("ALLOW_AGNES_POTENTIAL_COST", "false").lower() == "true"
    if not pexels_key and not (agnes_key and allow_agnes):
        raise RuntimeError(
            "Zero-budget mode requires PEXELS_API_KEY. Agnes is never called unless "
            "ALLOW_AGNES_POTENTIAL_COST=true is explicitly set."
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
                    "segments": segment_data}, ensure_ascii=False, indent=2), encoding="utf-8")
    storyboard_subtitles(storyboard_path, root / "persian.srt")
    synthesize_cloud_narration(storyboard_path, root / "narration.wav",
                               os.getenv("TTS_VOICE", "en-US-AriaNeural"))

    jobs, providers_used = [], []
    for index, segment in enumerate(segments, start=1):
        clip_path = root / "clips" / f"clip_{index:03d}.mp4"
        scene = scenes[index - 1]
        source = None
        if agnes_key and allow_agnes:
            try:
                source = generate_scene_video(segment.prompt, clip_path, seconds=12)
            except Exception as exc:
                if not pexels_key:
                    raise RuntimeError(f"Opt-in Agnes generation failed for scene {index}: {exc}") from exc
                print(f"Agnes scene {index} failed; falling back to Pexels: {exc}")
        if source is None:
            source = download_scene_video(scene["scene"], clip_path, min_duration=15)
            source["provider"] = "pexels"
        providers_used.append(source["provider"])
        jobs.append({"index": index, "title": segment.title,
                     "duration_target_seconds": segment.duration_seconds,
                     "prompt": segment.prompt, "status": "downloaded", **source})

    jobs_path = root / "video-jobs.json"
    jobs_path.write_text(json.dumps({"provider": "hybrid", "providers_used": providers_used,
                                     "status": "downloaded", "jobs": jobs},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    render_video(jobs_path, root / "final-video.mp4", root / "persian.srt", root / "narration.wav")
    actual_duration = validate_render_duration(root / "final-video.mp4")

    package_path = build_youtube_package(storyboard_path, root / "youtube-package.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    credits = [f"- Pexels footage: {job.get('source_url', '')} (photographer: {job.get('photographer', 'unknown')})"
               for job in jobs if job.get("provider") == "pexels"]
    package["description"] = (
        f"Explore {topic} in this one-minute technology documentary.\n\n"
        "Sources discovered for this episode (verify before monetization):\n"
        + "\n".join(f"- {s['publisher']}: {s['title']} — {s['url']}" for s in sources[:8])
        + ("\n\nAI-generated scenes: Agnes AI Video 2.5 Flash.\n" if "agnes" in providers_used
           else "\n\nVisuals: Pexels stock footage.\n")
        + "\n".join(credits) + "\n\nSubscribe for more technology explainers."
    )
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {"topic": topic, "video": str(root / "final-video.mp4"),
              "metadata": str(package_path), "source_count": len(sources),
              "visual_providers_used": providers_used, "render_duration_seconds": actual_duration,
              "youtube_uploaded": False, "privacy_status": "not_uploaded"}
    if publish:
        uploaded = upload_video(root / "final-video.mp4", package_path,
                                privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private"))
        result.update({"youtube": uploaded, "youtube_uploaded": True,
                       "privacy_status": uploaded["privacy_status"]})
    return result
