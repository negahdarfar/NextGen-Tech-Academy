"""Resumable YouTube uploads using a pre-authorized OAuth refresh token."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class YouTubeUploadError(RuntimeError):
    pass


def upload_video(video_path: str | Path, metadata_path: str | Path,
                 privacy_status: str | None = None) -> dict[str, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise YouTubeUploadError("Install the youtube optional dependencies.") from exc

    token_json = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    if not token_json:
        raise YouTubeUploadError("YOUTUBE_TOKEN_JSON secret is missing.")
    try:
        token_info = json.loads(token_json)
        credentials = Credentials.from_authorized_user_info(
            token_info, scopes=["https://www.googleapis.com/auth/youtube.upload"])
    except Exception as exc:
        raise YouTubeUploadError(f"Invalid YouTube OAuth token JSON: {exc}") from exc
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials.valid:
        raise YouTubeUploadError("YouTube OAuth credentials are not valid or refreshable.")

    video = Path(video_path)
    if not video.is_file() or video.stat().st_size < 1024:
        raise YouTubeUploadError("The final MP4 is missing or unexpectedly small.")
    package = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    title = str(package.get("recommended_title", "")).strip()[:100]
    description = str(package.get("description", package.get("description_template", ""))).strip()[:5000]
    if not title or not description or "[ADD PRIMARY SOURCE" in description:
        raise YouTubeUploadError("YouTube metadata is incomplete or still contains source placeholders.")
    privacy = privacy_status or os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
    if privacy not in {"private", "unlisted", "public"}:
        raise YouTubeUploadError("YOUTUBE_PRIVACY_STATUS must be private, unlisted or public.")
    if privacy == "public" and os.getenv("YOUTUBE_ALLOW_PUBLIC", "").lower() != "true":
        raise YouTubeUploadError("Public publishing is disabled. Set YOUTUBE_ALLOW_PUBLIC=true only after review.")

    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    body = {
        "snippet": {"title": title, "description": description,
                    "tags": package.get("tags", [])[:30], "categoryId": "28",
                    "defaultLanguage": "en"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024,
                            resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    retries = 0
    while response is None:
        try:
            _, response = request.next_chunk()
        except Exception:
            retries += 1
            if retries > 5:
                raise
    return {"video_id": response.get("id"), "url": f"https://www.youtube.com/watch?v={response.get('id')}",
            "privacy_status": privacy, "title": title}
