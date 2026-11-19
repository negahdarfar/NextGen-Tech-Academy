#!/usr/bin/env python3
"""Assemble ordered 16:9 clips into a long-form documentary MP4.

The script only joins local clips. It does not generate footage, narrate, translate,
upload, or publish. FFmpeg must be installed on the runner.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class DocumentaryError(RuntimeError):
    """Raised when an input or FFmpeg operation is invalid."""


def load_clip_manifest(manifest_path: str | Path) -> list[Path]:
    """Read a non-empty JSON array of clip paths relative to the manifest."""
    manifest = Path(manifest_path).resolve()
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentaryError(f"Cannot read clip manifest: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise DocumentaryError("Clip manifest must be a non-empty JSON array.")
    clips = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise DocumentaryError("Every clip entry must be a non-empty path string.")
        path = Path(item)
        if not path.is_absolute():
            path = manifest.parent / path
        path = path.resolve()
        if not path.is_file():
            raise DocumentaryError(f"Clip not found: {path}")
        clips.append(path)
    return clips


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout)[-3000:]
        raise DocumentaryError(f"FFmpeg failed: {detail}")


def assemble_documentary(
    clips_manifest: str | Path,
    output_file: str | Path,
    subtitles: str | Path | None = None,
    voiceover: str | Path | None = None,
    burn_subtitles: bool = False,
) -> Path:
    """Normalize and join clips, optionally replacing audio and muxing SRT captions."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise DocumentaryError("FFmpeg is required but was not found on PATH.")
    clips = load_clip_manifest(clips_manifest)
    output = Path(output_file).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    subtitle_path = Path(subtitles).resolve() if subtitles else None
    voice_path = Path(voiceover).resolve() if voiceover else None
    if subtitle_path and not subtitle_path.is_file():
        raise DocumentaryError(f"Subtitle file not found: {subtitle_path}")
    if voice_path and not voice_path.is_file():
        raise DocumentaryError(f"Voiceover file not found: {voice_path}")
    if burn_subtitles and not subtitle_path:
        raise DocumentaryError("--burn-subtitles requires --subtitles.")

    with tempfile.TemporaryDirectory(prefix="nextgen-documentary-") as temp_dir:
        work = Path(temp_dir)
        normalized = []
        for index, source in enumerate(clips):
            target = work / f"clip_{index:05d}.mp4"
            _run([
                ffmpeg, "-y", "-i", str(source),
                "-map", "0:v:0", "-map", "0:a:0?",
                "-vf",
                "scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-ar", "48000", "-ac", "2",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
            ])
            normalized.append(target)

        concat_file = work / "concat.txt"
        lines = []
        for path in normalized:
            escaped = str(path).replace("'", "'\\''")
            lines.append(f"file '{escaped}'\n")
        concat_file.write_text("".join(lines), encoding="utf-8")
        joined = work / "joined.mp4"
        _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i",
              str(concat_file), "-c", "copy", str(joined)])

        command = [ffmpeg, "-y", "-i", str(joined)]
        voice_index = None
        subtitle_index = None
        if voice_path:
            voice_index = 1
            command += ["-i", str(voice_path)]
        if subtitle_path:
            subtitle_index = 1 + int(bool(voice_path))
            command += ["-i", str(subtitle_path)]
        command += ["-map", "0:v:0"]
        if voice_index is not None:
            command += ["-map", f"{voice_index}:a:0", "-c:a", "aac"]
        else:
            command += ["-map", "0:a?", "-c:a", "copy"]
        if subtitle_index is not None and not burn_subtitles:
            command += ["-map", f"{subtitle_index}:s:0", "-c:s", "mov_text"]
        if burn_subtitles:
            # SRT is optional; burn-in is explicit because it requires video re-encoding.
            escaped = str(subtitle_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            command += ["-vf", f"subtitles='{escaped}'",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
        else:
            command += ["-c:v", "copy"]
        command += ["-movflags", "+faststart", str(output)]
        _run(command)

    if not output.is_file() or output.stat().st_size < 1024:
        raise DocumentaryError("FFmpeg did not produce a valid documentary output.")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", required=True, help="JSON array of clip paths, in story order")
    parser.add_argument("--output", default="documentary.mp4")
    parser.add_argument("--subtitles", help="Optional synchronized SRT file")
    parser.add_argument("--voiceover", help="Optional narration audio file replacing clip audio")
    parser.add_argument("--burn-subtitles", action="store_true",
                        help="Burn SRT captions into the video instead of muxing a soft subtitle track")
    args = parser.parse_args()
    try:
        output = assemble_documentary(
            args.clips, args.output, args.subtitles, args.voiceover, args.burn_subtitles
        )
    except DocumentaryError as exc:
        parser.exit(1, f"Documentary assembly failed: {exc}\n")
    print(f"DOCUMENTARY_ASSEMBLED {output}")
    print("Review continuity, narration sync, Persian subtitles, rights and factual accuracy before publishing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
