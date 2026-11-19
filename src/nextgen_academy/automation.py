"""Cloud-first stock-footage production and private YouTube upload."""
from __future__ import annotations
import json, os
from pathlib import Path
from .config import load_dotenv
from .cloud_tts import synthesize_cloud_narration
from .cloud_writer import draft_cloud_storyboard
from .research import discover_sources
from .script import storyboard_subtitles
from .stock_media import PexelsClient
from .video_pipeline import render_video, validate_render_duration
from .youtube_package import build_youtube_package
from .youtube_upload import upload_video, validate_youtube_credentials

def run_automated(topic: str = "", output_dir: str | Path = "output", publish: bool = False) -> dict:
    load_dotenv()
    if publish:
        validate_youtube_credentials()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if not topic.strip():
        from .topic_discovery import choose_topic
        topic = choose_topic()
    sources = discover_sources(topic, limit=12)
    storyboard_path = draft_cloud_storyboard(topic, sources, root / "storyboard.json")
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    if len(scenes) != 4:
        raise RuntimeError(f"Expected exactly four storyboard scenes, received {len(scenes)}.")
    client = PexelsClient()
    jobs = []
    for index, scene in enumerate(scenes, start=1):
        query = " ".join([topic, scene.get("scene", "")]).strip()[:180]
        target = root / "clips" / f"clip_{index:03d}.mp4"
        source = client.download_clip(query, target)
        jobs.append({"index": index, "title": f"Scene {index:03d}", "duration_target_seconds": 15,
                     "local_path": str(target), "source": source, "status": "downloaded"})
    manifest = {"provider": "pexels-stock", "status": "downloaded", "target_duration_seconds": 60, "jobs": jobs}
    (root / "stock-footage-sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "video-plan.json").write_text(json.dumps({"topic": topic, "target_duration_seconds": 60, "segments": [
        {"duration_seconds": 15, "narration": scene.get("narration_en", ""), "subtitle": scene.get("subtitle_fa", "")}
        for scene in scenes]}, ensure_ascii=False, indent=2), encoding="utf-8")
    storyboard_subtitles(storyboard_path, root / "persian.srt")
    synthesize_cloud_narration(storyboard_path, root / "narration.wav", os.getenv("TTS_VOICE", "en-US-AriaNeural"))
    render_video(root / "stock-footage-sources.json", root / "final-video.mp4", root / "persian.srt", root / "narration.wav")
    actual_duration = validate_render_duration(root / "final-video.mp4")
    package_path = build_youtube_package(storyboard_path, root / "youtube-package.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["description"] = (f"Explore {topic} in this one-minute technology documentary.\n\n"
        "Stock footage credits and source links:\n" + "\n".join(
        f"- Pexels creator: {j['source'].get('creator')}; {j['source'].get('source_url')}" for j in jobs) +
        "\n\nResearch leads (review before public release):\n" +
        "\n".join(f"- {s['publisher']}: {s['title']} — {s['url']}" for s in sources[:8]))
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"topic": topic, "video": str(root / "final-video.mp4"), "metadata": str(package_path),
              "source_count": len(sources), "render_duration_seconds": actual_duration,
              "youtube_uploaded": False, "privacy_status": "not_uploaded", "footage_provider": "Pexels"}
    if publish:
        uploaded = upload_video(root / "final-video.mp4", package_path, privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private"))
        result.update({"youtube": uploaded, "youtube_uploaded": True, "privacy_status": uploaded["privacy_status"]})
    return result
