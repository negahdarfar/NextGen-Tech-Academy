import json

from nextgen_academy.video_pipeline import extract_video_url, write_srt


def test_extracts_nested_https_mp4_url():
    payload = {"data": {"status": "completed", "outputs": [{"url": "https://cdn.example.org/out.mp4"}]}}
    assert extract_video_url(payload) == "https://cdn.example.org/out.mp4"


def test_rejects_non_https_video_url():
    import pytest
    from nextgen_academy.video_pipeline import PipelineError
    with pytest.raises(PipelineError):
        extract_video_url({"url": "http://cdn.example.org/out.mp4"})


def test_writes_timed_subtitles(tmp_path):
    path = write_srt([
        {"duration_seconds": 15, "narration": "متن فارسی اول"},
        {"duration_seconds": 15, "narration": "متن فارسی دوم"},
    ], tmp_path / "captions.srt")
    content = path.read_text(encoding="utf-8-sig")
    assert "00:00:00,000 --> 00:00:15,000" in content
    assert "متن فارسی دوم" in content
