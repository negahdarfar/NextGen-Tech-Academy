"""Download royalty-free stock footage from the Pexels API."""
from __future__ import annotations
import json, os, shutil
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class StockMediaError(RuntimeError):
    pass

class PexelsClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or os.getenv("PEXELS_API_KEY", "")).strip()
        if not self.api_key:
            raise StockMediaError("PEXELS_API_KEY is missing. Add a free Pexels API key as a GitHub Actions secret.")

    def search(self, query: str) -> dict:
        url = "https://api.pexels.com/videos/search?" + urlencode({"query": query, "per_page": 12, "orientation": "landscape"})
        request = Request(url, headers={"Authorization": self.api_key, "User-Agent": "NextGen-Tech-Academy/1.0"})
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise StockMediaError(f"Pexels search failed for '{query}': {exc}") from exc
        if not payload.get("videos"):
            raise StockMediaError(f"Pexels returned no landscape footage for: {query}")
        return payload

    def download_clip(self, query: str, target: str | Path, min_duration: int = 15) -> dict:
        payload = self.search(query)
        candidates = []
        for video in payload.get("videos", []):
            files = sorted(video.get("video_files", []), key=lambda f: (f.get("width", 0), f.get("height", 0)), reverse=True)
            for item in files:
                link = item.get("link", "")
                if link.startswith("https://") and item.get("width", 0) >= 640 and item.get("height", 0) >= 360:
                    candidates.append((video, item))
                    break
        if not candidates:
            raise StockMediaError(f"No downloadable landscape MP4 found for: {query}")
        video, selected = max(candidates, key=lambda pair: (pair[0].get("duration", 0) >= min_duration, pair[1].get("width", 0)))
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        request = Request(selected["link"], headers={"User-Agent": "NextGen-Tech-Academy/1.0"})
        temporary = target.with_suffix(target.suffix + ".part")
        try:
            with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            if temporary.stat().st_size < 100_000:
                raise StockMediaError("Downloaded stock clip is unexpectedly small.")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return {"pexels_video_id": video.get("id"), "creator": (video.get("user") or {}).get("name", ""),
                "source_url": video.get("url", ""), "duration": video.get("duration", 0),
                "width": selected.get("width"), "height": selected.get("height")}
