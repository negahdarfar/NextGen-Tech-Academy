"""Human-approved YouTube publishing for a fully reviewed long-form documentary."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .documentary_state import load_run_state
from .youtube_upload import upload_video


class DocumentaryPublishError(RuntimeError):
    pass


def publish_documentary(
    state_path: str | Path,
    video_path: str | Path,
    metadata_path: str | Path,
    privacy_status: str = "private",
    approve_upload: bool = False,
    approve_public: bool = False,
) -> dict[str, Any]:
    """Upload only after every chapter is reviewed and explicit approvals are present."""
    if not approve_upload:
        raise DocumentaryPublishError("Upload requires the separate --approve-upload confirmation.")
    if privacy_status not in {"private", "unlisted", "public"}:
        raise ValueError("privacy_status must be private, unlisted, or public.")
    if privacy_status == "public" and not approve_public:
        raise DocumentaryPublishError("Public visibility requires the additional --approve-public confirmation.")
    if privacy_status != "public" and approve_public:
        raise DocumentaryPublishError("--approve-public is only valid with --privacy-status public.")

    state = load_run_state(state_path)
    if state.get("status") != "ready_for_human_approval":
        raise DocumentaryPublishError(
            "Every chapter must be marked reviewed after watching the complete video and checking sources, rights and subtitles."
        )
    video = Path(video_path)
    metadata = Path(metadata_path)
    if not video.is_file() or video.stat().st_size < 1024:
        raise DocumentaryPublishError("Final documentary MP4 is missing or invalid.")
    if not metadata.is_file():
        raise DocumentaryPublishError("YouTube metadata package is missing.")
    for chapter in state["chapters"]:
        if chapter.get("status") != "reviewed":
            raise DocumentaryPublishError("All chapters must be reviewed before upload.")
        if chapter.get("outputs", {}).get("final_documentary") != str(video):
            raise DocumentaryPublishError("The reviewed run does not point to this exact final documentary file.")

    os.environ["YOUTUBE_ALLOW_PUBLIC"] = "true" if privacy_status == "public" and approve_public else "false"
    uploaded = upload_video(video, metadata, privacy_status=privacy_status)
    return {
        "uploaded": True,
        "video_id": uploaded.get("video_id"),
        "url": uploaded.get("url"),
        "privacy_status": uploaded.get("privacy_status"),
        "human_approval_recorded": True,
    }
