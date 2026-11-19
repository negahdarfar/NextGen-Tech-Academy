"""Minimal VidoGrid REST client using only the Python standard library."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API_BASE_URL = "https://api.vidogrid.ai/uapi/v1"


class VidoGridError(RuntimeError):
    """Raised when VidoGrid returns an error or an invalid response."""


@dataclass(frozen=True)
class VidoGridSettings:
    api_key: str
    base_url: str = API_BASE_URL
    model: str = "veo-3.1-fast"
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "VidoGridSettings":
        api_key = os.getenv("VIDOGRID_API_KEY", "").strip()
        if not api_key:
            raise ValueError("VIDOGRID_API_KEY is required for VidoGrid operations")
        return cls(
            api_key=api_key,
            base_url=os.getenv("VIDOGRID_BASE_URL", API_BASE_URL).strip().rstrip("/"),
            model=os.getenv("VIDOGRID_MODEL", "veo-3.1-fast").strip(),
            aspect_ratio=os.getenv("VIDOGRID_ASPECT_RATIO", "16:9").strip(),
            resolution=os.getenv("VIDOGRID_RESOLUTION", "720p").strip(),
        )


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
            "model": self.settings.model,
            "prompt": prompt,
            "aspect_ratio": self.settings.aspect_ratio,
            "resolution": self.settings.resolution,
        }
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
            "/video-gen/veo",
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
