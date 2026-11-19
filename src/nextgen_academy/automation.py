"""Cloud-first long-form stock-footage production and private YouTube upload."""
from __future__ import annotations
import json, os
from pathlib import Path
from .config import load_dotenv
from .cloud_tts import synthesize_cloud_narration
from .cloud_writer import draft_cloud_storyboard
from .research import discover_sources
from .evidence_audit import enrich_sources, write_evidence_audit
from .video_pipeline import render_video, validate_render_duration, write_srt
from .stock_media import PexelsClient
from .youtube_package import build_youtube_package
from .youtube_upload import upload_video, validate_youtube_credentials

def run_automated(topic: str = "", output_dir: str | Path = "output", publish: bool = False,
                  duration_minutes: int = 5) -> dict:
    load_dotenv()
    if duration_minutes not in range(3, 11):
        raise ValueError("duration_minutes must be between 3 and 10.")
    if publish:
        validate_youtube_credentials()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if not topic.strip():
        from .topic_discovery import choose_topic
        topic = choose_topic()
    target_seconds = duration_minutes * 60
    scene_duration = 15
    scene_count = target_seconds // scene_duration

    # Fetch source pages before drafting. A failed fetch is recorded but does not
    # silently convert an RSS lead into verified evidence.
    discovered = discover_sources(topic, limit=20)
    sources = enrich_sources(discovered)
    (root / "research-sources-audited.json").write_text(
        json.dumps({"topic": topic, "sources": sources}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    storyboard_path = draft_cloud_storyboard(topic, sources, root / "storyboard.json", target_seconds)
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    if len(scenes) != scene_count:
        raise RuntimeError(f"Expected {scene_count} scenes; received {len(scenes)}.")

    # This report measures page reachability and word overlap only. It never
    # marks a claim true; manual source review is still mandatory.
    write_evidence_audit(storyboard, sources, root / "evidence-audit.json")

    client = PexelsClient()
    jobs = []
    for index, scene in enumerate(scenes, 1):
        query = " ".join([topic, scene.get("scene", "")]).strip()[:180]
        target = root / "clips" / f"clip_{index:03d}.mp4"
        source = client.download_clip(query, target, min_duration=scene_duration)
        jobs.append({
            "index": index,
            "title": scene.get("title", f"Scene {index:03d}"),
            "duration_target_seconds": scene_duration,
            "local_path": str(target),
            "source": source,
            "status": "downloaded",
        })
    manifest = {
        "provider": "pexels-stock",
        "status": "downloaded",
        "target_duration_seconds": target_seconds,
        "jobs": jobs,
    }
    (root / "stock-footage-sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    segments = [
        {"duration_seconds": scene_duration, "narration": scene["narration_en"],
         "subtitle": scene["subtitle_fa"]}
        for scene in scenes
    ]
    (root / "video-plan.json").write_text(
        json.dumps({"topic": topic, "target_duration_seconds": target_seconds, "segments": segments},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_srt(segments, root / "persian.srt")
    synthesize_cloud_narration(
        storyboard_path, root / "narration.wav", os.getenv("TTS_VOICE", "en-US-AriaNeural"), scene_duration
    )
    render_video(
        root / "stock-footage-sources.json", root / "final-video.mp4",
        root / "persian.srt", root / "narration.wav", scene_duration
    )
    actual_duration = validate_render_duration(
        root / "final-video.mp4", target_seconds - 5, target_seconds + 10
    )
    package_path = build_youtube_package(storyboard_path, root / "youtube-package.json")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    credits = "\n".join(
        f"- Pexels creator: {job['source'].get('creator')}; {job['source'].get('source_url')}"
        for job in jobs
    )
    refs = "\n".join(
        f"- {source['publisher']}: {source['title']} — {source['url']}"
        for source in sources[:12]
    )
    package["description"] = (
        f"Explore {topic} in this {duration_minutes}-minute technology documentary.\n\n"
        "Stock footage credits and source links:\n" + credits +
        "\n\nResearch leads (not independently verified; review before public release):\n" + refs
    )
    package["recommended_title"] = package["recommended_title"][:100]
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "topic": topic,
        "video": str(root / "final-video.mp4"),
        "metadata": str(package_path),
        "source_count": len(sources),
        "reachable_source_count": sum(s.get("audit", {}).get("status") == "reachable" for s in sources),
        "scene_count": scene_count,
        "target_duration_seconds": target_seconds,
        "render_duration_seconds": actual_duration,
        "evidence_audit": str(root / "evidence-audit.json"),
        "youtube_uploaded": False,
        "privacy_status": "not_uploaded",
        "footage_provider": "Pexels",
        "narration": "English",
        "subtitles": "Persian",
        "human_fact_check_required": True,
    }
    if publish:
        uploaded = upload_video(
            root / "final-video.mp4", package_path,
            privacy_status=os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
        )
        result.update({
            "youtube": uploaded,
            "youtube_uploaded": True,
            "privacy_status": uploaded["privacy_status"],
        })
    return result
