"""Render a narrated still-image MP4 using local FFmpeg tools.

This is a minimal, offline-friendly first renderer: one visual background, one
narration track, and optional soft Persian SRT subtitles. It is not a full
multi-scene editor.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path

def _require_file(value: str, field: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"{field} does not exist or is not a file: {path}")
    return path.resolve()

def build_ffmpeg_command(image: Path, audio: Path, output: Path, subtitles: Path | None = None) -> list[str]:
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-framerate", "30", "-i", str(image),
        "-i", str(audio),
    ]
    if subtitles:
        cmd += ["-i", str(subtitles)]
    cmd += ["-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    if subtitles:
        cmd += ["-map", "2:s:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=fas"]
    cmd += ["-movflags", "+faststart", str(output)]
    return cmd

def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())

def render(manifest: dict) -> dict:
    image = _require_file(manifest["image"], "image")
    audio = _require_file(manifest["narration_audio"], "narration_audio")
    subtitle_value = manifest.get("persian_srt")
    subtitles = _require_file(subtitle_value, "persian_srt") if subtitle_value else None
    output = Path(manifest["output"]).expanduser()
    if output.suffix.lower() != ".mp4":
        raise ValueError("output must use .mp4 extension")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe must be installed and available on PATH")
    cmd = build_ffmpeg_command(image, audio, output.resolve(), subtitles)
    subprocess.run(cmd, check=True)
    duration = probe_duration(output.resolve())
    if duration < 60:
        output.unlink(missing_ok=True)
        raise ValueError(f"Rendered video is only {duration:.1f}s; minimum is 60s")
    return {"output": str(output.resolve()), "duration_seconds": round(duration, 2)}

def main() -> int:
    parser = argparse.ArgumentParser(description="Render a narrated long-form MP4 locally with FFmpeg")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = render(manifest)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"RENDER FAILED: {exc}\n")
    print(f"RENDERED: {result['output']} ({result['duration_seconds']} seconds)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
