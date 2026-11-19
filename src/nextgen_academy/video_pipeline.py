"""Poll VidoGrid jobs, download clips, and assemble a one-minute MP4."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from ipaddress import ip_address


class PipelineError(RuntimeError):
    """Raised when a provider job or local media operation fails."""


def _walk_urls(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"url", "video_url", "download_url"} and isinstance(item, str):
                yield item
            yield from _walk_urls(item)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.startswith("https://"):
                yield item
            else:
                yield from _walk_urls(item)


def extract_video_url(payload: dict[str, Any]) -> str:
    """Find a likely video URL in provider history payloads."""
    candidates = list(dict.fromkeys(_walk_urls(payload)))
    for candidate in candidates:
        parsed = urlparse(candidate)
        if parsed.scheme == "https" and parsed.hostname and (
            parsed.path.lower().endswith((".mp4", ".mov", ".webm"))
            or "video" in parsed.path.lower()
            or "download" in parsed.path.lower()
        ):
            try:
                ip = ip_address(parsed.hostname)
                if not ip.is_global:
                    continue
            except ValueError:
                if parsed.hostname in {"localhost"} or parsed.hostname.endswith(".local"):
                    continue
            return candidate
    raise PipelineError("No HTTPS video download URL found in VidoGrid history response")


def _status(payload: dict[str, Any]) -> str:
    for key in ("status", "state", "generation_status"):
        value = payload.get(key)
        if isinstance(value, str):
            return value.lower()
    for nested in payload.values():
        if isinstance(nested, dict):
            value = _status(nested)
            if value:
                return value
    return ""


def poll_and_download(client, jobs_manifest: str | Path, output_dir: str | Path,
                      timeout_seconds: int = 1800, poll_interval: int = 8) -> dict[str, Any]:
    """Poll queued UUIDs, persist each result, and download finished clips."""
    manifest_path = Path(jobs_manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds

    for job in manifest.get("jobs", []):
        clip_path = destination / f"clip_{int(job['index']):03d}.mp4"
        if clip_path.is_file() and clip_path.stat().st_size > 1024:
            job["status"] = "downloaded"
            job["local_path"] = str(clip_path)
            continue
        while time.monotonic() < deadline:
            payload = client.history(str(job["job_uuid"]))
            state = _status(payload)
            job["last_provider_response"] = payload
            job["status"] = state or "unknown"
            if state in {"failed", "error", "cancelled", "canceled"}:
                raise PipelineError(f"VidoGrid job {job['job_uuid']} failed: {payload}")
            if state in {"done", "completed", "complete", "success", "succeeded", "finished"}:
                url = extract_video_url(payload)
                _download(url, clip_path)
                job["status"] = "downloaded"
                job["download_url_host"] = urlparse(url).hostname
                job["local_path"] = str(clip_path)
                break
            _save(manifest_path, manifest)
            time.sleep(max(3, poll_interval))
        else:
            _save(manifest_path, manifest)
            raise TimeoutError(f"Timed out waiting for VidoGrid job {job['job_uuid']}")
        _save(manifest_path, manifest)

    manifest["status"] = "downloaded"
    _save(manifest_path, manifest)
    return manifest


def _download(url: str, target: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise PipelineError("Refusing non-HTTPS or malformed video URL")
    try:
        ip = ip_address(parsed.hostname)
        if not ip.is_global:
            raise PipelineError("Refusing a non-public download host")
    except ValueError:
        if parsed.hostname == "localhost" or parsed.hostname.endswith(".local"):
            raise PipelineError("Refusing a local download host")
    request = Request(url, headers={"User-Agent": "NextGen-Tech-Academy/0.1"})
    temporary = target.with_suffix(target.suffix + ".part")
    try:
        with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type and not (content_type.startswith("video/") or "octet-stream" in content_type):
                raise PipelineError(f"Unexpected video content type: {content_type}")
            shutil.copyfileobj(response, output)
        if temporary.stat().st_size < 1024:
            raise PipelineError("Downloaded video is unexpectedly small")
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()


def render_video(jobs_manifest: str | Path, output_file: str | Path,
                 subtitles: str | Path | None = None,
                 narration_audio: str | Path | None = None) -> Path:
    """Normalize and concatenate clips with FFmpeg; optionally mux narration/subtitles."""
    manifest = json.loads(Path(jobs_manifest).read_text(encoding="utf-8"))
    jobs = sorted(manifest.get("jobs", []), key=lambda item: int(item["index"]))
    if not jobs:
        raise PipelineError("No clips are present in the jobs manifest")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PipelineError("FFmpeg was not found. Install FFmpeg and add it to PATH.")
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    work = output.parent / (output.stem + "_normalized")
    work.mkdir(parents=True, exist_ok=True)
    normalized = []
    for job in jobs:
        source = Path(job.get("local_path", ""))
        if not source.is_file():
            raise PipelineError(f"Missing downloaded clip: {source}")
        target = work / f"clip_{int(job['index']):03d}.mp4"
        command = [
            ffmpeg, "-y", "-i", str(source), "-an",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                   "pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-movflags", "+faststart", str(target),
        ]
        _run(command)
        normalized.append(target)

    concat_file = work / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{path.as_posix().replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n"
                for path in normalized),
        encoding="utf-8",
    )
    silent_output = work / "joined.mp4"
    _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
          "-c", "copy", str(silent_output)])

    inputs = ["-i", str(silent_output)]
    audio_index = None
    subtitle_index = None
    if narration_audio:
        audio = Path(narration_audio)
        if not audio.is_file():
            raise PipelineError(f"Narration audio not found: {audio}")
        audio_index = 1
        inputs += ["-i", str(audio)]
    if subtitles:
        subtitle_file = Path(subtitles)
        if not subtitle_file.is_file():
            raise PipelineError(f"Subtitle file not found: {subtitle_file}")
        subtitle_index = 1 + int(bool(narration_audio))
        inputs += ["-i", str(subtitle_file)]
    command = [ffmpeg, "-y", *inputs, "-map", "0:v:0"]
    if audio_index is not None:
        command += ["-map", f"{audio_index}:a:0", "-c:a", "aac", "-shortest"]
    else:
        command += ["-map", "0:a?", "-c:a", "copy"]
    if subtitle_index is not None:
        command += ["-map", f"{subtitle_index}:s:0", "-c:s", "mov_text"]
    command += ["-c:v", "copy", "-movflags", "+faststart", str(output)]
    _run(command)
    return output


def write_srt(segments: list[dict[str, Any]], target: str | Path) -> Path:
    """Write simple timed Persian/English subtitle cues from storyboard narration."""
    cursor = 0.0
    rows = []
    for item in segments:
        duration = float(item.get("duration_seconds", 15))
        narration = str(item.get("narration", "")).strip()
        if narration:
            start, end = _stamp(cursor), _stamp(cursor + duration)
            rows.append(f"{len(rows)+1}\n{start} --> {end}\n{narration}\n")
        cursor += duration
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows), encoding="utf-8-sig")
    return path


def _stamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _save(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise PipelineError(f"Media command failed: {result.stderr[-2500:]}")
