"""Orchestrate local English narration, Persian subtitles, and MP4 rendering."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .tts import synthesize
from .translate_srt import argos_translate, translate_srt_content
from .render import render

def run_pipeline(manifest: dict) -> dict:
    required = ("script", "piper_model", "image", "output")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError("Missing manifest fields: " + ", ".join(missing))
    build_dir = Path(manifest.get("build_dir", "build"))
    build_dir.mkdir(parents=True, exist_ok=True)
    audio_path = Path(manifest.get("narration_audio", build_dir / "narration-en.wav"))
    duration = synthesize(Path(manifest["script"]), Path(manifest["piper_model"]),
                          audio_path, executable=manifest.get("piper_executable", "piper"),
                          minimum_seconds=60.0)
    persian_srt = manifest.get("persian_srt")
    if manifest.get("english_srt"):
        english_content = Path(manifest["english_srt"]).read_text(encoding="utf-8-sig")
        translated = translate_srt_content(english_content, argos_translate)
        persian_srt = str(build_dir / "subtitles-fa.srt")
        Path(persian_srt).write_text(translated, encoding="utf-8")
    render_manifest = {
        "image": manifest["image"],
        "narration_audio": str(audio_path),
        "persian_srt": persian_srt,
        "output": manifest["output"],
    }
    result = render(render_manifest)
    result["narration_duration_seconds"] = round(duration, 2)
    result["subtitle_mode"] = "translated_offline" if manifest.get("english_srt") else ("provided" if persian_srt else "none")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local NextGen narrated-video pipeline")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = run_pipeline(manifest)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.exit(1, f"PIPELINE FAILED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
