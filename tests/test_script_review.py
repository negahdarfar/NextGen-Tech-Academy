import json

from nextgen_academy.script_review import review_storyboard


def test_review_requires_sources_and_claim_mapping(tmp_path):
    data = {
        "topic": "AI robotics",
        "scenes": [
            {"narration_en": "This is a narration with enough words to describe the technology clearly and explain its real world impact to viewers.", "subtitle_fa": "زیرنویس فارسی"}
            for _ in range(4)
        ],
        "sources": [
            {"id": "s1", "url": "https://example.org/report", "publisher": "Example", "checked": True},
            {"id": "s2", "url": "https://example.org/paper", "publisher": "Example", "checked": True},
        ],
        "claims": [{"text": "A testable factual claim", "source_ids": ["s1", "s2"]}],
    }
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert review_storyboard(path)["passed"] is True
    data["claims"][0]["source_ids"] = ["unknown"]
    path.write_text(json.dumps(data), encoding="utf-8")
    report = review_storyboard(path)
    assert report["passed"] is False
    assert any("source_ids" in error for error in report["errors"])
