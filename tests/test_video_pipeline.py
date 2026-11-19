import pytest
from nextgen_academy.video_pipeline import write_srt, PipelineError

def test_writes_timed_subtitles(tmp_path):
    path=write_srt([{"duration_seconds":15,"narration":"متن فارسی اول"},{"duration_seconds":15,"narration":"متن فارسی دوم"}],tmp_path/"captions.srt")
    content=path.read_text(encoding="utf-8-sig")
    assert "00:00:00,000 --> 00:00:15,000" in content
    assert "متن فارسی دوم" in content

def test_duration_validation_rejects_missing_ffprobe(monkeypatch,tmp_path):
    from nextgen_academy import video_pipeline
    monkeypatch.setattr(video_pipeline.shutil,"which",lambda _:None)
    with pytest.raises(PipelineError,match="ffprobe"):
        video_pipeline.validate_render_duration(tmp_path/"missing.mp4")
