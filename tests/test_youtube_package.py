import json

from nextgen_academy.youtube_package import build_youtube_package


def test_youtube_package_has_four_chapters_and_no_fake_sources(tmp_path):
    storyboard = tmp_path / "storyboard.json"
    storyboard.write_text(json.dumps({
        "topic": "quantum computing",
        "scenes": [{"title": f"Part {i}"} for i in range(1, 5)],
    }), encoding="utf-8")
    output = build_youtube_package(storyboard, tmp_path / "package.json")
    package = json.loads(output.read_text(encoding="utf-8"))
    assert len(package["chapters"]) == 4
    assert package["chapters"][-1]["time"] == "00:45"
    assert "[ADD PRIMARY SOURCE 1]" in package["description_template"]
    assert package["recommended_title"] in package["title_options"]
