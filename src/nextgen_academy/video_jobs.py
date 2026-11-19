"""Create and persist a resumable manifest of VidoGrid clip jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from .video_segments import VideoSegment


class VideoProvider(Protocol):
    def submit_video(self, prompt: str) -> dict[str, Any]: ...


def submit_segments(
    segments: list[VideoSegment],
    provider: VideoProvider,
    manifest_path: str | Path,
) -> dict[str, Any]:
    """Submit clips in order and persist after every accepted job.

    Sequential submission limits accidental bursts and makes interruption
    recoverable. Re-running this function with the same manifest is not
    supported yet; inspect/resume from the saved manifest instead.
    """
    target = Path(manifest_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "provider": "vidogrid",
        "status": "submitting",
        "clip_duration_target_seconds": 15,
        "jobs": [],
    }
    _write_manifest(target, manifest)
    for segment in segments:
        response = provider.submit_video(segment.prompt)
        manifest["jobs"].append({
            "index": segment.index,
            "title": segment.title,
            "duration_target_seconds": segment.duration_seconds,
            "prompt": segment.prompt,
            "job_uuid": response["uuid"],
            "provider_response": response,
            "status": "queued",
        })
        _write_manifest(target, manifest)
    manifest["status"] = "submitted"
    _write_manifest(target, manifest)
    return manifest


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)
