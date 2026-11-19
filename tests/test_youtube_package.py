import json
from nextgen_academy.youtube_package import build_youtube_package

def test_youtube_package_has_longform_chapters_and_no_fake_sources(tmp_path):
    storyboard=tmp_path/"storyboard.json"
    storyboard.write_text(json.dumps({
        "topic":"quantum computing",
        "clip_duration_seconds":15,
        "scenes":[{"title":f"Part {i}"} for i in range(1,21)],
    }),encoding="utf-8")
    output=build_youtube_package(storyboard,tmp_path/"package.json")
    package=json.loads(output.read_text(encoding="utf-8"))
    assert len(package["chapters"])==20
    assert package["chapters"][0]["time"]=="00:00"
    assert package["chapters"][-1]["time"]=="04:45"
    assert "[ADD VERIFIED PRIMARY SOURCES]" in package["description_template"]
    assert package["recommended_title"] in package["title_options"]
