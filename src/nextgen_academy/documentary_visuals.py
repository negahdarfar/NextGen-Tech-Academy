"""Resumable chapter visual generation with explicit free-provider routing."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .agnes_video import generate_scene_video
from .documentary_state import load_run_state, update_chapter_state
from .pexels import download_scene_video


class DocumentaryVisualError(RuntimeError):
    pass


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def generate_chapter_visuals(state_path: str | Path, chapter_number: int,
                             script_path: str | Path,
                             output_dir: str | Path = "output/documentary/visuals",
                             provider: str = "auto") -> dict[str, Any]:
    """Generate/restore each shot; persist provenance after every successful asset."""
    if provider not in {"auto", "agnes", "pexels"}:
        raise ValueError("provider must be auto, agnes or pexels")
    state = load_run_state(state_path)
    chapter = next((item for item in state["chapters"] if item["chapter"] == chapter_number), None)
    if chapter is None:
        raise ValueError(f"Unknown chapter number: {chapter_number}")
    if chapter["status"] not in {"narrated", "assembled"}:
        raise DocumentaryVisualError("Generate visuals after the chapter has a completed narration stage.")
    script_file = Path(script_path)
    if not script_file.is_file():
        raise FileNotFoundError(script_file)
    script = json.loads(script_file.read_text(encoding="utf-8"))
    if int(script.get("chapter", -1)) != chapter_number:
        raise DocumentaryVisualError("Script chapter number does not match the requested chapter.")
    shots = script.get("visual_shots")
    if not isinstance(shots, list) or not shots:
        raise DocumentaryVisualError("The chapter script has no visual_shots. Regenerate its script.")
    clip_seconds = int(script.get("visual_clip_target_seconds", chapter.get("visual_clip_target_seconds", 12)))
    if clip_seconds not in (4, 6, 8, 10, 12):
        raise DocumentaryVisualError("Unsupported clip target in chapter script.")
    agnes_key = os.getenv("AGNES_API_KEY", "").strip()
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    if provider == "agnes" and not agnes_key:
        raise DocumentaryVisualError("AGNES_API_KEY is missing; no visual request was sent.")
    if provider == "pexels" and not pexels_key:
        raise DocumentaryVisualError("PEXELS_API_KEY is missing; no visual request was sent.")
    if provider == "auto" and not (agnes_key or pexels_key):
        raise DocumentaryVisualError("Configure AGNES_API_KEY or PEXELS_API_KEY. No paid fallback is enabled.")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"chapter-{chapter_number:02d}-assets.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("chapter") != chapter_number or manifest.get("script_path") != str(script_file):
            raise DocumentaryVisualError("Existing asset manifest belongs to a different script; use a new output directory.")
    else:
        manifest = {"chapter": chapter_number, "script_path": str(script_file),
                    "clip_target_seconds": clip_seconds, "status": "in_progress", "shots": []}
    completed = {int(item["shot"]): item for item in manifest["shots"]
                 if item.get("status") == "downloaded" and
                 Path(item.get("local_path", "")).is_file() and
                 Path(item.get("local_path", "")).stat().st_size > 1024}
    saved = []
    for index, shot in enumerate(shots, 1):
        prompt = str(shot.get("visual_prompt", "")).strip() if isinstance(shot, dict) else ""
        if not prompt:
            raise DocumentaryVisualError(f"Visual shot {index} has an empty prompt.")
        if index in completed:
            saved.append(completed[index])
            continue
        target = root / f"chapter-{chapter_number:02d}-shot-{index:03d}.mp4"
        result = None
        errors = []
        order = ([provider] if provider != "auto" else
                 (["agnes", "pexels"] if agnes_key and pexels_key else
                  ["agnes"] if agnes_key else ["pexels"]))
        for selected in order:
            try:
                if selected == "agnes":
                    result = generate_scene_video(prompt, target, seconds=clip_seconds)
                else:
                    result = download_scene_video(prompt, target, min_duration=clip_seconds)
                    result["provider"] = "pexels"
                break
            except Exception as exc:
                errors.append(f"{selected}: {str(exc)[:500]}")
                if provider != "auto":
                    raise DocumentaryVisualError("; ".join(errors)) from exc
        if result is None:
            raise DocumentaryVisualError(f"Shot {index} failed: " + " | ".join(errors))
        local_path = Path(result.get("local_path", target))
        if not local_path.is_file() or local_path.stat().st_size < 1024:
            raise DocumentaryVisualError(f"Provider did not create a valid clip for shot {index}.")
        item = {"shot": index, "visual_prompt": prompt, "status": "downloaded",
                "local_path": str(local_path), "provider": result.get("provider"),
                "model": result.get("model"), "video_id": result.get("video_id"),
                "source_url": result.get("source_url"), "photographer": result.get("photographer"),
                "duration_seconds": result.get("duration_seconds"),
                "resolution": result.get("resolution"), "fallback_errors": errors}
        completed[index] = item
        saved.append(item)
        manifest["shots"] = [completed[key] for key in sorted(completed)]
        manifest["status"] = "in_progress"
        _save(manifest_path, manifest)
    manifest["shots"] = [completed[key] for key in sorted(completed)]
    manifest["status"] = "complete" if len(manifest["shots"]) == len(shots) else "in_progress"
    manifest["providers_used"] = sorted({item.get("provider", "unknown") for item in manifest["shots"]})
    _save(manifest_path, manifest)
    update_chapter_state(state_path, chapter_number,
                         outputs={"visual_manifest": str(manifest_path)})
    return {"chapter": chapter_number, "status": manifest["status"],
            "shot_count": len(manifest["shots"]), "providers_used": manifest["providers_used"],
            "manifest_path": str(manifest_path),
            "resumed_existing_shots": resumed_count}
