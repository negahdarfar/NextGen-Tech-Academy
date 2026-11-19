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
    """Submit clips in order, skipping UUIDs already saved in the manifest."""
    target = Path(manifest_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        manifest = json.loads(target.read_text(encoding="utf-8"))
        if manifest.get("provider") != "vidogrid":
            raise ValueError("manifest provider does not match VidoGrid")
        existing = {int(job["index"]): job for job in manifest.get("jobs", [])}
        expected = {segment.index: segment.prompt for segment in segments}
        for index, job in existing.items():
            if index not in expected or job.get("prompt") != expected[index]:
                raise ValueError(
                    "existing manifest does not match this storyboard; "
                    "use a new manifest path"
                )
    else:
        manifest = {
            "provider": "vidogrid",
            "status": "submitting",
            "clip_duration_target_seconds": segments[0].duration_seconds if segments else 15,\n            "target_duration_seconds": sum(segment.duration_seconds for segment in segments),
            "jobs": [],
        }
        existing = {}

    manifest["status"] = "submitting"
    _write_manifest(target, manifest)

    for segment in segments:
        if segment.index in existing and existing[segment.index].get("job_uuid"):
            continue
        response = provider.submit_video(segment.prompt)
        job = {
            "index": segment.index,
            "title": segment.title,
            "duration_target_seconds": segment.duration_seconds,
            "prompt": segment.prompt,
            "job_uuid": response["uuid"],
            "provider_response": response,
            "status": "queued",
        }
        manifest["jobs"] = [
            item for item in manifest["jobs"] if int(item["index"]) != segment.index
        ]
        manifest["jobs"].append(job)
        manifest["jobs"].sort(key=lambda item: int(item["index"]))
        existing[segment.index] = job
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
