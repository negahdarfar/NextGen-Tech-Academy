"""Tests for the long-form documentary assembly utility."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "assemble_documentary", ROOT / "scripts" / "assemble_documentary.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_manifest_resolves_relative_clip_paths(tmp_path):
    clip = tmp_path / "scene.mp4"
    clip.write_bytes(b"video-placeholder")
    manifest = tmp_path / "clips.json"
    manifest.write_text(json.dumps(["scene.mp4"]), encoding="utf-8")
    assert MODULE.load_clip_manifest(manifest) == [clip.resolve()]


def test_manifest_rejects_empty_list(tmp_path):
    manifest = tmp_path / "clips.json"
    manifest.write_text("[]", encoding="utf-8")
    try:
        MODULE.load_clip_manifest(manifest)
    except MODULE.DocumentaryError as exc:
        assert "non-empty" in str(exc)
    else:
        raise AssertionError("empty manifest should be rejected")


def test_manifest_rejects_missing_clip(tmp_path):
    manifest = tmp_path / "clips.json"
    manifest.write_text(json.dumps(["missing.mp4"]), encoding="utf-8")
    try:
        MODULE.load_clip_manifest(manifest)
    except MODULE.DocumentaryError as exc:
        assert "Clip not found" in str(exc)
    else:
        raise AssertionError("missing clip should be rejected")


# Long-form integration assembly tests
import pytest

from nextgen_academy.documentary_state import initialize_documentary_run, update_chapter_state, load_run_state
from nextgen_academy import documentary_assembly


def _run_with_outputs(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "target_duration_seconds": 60,
        "chapters": [{"chapter": 1, "title": "x", "duration_seconds": 60}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    for stage in ("researched", "scripted", "narrated"):
        update_chapter_state(state, 1, status=stage)
    audio = tmp_path / "audio.mp3"; audio.write_bytes(b"a" * 2048)
    srt = tmp_path / "captions.srt"; srt.write_text("1\n00:00:00,000 --> 00:00:10,000\nسلام\n", encoding="utf-8-sig")
    clip = tmp_path / "clip.mp4"; clip.write_bytes(b"v" * 2048)
    manifest = tmp_path / "assets.json"
    manifest.write_text(json.dumps({"status": "complete", "shots": [
        {"shot": 1, "local_path": str(clip), "provider": "agnes", "model": "agnes-video-2.5-flash", "video_id": "test-job"}
    ]}))
    update_chapter_state(state, 1, outputs={"narration_audio": str(audio),
        "persian_subtitles": str(srt), "visual_manifest": str(manifest)})
    return state


def test_assembles_all_chapters_and_checkpoints_without_public_upload(tmp_path, monkeypatch):
    state = _run_with_outputs(tmp_path)
    monkeypatch.setattr(documentary_assembly.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(documentary_assembly, "_duration", lambda ffprobe, path: 60.0)
    def fake_run(command):
        if "-show_entries" in command:
            return json.dumps({"streams": [
                {"codec_type": "video", "width": 1920, "height": 1080, "avg_frame_rate": "30/1"},
                {"codec_type": "audio", "sample_rate": "48000", "channels": 2}, {"codec_type": "subtitle"}]})
        if command[-1].endswith(".mp4") or command[-1].endswith(".wav"):
            Path(command[-1]).write_bytes(b"z" * 2048)
        return ""
    monkeypatch.setattr(documentary_assembly, "_run", fake_run)
    output = tmp_path / "final.mp4"
    result = documentary_assembly.assemble_documentary_run(state, output)
    assert result["status"] == "assembled_pending_human_review"
    assert result["public_upload"] is False
    assert output.is_file()
    assert load_run_state(state)["chapters"][0]["status"] == "assembled"


def test_assembly_rejects_missing_visual_provenance(tmp_path):
    state = _run_with_outputs(tmp_path)
    data = load_run_state(state)
    data["chapters"][0]["outputs"].pop("visual_manifest")
    state.write_text(json.dumps(data))
    with pytest.raises(documentary_assembly.DocumentaryAssemblyError, match="missing outputs"):
        documentary_assembly.assemble_documentary_run(state, tmp_path / "final.mp4")
