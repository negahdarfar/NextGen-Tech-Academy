from nextgen_academy import agnes_video


def test_agnes_flash_posts_720p_and_polls(monkeypatch, tmp_path):
    calls = []
    def fake_request(url, method="GET", payload=None, timeout=90):
        calls.append((url, method, payload))
        if method == "POST":
            return {"video_id": "vid-123"}
        return {"status": "completed", "url": "https://cdn.example.org/clip.mp4"}
    def fake_download(url, target):
        target.write_bytes(b"x" * 2048)
    monkeypatch.setenv("AGNES_API_KEY", "test-key")
    monkeypatch.setattr(agnes_video, "_request", fake_request)
    monkeypatch.setattr(agnes_video, "_download", fake_download)
    monkeypatch.setattr(agnes_video.time, "sleep", lambda _: None)

    result = agnes_video.generate_scene_video("cinematic test scene", tmp_path / "clip.mp4")

    assert result["provider"] == "agnes"
    assert result["video_id"] == "vid-123"
    assert calls[0][1] == "POST"
    assert calls[0][2]["model"] == "agnes-video-2.5-flash"
    assert calls[0][2]["seconds"] == "12"
    assert calls[0][2]["size"] == "720P"
    assert "model_name=agnes-video-2.5-flash" in calls[1][0]


def test_agnes_rejects_unsupported_duration():
    import pytest
    with pytest.raises(ValueError):
        agnes_video.generate_scene_video("scene", "clip.mp4", seconds=15)
