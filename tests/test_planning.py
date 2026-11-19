from nextgen_academy.planning import build_plan


def test_build_plan_has_requested_languages_and_format():
    plan = build_plan("Humanoid robots in manufacturing")
    assert plan.topic == "Humanoid robots in manufacturing"
    assert plan.narration_language == "English"
    assert plan.subtitle_language == "Persian"
    assert plan.format == "standard long-form YouTube video"
    assert "Request human approval before publishing" in plan.stages


def test_build_plan_rejects_empty_topic():
    try:
        build_plan("   ")
    except ValueError as exc:
        assert "topic is required" in str(exc)
    else:
        raise AssertionError("Expected empty topic to be rejected")
