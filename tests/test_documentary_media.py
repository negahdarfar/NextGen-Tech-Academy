import json
from pathlib import Path

import pytest

from nextgen_academy.documentary_state import initialize_documentary_run, update_chapter_state, load_run_state
from nextgen_academy import documentary_media


def _scripted_run(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "chapters": [
        {"chapter": 1, "title": "Chapter", "duration_seconds": 60, "target_narration_words": 100}
    ]}), encoding="utf-8")
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    update_chapter_state(state, 1, status="researched")
    update_chapter_state(state, 1, status="scripted")
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"chapter": 1, "narration_en": "Hello world. This is a test.",
                                  "subtitle_fa": "سلام دنیا. این یک آزمایش است."}), encoding="utf-8")
    return state, script


def test_chapter_tts_writes_audio_subtitles_and_checkpoints(tmp_path, monkeypatch):
    state, script = _scripted_run(tmp_path)
    monkeypatch.setattr(documentary_media.shutil, "which", lambda name: "/usr/bin/" + name)
    def fake_run(command, **kwargs):
        if "ffprobe" in command[0]:
            return type("Result", (), {"returncode": 0, "stdout": "12.5", "stderr": ""})()
        Path(command[-1]).write_bytes(b"x" * 2048)
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(documentary_media.subprocess, "run", fake_run)
    result = documentary_media.synthesize_documentary_chapter(state, 1, script, tmp_path / "media")
    assert result["status"] == "narrated"
    assert result["human_timing_review_required"] is True
    saved = load_run_state(state)["chapters"][0]
    assert saved["status"] == "narrated"
    assert Path(saved["outputs"]["narration_audio"]).is_file()
    assert Path(saved["outputs"]["persian_subtitles"]).is_file()


def test_tts_refuses_wrong_stage(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "chapters": [{"chapter": 1, "title": "x"}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    script = tmp_path / "script.json"
    script.write_text("{}")
    with pytest.raises(documentary_media.DocumentaryMediaError, match="scripted"):
        documentary_media.synthesize_documentary_chapter(state, 1, script)
