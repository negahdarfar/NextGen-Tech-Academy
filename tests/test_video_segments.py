import pytest

from nextgen_academy.video_segments import build_segments


def test_builds_ordered_15_second_segments_with_continuity():
    clips = build_segments(
        "Future of robotics",
        ["A factory exterior at dawn", "A robot arm assembling a component"],
    )
    assert len(clips) == 2
    assert clips[0].duration_seconds == 15
    assert "Opening shot" in clips[0].continuity_in
    assert "Continue directly from clip 1" in clips[1].continuity_in
    assert "same subjects" in clips[1].prompt
    assert "16:9" in clips[0].prompt


def test_rejects_empty_scenes_and_invalid_duration():
    with pytest.raises(ValueError):
        build_segments("Robotics", [])
    with pytest.raises(ValueError):
        build_segments("Robotics", ["A robot"], duration_seconds=20)
