"""Local Piper TTS adapter for English scene narration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class TTSError(RuntimeError):
    """Raised when narration is missing or Piper synthesis fails."""


def validate_scenes(scenes: list[dict[str, Any]]) -> None:
    if len(scenes) != 4:
        raise TTSError("The one-minute preset requires exactly four scenes.")
    for number, scene in enumerate(scenes, start=1):
        if not str(scene.get("narration_en", "")).strip():
            raise TTSError(f"Scene {number}: narration_en is empty.")
        if not str(scene.get("subtitle_fa", "")).strip():
            raise TTSError(f"Scene {number}: subtitle_fa is empty.")


def synthesize_storyboard(storyboard_path: str | Path, output_wav: str | Path,
                          model_path: str | Path, work_dir: str | Path | None = None,
                          speaker_id: int | None = None) -> Path:
    """Synthesize four English narration tracks and join them into one WAV."""
    payload = json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    scenes = payload.get("scenes", [])
    validate_scenes(scenes)

    model = Path(model_path)
    if not model.is_file() or not Path(str(model) + ".json").is_file():
        raise TTSError("Piper model and matching .onnx.json config file are both required.")
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise TTSError("FFmpeg and ffprobe are required to prepare synchronized narration.")

    root = Path(work_dir) if work_dir else Path(output_wav).parent / "voiceover_parts"
    root.mkdir(parents=True, exist_ok=True)
    tracks: list[Path] = []
    for index, scene in enumerate(scenes, start=1):
        target = root / f"narration_{index:02d}.wav"
        command = [
            sys.executable, "-m", "piper", "-m", str(model),
            "-f", str(target),
        ]
        if speaker_id is not None:
            command += ["--speaker", str(speaker_id)]
        result = subprocess.run(
            command, input=str(scene["narration_en"]).strip(),
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not target.is_file():
            raise TTSError(f"Piper failed on scene {index}: {result.stderr[-1500:]}")
        probe = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(target)],
            capture_output=True, text=True,
        )
        if probe.returncode != 0:
            raise TTSError(f"Could not inspect narration duration for scene {index}.")
        duration = float(probe.stdout.strip())
        if duration > 15.0:
            raise TTSError(
                f"Scene {index} narration is {duration:.1f}s; shorten the English text "
                "so it fits the 15-second scene."
            )
        synchronized = root / f"narration_{index:02d}_15s.wav"
        padded = subprocess.run(
            [ffmpeg, "-y", "-i", str(target), "-af",
             "apad=whole_dur=15,atrim=duration=15", "-c:a", "pcm_s16le",
             str(synchronized)],
            capture_output=True, text=True,
        )
        if padded.returncode != 0:
            raise TTSError(f"Could not synchronize scene {index}: {padded.stderr[-1200:]}")
        tracks.append(synchronized)

    concat = root / "voiceover_concat.txt"
    concat.write_text("".join(f"file '{track.resolve().as_posix()}'\n" for track in tracks),
                      encoding="utf-8")
    output = Path(output_wav)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c:a", "pcm_s16le", str(output)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not output.is_file():
        raise TTSError(f"Could not join narration tracks: {result.stderr[-2000:]}")
    return output
