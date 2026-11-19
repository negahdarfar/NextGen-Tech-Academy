"""Free stock-video retrieval from the Pexels API.

Pexels API access is free subject to its published rate limits and license.
It requires a free API key; this adapter never silently falls back to paid APIs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PexelsError(RuntimeError):
    pass


def download_scene_video(query: str, target: str | Path, min_duration: int = 15) -> dict:
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        raise PexelsError("Set the free PEXELS_API_KEY GitHub Secret to use Pexels stock footage.")
    if not query.strip():
        raise ValueError("A non-empty scene query is required.")
    params = urlencode({"query": query[:180], "per_page": 20, "orientation": "landscape"})
    request = Request(
        f"https://api.pexels.com/videos/search?{params}",
        headers={"Authorization": api_key, "User-Agent": "NextGen-Tech-Academy/1.0"},
    )
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise PexelsError(f"Pexels search failed: {exc}") from exc

    candidates = []
    for video in payload.get("videos", []):
        duration = int(video.get("duration", 0) or 0)
        if duration < min_duration:
            continue
        files = [item for item in video.get("video_files", [])
                 if item.get("link") and item.get("file_type") == "video/mp4"]
        if not files:
            continue
        files.sort(key=lambda item: (int(item.get("width", 0) or 0),
                                     int(item.get("height", 0) or 0)), reverse=True)
        candidates.append((video, files[0]))
    if not candidates:
        raise PexelsError(f"No landscape Pexels clip of at least {min_duration}s found for: {query}")

    video, selected = candidates[0]
    destination = Path(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    download = Request(selected["link"], headers={"User-Agent": "NextGen-Tech-Academy/1.0"})
    try:
        with urlopen(download, timeout=180) as response, destination.open("wb") as output:
            output.write(response.read())
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise PexelsError(f"Pexels clip download failed: {exc}") from exc
    if destination.stat().st_size < 1024:
        destination.unlink(missing_ok=True)
        raise PexelsError("Pexels returned an unexpectedly small video file.")
    return {
        "pexels_video_id": video.get("id"),
        "photographer": video.get("user", {}).get("name", ""),
        "source_url": video.get("url", ""),
        "duration_seconds": video.get("duration"),
        "local_path": str(destination),
    }
