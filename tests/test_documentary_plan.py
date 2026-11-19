import json

import pytest

from nextgen_academy.documentary_plan import build_documentary_plan, save_documentary_plan


@pytest.mark.parametrize(("minutes", "slots"), [(15, 75), (30, 150), (60, 300)])
def test_long_form_plan_has_exact_duration_and_visual_slots(minutes, slots):
    plan = build_documentary_plan("AI in science", minutes=minutes)
    assert plan["target_duration_seconds"] == minutes * 60
    assert plan["required_visual_slots"] == slots
    assert plan["shots"][-1]["start_seconds"] + plan["shots"][-1]["duration_seconds"] == minutes * 60
    assert sum(ch["duration_seconds"] for ch in plan["chapters"]) == minutes * 60
    assert plan["pipeline_status"] == "blueprint_only"


def test_plan_is_saved_as_json(tmp_path):
    target = save_documentary_plan(build_documentary_plan("Robotics", 15), tmp_path / "plan.json")
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["narration_language"] == "English"
    assert payload["subtitle_language"] == "Persian"


@pytest.mark.parametrize(("topic", "minutes", "clip_seconds"), [
    (" ", 15, 12), ("topic", 10, 12), ("topic", 15, 20),
])
def test_invalid_inputs_are_rejected(topic, minutes, clip_seconds):
    with pytest.raises(ValueError):
        build_documentary_plan(topic, minutes, clip_seconds)
