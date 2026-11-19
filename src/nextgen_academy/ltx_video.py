"""Optional, budget-gated LTX-2.5 video generation with safe Pexels fallback.

The API is paid per generated second. It is disabled unless both LTX_API_KEY
and a positive LTX_MAX_SPEND_USD are supplied. The local budget is a request
planner, not a provider-side billing hard cap.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LTXError(RuntimeError):
    """Raised when the LTX API cannot produce a usable clip."""


class LTXClient:
    BASE_URL = "https://api.ltx.io/v2"
    PRICES = {
        ("ltx-2-5-fast", "1280x720"): 0.09,
        ("ltx-2-5-fast", "1920x1080"): 0.13,
        ("ltx-2-5-pro", "1280x720"): 0.12,
        ("ltx-2-5-pro", "1920x1080"): 0.17,
    }

    def __init__(self, api_key: str, model: str = "ltx-2-5-fast",
                 resolution: str = "1280x720", duration: int = 8,
                 max_spend_usd: float = 0.0, timeout_seconds: int = 1200):
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.resolution = resolution
        self.duration = duration
        self.max_spend_usd = max(0.0, float(max_spend_usd))
        self.timeout_seconds = timeout_seconds
        if not self.api_key:
            raise LTXError("LTX_API_KEY is missing.")
        if (self.model, self.resolution) not in self.PRICES:
            raise LTXError("Unsupported LTX model/resolution pricing combination.")
        if duration not in (6, 8, 10, 12, 14, 16, 18, 20):
            raise LTXError("Unsupported LTX-2.5 Fast duration.")
        self.cost_per_second = self.PRICES[(self.model, self.resolution)]

    @classmethod
    def from_env(cls) -> "LTXClient | None":
        key = os.getenv("LTX_API_KEY", "").strip()
        try:
            budget = float(os.getenv("LTX_MAX_SPEND_USD", "0") or "0")
        except ValueError:
            budget = 0.0
        if not key or budget <= 0:
            return None
        return cls(
            key,
            model=os.getenv("LTX_MODEL", "ltx-2-5-fast"),
            resolution=os.getenv("LTX_RESOLUTION", "1280x720"),
            duration=int(os.getenv("LTX_CLIP_SECONDS", "8")),
            max_spend_usd=budget,
        )

    @property
    def estimated_clip_cost(self) -> float:
        return round(self.duration * self.cost_per_second, 4)

    def allowed_clip_count(self, remaining_budget: float, max_scenes: int) -> int:
        if remaining_budget <= 0 or max_scenes <= 0:
            return 0
        return min(max_scenes, int((remaining_budget + 1e-9) // self.estimated_clip_cost))

    def generate_clip(self, prompt: str, target: str | Path) -> dict:
        """Submit, poll and download one clip. Does not retry billable jobs."""
        payload = {
            "prompt": prompt,
            "model": self.model,
            "duration": self.duration,
            "resolution": self.resolution,
        }
        job = self._request("POST", f"{self.BASE_URL}/text-to-video", payload)
        job_id = str(job.get("id", "")).strip()
        if not job_id:
            raise LTXError("LTX API did not return a job id.")
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            time.sleep(5)
            status = self._request("GET", f"{self.BASE_URL}/text-to-video/{job_id}")
            state = status.get("status")
            if state == "completed":
                video_url = ((status.get("result") or {}).get("video_url") or "")
                if not video_url.startswith("https://"):
                    raise LTXError("LTX completed without a valid HTTPS video URL.")
                self._download(video_url, target)
                return {
                    "provider": "ltx-2.5",
                    "job_id": job_id,
                    "model": self.model,
                    "resolution": self.resolution,
                    "duration_seconds": self.duration,
                    "estimated_cost_usd": self.estimated_clip_cost,
                }
            if state == "failed":
                raise LTXError(f"LTX job failed: {status.get('error', 'unknown error')}")
            if state not in ("pending", "processing"):
                raise LTXError(f"Unexpected LTX job status: {state!r}")
        raise LTXError(f"LTX job {job_id} timed out; check the LTX console before retrying.")

    def _request(self, method: str, url: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NextGen-Tech-Academy/1.0",
        })
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise LTXError(f"LTX API request failed: {exc}") from exc

    @staticmethod
    def _download(url: str, target: str | Path) -> None:
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        request = Request(url, headers={"User-Agent": "NextGen-Tech-Academy/1.0"})
        try:
            with urlopen(request, timeout=180) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            if temporary.stat().st_size < 100_000:
                raise LTXError("LTX video download is unexpectedly small.")
            temporary.replace(path)
        except Exception as exc:
            if temporary.exists():
                temporary.unlink()
            if isinstance(exc, LTXError):
                raise
            raise LTXError(f"LTX video download failed: {exc}") from exc
