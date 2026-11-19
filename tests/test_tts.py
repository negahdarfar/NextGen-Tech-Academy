import json
import pytest

from nextgen_academy.tts import TTSError, validate_scenes
from nextgen_academy.script import storyboard_subtitles


def scenes():
    return [
        {"narration_en": f"English line {i}", "subtitle_fa": f"متن فارسی {i}"}
        for i in range(1, 5)
    ]


def test_validate_requires_four_bilingual_scenes():
    validate_scenes(scenes())
    with pytest.raises(TTSError):
        validate_scenes(scenes()[:3])


def test_validate_rejects_missing_english_narration():
    data = scenes()
    data[2]["narration_en"] = ""
    with pytest.raises(TTSError):
        validate_scenes(data)


def test_storyboard_subtitles_are_timed_in_four_quarters(tmp_path):
    source = tmp_path / "storyboard.json"
    source.write_text(json.dumps({"scenes": scenes()}, ensure_ascii=False), encoding="utf-8")
    result = storyboard_subtitles(source, tmp_path / "fa.srt")
    text = result.read_text(encoding="utf-8-sig")
    assert "00:00:00,000 --> 00:00:15,000" in text
    assert "00:00:45,000 --> 00:01:00,000" in text
    assert "متن فارسی 4" in text
