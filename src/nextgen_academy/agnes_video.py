"""Agnes AI Video 2.5 Flash adapter (720p, asynchronous API)."""
from __future__ import annotations

import json
import os
import time
from ipaddress import ip_address
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class AgnesVideoError(RuntimeError):
    """Raised when Agnes video generation or retrieval fails."""


def _request(url: str, *, method: str = "GET", payload: dict | None = None,
             timeout: int = 90) -> dict:
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        raise AgnesVideoError("AGNES_API_KEY is not configured.")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "NextGen-Tech-Academy/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except HTTPError as exc:
        detail = exc.read(1500).decode("utf-8", errors="replace")
        raise AgnesVideoError(f"Agnes API returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise AgnesVideoError(f"Agnes API request failed: {exc}") from exc
    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgnesVideoError("Agnes API returned invalid JSON.") from exc
    if not isinstance(result, dict):
        raise AgnesVideoError("Agnes API returned an unexpected response.")
    return result


def _download(url: str, target: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise AgnesVideoError("Refusing a non-HTTPS or malformed video URL.")
    try:
        address = ip_address(parsed.hostname)
        if not address.is_global:
            raise AgnesVideoError("Refusing a non-public video download host.")
    except ValueError:
        if parsed.hostname in {"localhost"} or parsed.hostname.endswith(".local"):
            raise AgnesVideoError("Refusing a local video download host.")
    request = Request(url, headers={"User-Agent": "NextGen-Tech-Academy/1.0"})
    temporary = target.with_suffix(target.suffix + ".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(request, timeout=180) as response, temporary.open("wb") as output:
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type and not (content_type.startswith("video/") or
                                     "octet-stream" in content_type):
                raise AgnesVideoError(f"Unexpected video content type: {content_type}")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        if temporary.stat().st_size < 1024:
            raise AgnesVideoError("Agnes returned an unexpectedly small video file.")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def generate_scene_video(prompt: str, target: str | Path,
                         seconds: int = 12, timeout_seconds: int = 1800) -> dict:
    """Generate a 4–12 second 720p 16:9 clip and return local provenance."""
    if not 4 <= seconds <= 12:
        raise ValueError("Agnes Video 2.5 Flash supports 4–12 second clips.")
    if not prompt.strip():
        raise ValueError("A non-empty video prompt is required.")
    base = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip("/")
    model = "agnes-video-2.5-flash"
    created = _request(
        f"{base}/videos", method="POST",
        payload={"model": model, "prompt": prompt, "mode": "text",
                 "seconds": str(seconds), "size": "720P",
                 "aspect_ratio": "16:9", "n": 1},
        timeout=120,
    )
    video_id = created.get("video_id")
    if not video_id:
        raise AgnesVideoError(f"Agnes create response did not contain video_id: {created}")
    poll_base = base.rsplit("/v1", 1)[0]
    poll_url = (f"{poll_base}/agnesapi?video_id={video_id}"
                f"&model_name={model}")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = _request(poll_url, timeout=90)
        status = str(result.get("status", "")).lower()
        if status == "completed":
            video_url = result.get("url")
            if not isinstance(video_url, str) or not video_url:
                raise AgnesVideoError("Agnes marked the task completed but returned no URL.")
            destination = Path(target)
            _download(video_url, destination)
            return {"provider": "agnes", "model": model, "video_id": video_id,
                    "duration_seconds": seconds, "resolution": "720P",
                    "local_path": str(destination)}
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise AgnesVideoError(f"Agnes video generation failed: {result}")
        time.sleep(12)
    raise TimeoutError(f"Timed out waiting for Agnes video {video_id}.")
