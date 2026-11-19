"""Minimal VidoGrid REST client using only the Python standard library."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API_BASE_URL = "https://api.vidogrid.ai/uapi/v1"
DEFAULT_VIDEO_ENDPOINT = "/video-gen/grok-imagine-video-1.5-lite"


class VidoGridError(RuntimeError):
    """Raised when VidoGrid returns an error or an invalid response."""


@dataclass(frozen=True)
class VidoGridSettings:
    api_key: str
    base_url: str = API_BASE_URL
    endpoint: str = DEFAULT_VIDEO_ENDPOINT
    model: str = "grok-imagine-video-1.5-lite"
    duration_seconds: int = 15
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "VidoGridSettings":
        env = _load_local_env()
        api_key = env.get("VIDOGRID_API_KEY", "").strip()
        if not api_key:
            raise ValueError("VIDOGRID_API_KEY is required for VidoGrid operations")
        endpoint = env.get("VIDOGRID_ENDPOINT", DEFAULT_VIDEO_ENDPOINT).strip()
        if not endpoint.startswith("/video-gen/"):
            raise ValueError("VIDOGRID_ENDPOINT must be a /video-gen/ path")
        duration = int(env.get("VIDOGRID_DURATION_SECONDS", "15"))
        if not 1 <= duration <= 15:
            raise ValueError("VIDOGRID_DURATION_SECONDS must be between 1 and 15")
        return cls(
            api_key=api_key,
            base_url=env.get("VIDOGRID_BASE_URL", API_BASE_URL).strip().rstrip("/"),
            endpoint=endpoint,
            model=env.get("VIDOGRID_MODEL", "grok-imagine-video-1.5-lite").strip(),
            duration_seconds=duration,
            aspect_ratio=env.get("VIDOGRID_ASPECT_RATIO", "16:9").strip(),
            resolution=env.get("VIDOGRID_RESOLUTION", "720p").strip(),
        )


def _load_local_env() -> dict[str, str]:
    """Read simple KEY=VALUE entries from .env; process env takes precedence."""
    values: dict[str, str] = {}
    env_path = Path(".env")
    if env_path.is_file():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    values.update(os.environ)
    return values


class VidoGridClient:
    def __init__(self, settings: VidoGridSettings):
        self.settings = settings

    def _request(self, method: str, path: str, body: bytes | None = None,
                 content_type: str | None = None) -> dict[str, Any]:
        headers = {"x-api-key": self.settings.api_key, "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = content_type
        request = Request(
            f"{self.settings.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise VidoGridError(f"VidoGrid HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise VidoGridError(f"VidoGrid connection failed: {exc}") from exc
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise VidoGridError("VidoGrid returned non-JSON content") from exc
        if not isinstance(data, dict):
            raise VidoGridError("VidoGrid returned an unexpected response shape")
        return data

    def account(self) -> dict[str, Any]:
        """Return account and credit information; never assumes free quota."""
        return self._request("GET", "/account")

    def submit_video(self, prompt: str) -> dict[str, Any]:
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")
        boundary = f"----NextGen{uuid.uuid4().hex}"
        fields = {
            "prompt": prompt,
            "duration": str(self.settings.duration_seconds),
            "aspect_ratio": self.settings.aspect_ratio,
            "resolution": self.settings.resolution,
        }
        # The Veo endpoint selects its model through a form field; the Grok
        # Lite endpoint is model-specific and uses the duration field directly.
        if self.settings.endpoint == "/video-gen/veo":
            fields["model"] = self.settings.model
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ])
        chunks.append(f"--{boundary}--\r\n".encode())
        response = self._request(
            "POST",
            self.settings.endpoint,
            body=b"".join(chunks),
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        if not response.get("uuid"):
            raise VidoGridError("VidoGrid response did not contain a job uuid")
        return response

    def history(self, job_uuid: str) -> dict[str, Any]:
        if not job_uuid.strip():
            raise ValueError("job_uuid cannot be empty")
        return self._request("GET", f"/history/{quote(job_uuid, safe='')}")
