import json
from pathlib import Path

from nextgen_academy.documentary_metadata import build_documentary_metadata


def test_builds_chapter_metadata_and_credits_from_provenance(tmp_path):
    script = tmp_path / "chapter-script.json"
    script.write_text(json.dumps({"sources": [
        {"publisher": "Journal", "title": "Primary study", "url": "https://example.org/study"}
    ]}))
    clip_manifest = tmp_path / "assets.json"
    clip_manifest.write_text(json.dumps({"shots": [
        {"provider": "pexels", "photographer": "A. Creator", "source_url": "https://pexels.com/video/123"}
    ]}))
    state = tmp_path / "state.json"
    state.write_text(json.dumps({
        "schema_version": 1, "topic": "AI in science", "target_duration_seconds": 900,
        "chapters": [{"chapter": 1, "title": "Opening", "outputs": {
            "script": str(script), "visual_manifest": str(clip_manifest)
        }}]
    }))
    target = build_documentary_metadata(state, tmp_path / "youtube.json", [
        {"chapter": 1, "title": "Opening", "start_seconds": 0, "end_seconds": 60}
    ])
    payload = json.loads(target.read_text())
    assert payload["chapters"][0]["time"] == "00:00"
    assert "https://example.org/study" in payload["description"]
    assert "A. Creator" in payload["description"]
    assert payload["upload_performed"] is False
    assert payload["requires_human_review"] is True
