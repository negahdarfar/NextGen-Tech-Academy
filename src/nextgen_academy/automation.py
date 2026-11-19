"""End-to-end automation entry point for GitHub-hosted runners."""
from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

from .cloud_tts import synthesize_cloud_narration
from .cloud_writer import draft_cloud_storyboard
from .research import discover_sources
from .script import storyboard_subtitles
from .video_jobs import submit_segments
from .video_pipeline import poll_and_download, render_video, validate_render_duration
from .video_segments import build_segments, segments_as_dicts
from .vidogrid import VidoGridClient, VidoGridSettings
from .youtube_package import build_youtube_package
from .youtube_upload import upload_video


def run_automated(topic: str = "", output_dir: str | Path = "output",
                  publish: bool = False) -> dict:
    if publish and not os.getenv("YOUTUBE_TOKEN_JSON", "").strip():
        raise RuntimeError("YOUTUBE_TOKEN_JSON is required before generation when --upload is selected.")
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

    client = VidoGridClient(VidoGridSettings.from_env())
    account = client.account()
    _require_free_credit_budget(account, clips=len(segments))
    router = _VidoGridRouter()
    jobs_path = root / "vidogrid-jobs.json"
    submit_segments(segments, router, jobs_path)
    poll_and_download(
        client, jobs_path, root / "clips",
        timeout_seconds=int(os.getenv("VIDOGRID_TIMEOUT_SECONDS", "2400")),
        poll_interval=int(os.getenv("VIDOGRID_POLL_INTERVAL", "10")),
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
        + "\n\nSubscribe for more technology explainers."
    )
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "topic": topic,
        "video": str(root / "final-video.mp4"),
        "metadata": str(package_path),
        "source_count": len(sources),
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


def _require_free_credit_budget(account: dict, clips: int) -> None:
    """Fail closed unless API reports free credits and the user configures per-clip cost."""
    free_keys = {
        "free_credits", "free_balance", "bonus_credits",
        "trial_credits", "promotional_credits",
    }
    balances: list[float] = []

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in free_keys and isinstance(item, (int, float)):
                    balances.append(float(item))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(account)
    if not balances:
        raise RuntimeError(
            "VidoGrid did not expose a separate free/trial credit balance. "
            "No video jobs were submitted to avoid paid usage."
        )
    try:
        per_clip = float(os.environ["VIDOGRID_CREDITS_PER_CLIP"])
    except (KeyError, ValueError) as exc:
        raise RuntimeError(
            "Set VIDOGRID_CREDITS_PER_CLIP from current VidoGrid pricing for the selected models."
        ) from exc
    if per_clip <= 0:
        raise RuntimeError("VIDOGRID_CREDITS_PER_CLIP must be greater than zero.")
    required = per_clip * clips
    available = min(balances)
    if available < required:
        raise RuntimeError(
            f"Insufficient free VidoGrid credits: available={available}, "
            f"estimated_required={required}. No jobs were submitted."
        )


class _VidoGridRouter:
    """Select a configured VidoGrid model for each sequential clip."""
    def __init__(self):
        self.models = [
            model.strip() for model in os.getenv(
                "VIDOGRID_MODEL_ROTATION",
                "grok-imagine-video-1.5-lite,grok-imagine-video-1.5",
            ).split(",") if model.strip()
        ]
        if not self.models:
            raise RuntimeError("VIDOGRID_MODEL_ROTATION must contain at least one model.")
        unsupported = set(self.models) - {
            "grok-imagine-video-1.5-lite", "grok-imagine-video-1.5",
        }
        if unsupported:
            raise RuntimeError(f"Unsupported VidoGrid video model(s): {sorted(unsupported)}")
        self.index = 0
        self.clients = {}
        base = VidoGridSettings.from_env()
        for model in self.models:
            endpoint = (
                "/video-gen/grok-imagine-video-1.5-lite"
                if model == "grok-imagine-video-1.5-lite"
                else "/video-gen/grok-imagine-video-1.5"
            )
            self.clients[model] = VidoGridClient(replace(base, endpoint=endpoint, model=model))

    def submit_video(self, prompt: str) -> dict:
        model = self.models[self.index % len(self.models)]
        self.index += 1
        result = self.clients[model].submit_video(prompt)
        result["selected_model"] = model
        return result
