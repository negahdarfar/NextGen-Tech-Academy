"""End-to-end automation entry point for GitHub-hosted runners."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .cloud_tts import synthesize_cloud_narration
from .cloud_writer import draft_cloud_storyboard
from .research import discover_sources
from .script import storyboard_subtitles
from .video_jobs import submit_segments
from .video_pipeline import poll_and_download, render_video
from .video_segments import build_segments, segments_as_dicts
from .vidogrid import VidoGridClient, VidoGridSettings
from .youtube_package import build_youtube_package
from .youtube_upload import upload_video


def run_automated(topic: str = "", output_dir: str | Path = "output",
                  publish: bool = False) -> dict:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if not topic.strip():
        from .topic_discovery import choose_topic
        topic = choose_topic()
    sources = discover_sources(topic, limit=12)
    storyboard_path = draft_cloud_storyboard(topic, sources, root / "storyboard.json")
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    segments = build_segments(topic, [s["scene"] for s in scenes], duration_seconds=15)
    segment_data = segments_as_dicts(segments)
    for i, scene in enumerate(scenes):
        segment_data[i]["narration"] = scene["narration_en"]
        segment_data[i]["subtitle"] = scene["subtitle_fa"]
    plan_path = root / "video-plan.json"
    plan_path.write_text(json.dumps({"topic": topic, "target_duration_seconds": 60,
                                     "segments": segment_data}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    storyboard_subtitles(storyboard_path, root / "persian.srt")
    synthesize_cloud_narration(storyboard_path, root / "narration.wav",
                               os.getenv("TTS_VOICE", "en-US-AriaNeural"))
    client = VidoGridClient(VidoGridSettings.from_env())
    account = client.account()
    print("VidoGrid account response:", json.dumps(account, ensure_ascii=False)[:1500])
    router = _VidoGridRouter()
    jobs_path = root / "vidogrid-jobs.json"
    submit_segments(segments, router, jobs_path)
    poll_and_download(client, jobs_path, root / "clips",
                      timeout_seconds=int(os.getenv("VIDOGRID_TIMEOUT_SECONDS", "2400")),
                      poll_interval=int(os.getenv("VIDOGRID_POLL_INTERVAL", "10")))
    render_video(jobs_path, root / "final-video.mp4",
                 root / "persian.srt", root / "narration.wav")
    package_path = build_youtube_package(storyboard_path, root / "youtube-package.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["description"] = (
        f"Explore {topic} in this one-minute technology documentary.\n\n"
        "Sources discovered for this episode (review before public release):\n" +
        "\n".join(f"- {s['publisher']}: {s['title']} — {s['url']}" for s in sources[:8]) +
        "\n\nSubscribe for more technology explainers."
    )
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"topic": topic, "video": str(root / "final-video.mp4"),
              "metadata": str(package_path), "source_count": len(sources),
              "public_publish_enabled": publish}
    if publish:
        result["youtube"] = upload_video(root / "final-video.mp4", package_path,
                                         privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private"))
    return result


class _VidoGridRouter:
    """Select a configured model for each clip while preserving ordered job manifests."""
    def __init__(self):
        self.models = [m.strip() for m in os.getenv(
            "VIDOGRID_MODEL_ROTATION", "grok-imagine-video-1.5-lite,grok-imagine-video-1.5"
        ).split(",") if m.strip()]
        self.index = 0
        self.clients = {}
        for model in self.models:
            endpoint = ("/video-gen/grok-imagine-video-1.5-lite"
                        if model == "grok-imagine-video-1.5-lite"
                        else "/video-gen/grok-imagine-video-1.5")
            base = VidoGridSettings.from_env()
            from dataclasses import replace
            self.clients[model] = VidoGridClient(replace(base, endpoint=endpoint, model=model))

    def submit_video(self, prompt: str) -> dict:
        model = self.models[self.index % len(self.models)]
        self.index += 1
        result = self.clients[model].submit_video(prompt)
        result["selected_model"] = model
        return result
