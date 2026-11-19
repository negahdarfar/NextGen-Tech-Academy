import json
from pathlib import Path

import pytest

from nextgen_academy.documentary_state import initialize_documentary_run, update_chapter_state
from nextgen_academy import documentary_visuals


def test_visual_generation_resumes_and_records_provider_provenance(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "target_duration_seconds": 60,
        "visual_clip_target_seconds": 12, "chapters": [{"chapter": 1, "title": "x", "duration_seconds": 60}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    update_chapter_state(state, 1, status="researched")
    update_chapter_state(state, 1, status="scripted")
    update_chapter_state(state, 1, status="narrated")
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"chapter": 1, "visual_clip_target_seconds": 12,
                                  "visual_shots": [{"visual_prompt": "A robot in a lab", "stock_search_query": "robot research laboratory"}]}))
    monkeypatch.setenv("AGNES_API_KEY", "test")
    target = tmp_path / "clips" / "clip.mp4"
    def fake_generate(prompt, path, seconds):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 2048)
        return {"provider": "agnes", "model": "mock", "video_id": "test-job", "local_path": str(path), "duration_seconds": seconds}
    monkeypatch.setattr(documentary_visuals, "generate_scene_video", fake_generate)
    result = documentary_visuals.generate_chapter_visuals(state, 1, script, tmp_path / "assets", provider="agnes", allow_agnes_potential_cost=True)
    assert result["status"] == "complete"
    manifest = json.loads(Path(result["manifest_path"]).read_text())
    assert manifest["shots"][0]["provider"] == "agnes"
    # A second run reuses the already downloaded shot; no provider call is made.
    monkeypatch.setattr(documentary_visuals, "generate_scene_video",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must resume")))
    result2 = documentary_visuals.generate_chapter_visuals(state, 1, script, tmp_path / "assets", provider="agnes", allow_agnes_potential_cost=True)
    assert result2["status"] == "complete"


def test_visuals_require_narrated_chapter(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "chapters": [{"chapter": 1, "title": "x"}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"chapter": 1, "visual_shots": [{"visual_prompt": "x"}]}))
    with pytest.raises(documentary_visuals.DocumentaryVisualError, match="narration"):
        documentary_visuals.generate_chapter_visuals(state, 1, script)



def test_zero_budget_auto_uses_pexels_search_terms(tmp_path, monkeypatch):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"topic": "AI", "target_duration_seconds": 60,
        "visual_clip_target_seconds": 12, "chapters": [{"chapter": 1, "title": "x", "duration_seconds": 60}]}))
    state = tmp_path / "state.json"
    initialize_documentary_run(plan, state)
    update_chapter_state(state, 1, status="researched")
    update_chapter_state(state, 1, status="scripted")
    update_chapter_state(state, 1, status="narrated")
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"chapter": 1, "visual_clip_target_seconds": 12,
        "visual_shots": [{"visual_prompt": "Long cinematic prompt about a robotics laboratory",
                          "stock_search_query": "robot research laboratory"}]}))
    monkeypatch.setenv("PEXELS_API_KEY", "test")
    seen = {}
    def fake_download(query, path, min_duration):
        seen["query"] = query
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 2048)
        return {"local_path": str(path), "source_url": "https://pexels.com/video/1",
                "photographer": "Creator", "duration_seconds": 20}
    monkeypatch.setattr(documentary_visuals, "download_scene_video", fake_download)
    result = documentary_visuals.generate_chapter_visuals(state, 1, script, tmp_path / "assets")
    assert result["status"] == "complete"
    assert seen["query"] == "robot research laboratory"
