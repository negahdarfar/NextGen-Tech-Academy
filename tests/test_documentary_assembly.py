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
