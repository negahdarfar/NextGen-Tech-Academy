import json
from unittest.mock import patch
import pytest
from nextgen_academy.cloud_writer import draft_cloud_storyboard

def sources():
    return [{"id":"src1","title":"Research paper","publisher":"arXiv","url":"https://arxiv.org/abs/1234","summary":"A study overview"},
            {"id":"src2","title":"Industry report","publisher":"News","url":"https://example.org/report","summary":"A report summary"}]

def draft(n=20):
    return {"scenes":[{"title":f"Scene {i}","scene":"Visual description",
        "narration_en":"This technology is changing how researchers solve difficult problems across several industries around the world today.",
        "subtitle_fa":"این فناوری شیوه حل مسائل را در صنایع گوناگون تغییر می‌دهد.",
        "source_ids":["src1"]} for i in range(1,n+1)],
        "claims":[{"text":"A supported claim","source_ids":["src1","src2"]}]}

def test_cloud_writer_saves_five_minute_storyboard(tmp_path):
    with patch("nextgen_academy.cloud_writer.generate_json",return_value=draft()):
        path=draft_cloud_storyboard("robotics",sources(),tmp_path/"story.json",300)
    data=json.loads(path.read_text(encoding="utf-8"))
    assert len(data["scenes"])==20
    assert data["target_duration_seconds"]==300
    assert all(scene["source_ids"] for scene in data["scenes"])

def test_cloud_writer_rejects_wrong_scene_count(tmp_path):
    with patch("nextgen_academy.cloud_writer.generate_json",return_value=draft(4)):
        with pytest.raises(ValueError,match="exactly 20"):
            draft_cloud_storyboard("robotics",sources(),tmp_path/"story.json",300)

def test_cloud_writer_rejects_unknown_source_ids(tmp_path):
    bad=draft(); bad["claims"][0]["source_ids"]=["not-a-source"]
    with patch("nextgen_academy.cloud_writer.generate_json",return_value=bad):
        with pytest.raises(ValueError,match="source IDs"):
            draft_cloud_storyboard("robotics",sources(),tmp_path/"story.json",300)

def test_cloud_writer_rejects_scene_without_source_ids(tmp_path):
    bad=draft(); bad["scenes"][0]["source_ids"]=[]
    with patch("nextgen_academy.cloud_writer.generate_json",return_value=bad):
        with pytest.raises(ValueError,match="Scene 1"):
            draft_cloud_storyboard("robotics",sources(),tmp_path/"story.json",300)

def test_cloud_writer_rejects_overlong_narration(tmp_path):
    bad=draft(); bad["scenes"][0]["narration_en"]=" ".join(["word"]*35)
    with patch("nextgen_academy.cloud_writer.generate_json",return_value=bad):
        with pytest.raises(ValueError,match="18-30"):
            draft_cloud_storyboard("robotics",sources(),tmp_path/"story.json",300)
