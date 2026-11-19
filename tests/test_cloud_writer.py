import json
from unittest.mock import patch

import pytest

from nextgen_academy.cloud_writer import draft_cloud_storyboard


def sources():
    return [
        {"id": "src1", "title": "Research paper", "publisher": "arXiv",
         "url": "https://arxiv.org/abs/1234", "summary": "A study overview", "checked": False},
        {"id": "src2", "title": "Industry report", "publisher": "News",
         "url": "https://example.org/report", "summary": "A report summary", "checked": False},
    ]


def draft():
    return {
        "scenes": [
            {"title": f"Scene {i}", "scene": "Visual description",
             "narration_en": "This technology is changing how researchers and engineers solve difficult problems across several industries around the world today.",
             "subtitle_fa": "این فناوری شیوه حل مسائل را در صنایع گوناگون تغییر می‌دهد."}
            for i in range(1, 5)
        ],
        "claims": [{"text": "A supported claim", "source_ids": ["src1", "src2"]}],
    }


def test_cloud_writer_saves_four_bilingual_scenes(tmp_path):
    with patch("nextgen_academy.cloud_writer.generate_json", return_value=draft()):
        path = draft_cloud_storyboard("robotics", sources(), tmp_path / "story.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["scenes"]) == 4
    assert payload["language"]["narration"] == "English"
    assert payload["sources"][0]["checked"] is False


def test_cloud_writer_rejects_unknown_source_ids(tmp_path):
    bad = draft()
    bad["claims"][0]["source_ids"] = ["not-a-source"]
    with patch("nextgen_academy.cloud_writer.generate_json", return_value=bad):
        with pytest.raises(ValueError, match="source IDs"):
            draft_cloud_storyboard("robotics", sources(), tmp_path / "story.json")
