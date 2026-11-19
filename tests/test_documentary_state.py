import json

import pytest

from nextgen_academy.documentary_state import (
    initialize_documentary_run,
    load_run_state,
    update_chapter_state,
)


def _blueprint(path):
    path.write_text(json.dumps({
        "topic": "Test topic",
        "target_duration_seconds": 900,
        "chapters": [
            {"chapter": 1, "title": "Opening"},
            {"chapter": 2, "title": "Evidence"},
        ],
    }), encoding="utf-8")
    return path


def test_initialize_and_resume_preserves_completed_chapter(tmp_path):
    plan = _blueprint(tmp_path / "plan.json")
    state = tmp_path / "run.json"
    initialize_documentary_run(plan, state)
    update_chapter_state(state, 1, status="researched", outputs={"research": "ch1.json"})
    update_chapter_state(state, 1, status="scripted", outputs={"script": "ch1.md"})
    update_chapter_state(state, 2, error="temporary provider failure")
    loaded = load_run_state(state)
    assert loaded["chapters"][0]["status"] == "scripted"
    assert loaded["chapters"][0]["outputs"]["research"] == "ch1.json"
    assert loaded["chapters"][1]["attempts"] == 1
    assert loaded["chapters"][1]["status"] == "planned"


def test_initialize_refuses_to_overwrite_existing_state(tmp_path):
    plan = _blueprint(tmp_path / "plan.json")
    state = tmp_path / "run.json"
    initialize_documentary_run(plan, state)
    with pytest.raises(FileExistsError):
        initialize_documentary_run(plan, state)


def test_stages_must_be_sequential_and_cannot_regress(tmp_path):
    plan = _blueprint(tmp_path / "plan.json")
    state = tmp_path / "run.json"
    initialize_documentary_run(plan, state)
    with pytest.raises(ValueError, match="cannot be skipped"):
        update_chapter_state(state, 1, status="scripted")
    update_chapter_state(state, 1, status="researched")
    with pytest.raises(ValueError, match="regression"):
        update_chapter_state(state, 1, status="planned")


def test_all_reviewed_marks_run_ready_for_human_approval(tmp_path):
    plan = _blueprint(tmp_path / "plan.json")
    state = tmp_path / "run.json"
    initialize_documentary_run(plan, state)
    for chapter in (1, 2):
        for stage in ("researched", "scripted", "narrated", "assembled", "reviewed"):
            update_chapter_state(state, chapter, status=stage)
    assert load_run_state(state)["status"] == "ready_for_human_approval"
