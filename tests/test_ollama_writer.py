import io
import json
from unittest.mock import patch

from nextgen_academy.ollama_writer import draft_storyboard


def test_ollama_draft_writes_bilingual_four_scene_package(tmp_path):
    scenes = [
        {
            "title": f"Scene {i}",
            "scene": "A visual description",
            "narration_en": "This technology is changing how people work, learn, and solve difficult problems across many industries around the world today.",
            "subtitle_fa": "این فناوری شیوه کار و یادگیری مردم را تغییر می‌دهد.",
        }
        for i in range(1, 5)
    ]
    response = {"message": {"content": json.dumps({"scenes": scenes})}}
    fake = io.BytesIO(json.dumps(response).encode("utf-8"))
    with patch("nextgen_academy.ollama_writer.urlopen", return_value=fake):
        path = draft_storyboard("technology", tmp_path / "storyboard.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["scenes"]) == 4
    assert payload["language"]["narration"] == "English"
    assert payload["language"]["subtitles"] == "Persian"
    assert payload["sources"] == []
