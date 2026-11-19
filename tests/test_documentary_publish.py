import json
from pathlib import Path

import pytest

from nextgen_academy.documentary_state import initialize_documentary_run, update_chapter_state
from nextgen_academy import documentary_publish


def _reviewed_run(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "target_duration_seconds": 900,
        "chapters": [{"chapter": 1, "title": "Opening"}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    for stage in ("researched", "scripted", "narrated", "assembled", "reviewed"):
        update_chapter_state(state, 1, status=stage)
    video = tmp_path / "final.mp4"; video.write_bytes(b"x" * 2048)
    metadata = tmp_path / "youtube.json"; metadata.write_text(json.dumps({
        "recommended_title": "AI documentary", "description": "Reviewed source-based description",
        "tags": ["AI"]
    }))
    update_chapter_state(state, 1, outputs={"final_documentary": str(video)})
    return state, video, metadata


def test_upload_requires_explicit_approval_and_reviewed_run(tmp_path, monkeypatch):
    state, video, metadata = _reviewed_run(tmp_path)
    monkeypatch.setattr(documentary_publish, "upload_video", lambda *a, **k: {
        "video_id": "abc123", "url": "https://youtube.com/watch?v=abc123",
        "privacy_status": "private"
    })
    with pytest.raises(documentary_publish.DocumentaryPublishError, match="approve-upload"):
        documentary_publish.publish_documentary(state, video, metadata)
    result = documentary_publish.publish_documentary(
        state, video, metadata, privacy_status="private", approve_upload=True
    )
    assert result["uploaded"] is True
    assert result["privacy_status"] == "private"


def test_public_upload_requires_second_confirmation(tmp_path, monkeypatch):
    state, video, metadata = _reviewed_run(tmp_path)
    monkeypatch.setattr(documentary_publish, "upload_video",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not upload")))
    with pytest.raises(documentary_publish.DocumentaryPublishError, match="approve-public"):
        documentary_publish.publish_documentary(
            state, video, metadata, privacy_status="public", approve_upload=True
        )
