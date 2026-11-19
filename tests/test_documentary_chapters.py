import json

import pytest

from nextgen_academy.documentary_state import initialize_documentary_run, load_run_state
from nextgen_academy import documentary_chapters as chapters


def _state(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({
        "topic": "AI in science", "target_duration_seconds": 900,
        "chapters": [{"chapter": 1, "title": "The evidence",
                      "duration_seconds": 45, "target_narration_words": 100}],
    }), encoding="utf-8")
    state = tmp_path / "run.json"
    initialize_documentary_run(plan, state)
    return state


def test_process_chapter_researches_writes_script_and_updates_state(tmp_path, monkeypatch):
    state = _state(tmp_path)
    sources = [
        {"id": "src1", "title": "Study one", "publisher": "Journal", "url": "https://example.org/1", "summary": "Evidence"},
        {"id": "src2", "title": "Study two", "publisher": "Lab", "url": "https://example.org/2", "summary": "More evidence"},
    ]
    monkeypatch.setattr(chapters, "discover_sources", lambda *a, **k: sources)
    narration = " ".join(["Evidence"] * 100)
    monkeypatch.setattr(chapters, "generate_json", lambda *a, **k: {
        "narration_en": narration, "subtitle_fa": "ترجمه کامل فارسی",
        "claims": [{"text": "A supported claim", "source_ids": ["src1"]}],
        "visual_shots": [{"visual_prompt": f"Shot {i}: cinematic science laboratory", "stock_search_query": "science laboratory robot"} for i in range(4)],
    })
    result = chapters.process_documentary_chapter(state, 1, tmp_path / "out")
    assert result["status"] == "scripted"
    saved = load_run_state(state)["chapters"][0]
    assert saved["status"] == "scripted"
    assert saved["target_narration_words"] == 100
    assert saved["duration_seconds"] == 45
    assert (tmp_path / "out" / "chapter-01-script.json").is_file()


def test_completed_script_is_skipped_without_provider_calls(tmp_path, monkeypatch):
    state = _state(tmp_path)
    monkeypatch.setattr(chapters, "discover_sources", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(chapters, "generate_json", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    # Advance the manifest as if a previous execution completed this chapter.
    from nextgen_academy.documentary_state import update_chapter_state
    update_chapter_state(state, 1, status="researched")
    update_chapter_state(state, 1, status="scripted")
    result = chapters.process_documentary_chapter(state, 1, tmp_path / "out")
    assert result["skipped"] is True


def test_invalid_claim_source_is_rejected(tmp_path, monkeypatch):
    state = _state(tmp_path)
    sources = [
        {"id": "src1", "title": "Study one", "publisher": "Journal", "url": "https://example.org/1", "summary": "Evidence"},
        {"id": "src2", "title": "Study two", "publisher": "Lab", "url": "https://example.org/2", "summary": "More evidence"},
    ]
    monkeypatch.setattr(chapters, "discover_sources", lambda *a, **k: sources)
    monkeypatch.setattr(chapters, "generate_json", lambda *a, **k: {
        "narration_en": " ".join(["Evidence"] * 100), "subtitle_fa": "ترجمه",
        "claims": [{"text": "Unsupported", "source_ids": ["missing"]}],
        "visual_shots": [{"visual_prompt": f"Shot {i}: cinematic science laboratory", "stock_search_query": "science laboratory robot"} for i in range(4)],
    })
    with pytest.raises(ValueError, match="invalid source IDs"):
        chapters.process_documentary_chapter(state, 1, tmp_path / "out")
    assert load_run_state(state)["chapters"][0]["status"] == "researched"
