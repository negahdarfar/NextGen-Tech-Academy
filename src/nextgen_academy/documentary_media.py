"""Chapter-level cloud narration and approximate Persian subtitle timing.

Uses the optional Edge TTS CLI. Provider availability/terms can change; run explicitly.
Subtitle timing is estimated from Persian sentence lengths and must be reviewed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .documentary_state import load_run_state, update_chapter_state


class DocumentaryMediaError(RuntimeError):
    pass


def _sentences(text: str) -> list[str]:
    import re
    return [part.strip() for part in re.split(r"(?<=[.!?؟۔])\s+", text.strip()) if part.strip()]


def _stamp(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write_estimated_srt(text: str, duration: float, target: Path) -> int:
    sentences = _sentences(text)
    if not sentences:
        raise DocumentaryMediaError("Persian translation contains no subtitle text.")
    weights = [max(1, len(item)) for item in sentences]
    total = sum(weights)
    cursor = 0.0
    rows = []
    for index, (sentence, weight) in enumerate(zip(sentences, weights), 1):
        end = duration if index == len(sentences) else cursor + duration * weight / total
        rows.append(f"{index}\n{_stamp(cursor)} --> {_stamp(end)}\n{sentence}\n")
        cursor = end
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(rows), encoding="utf-8-sig")
    return len(rows)


def synthesize_documentary_chapter(state_path: str | Path, chapter_number: int,
                                   script_path: str | Path,
                                   output_dir: str | Path = "output/documentary/media",
                                   voice: str = "en-US-AriaNeural") -> dict[str, Any]:
    """Create chapter MP3 + estimated Persian SRT, then checkpoint the narrated stage."""
    state = load_run_state(state_path)
    chapter = next((item for item in state["chapters"] if item["chapter"] == chapter_number), None)
    if chapter is None:
        raise ValueError(f"Unknown chapter number: {chapter_number}")
    if chapter["status"] != "scripted":
        raise DocumentaryMediaError("Chapter must be scripted before narration.")
    script_file = Path(script_path)
    if not script_file.is_file():
        raise FileNotFoundError(script_file)
    script = json.loads(script_file.read_text(encoding="utf-8"))
    if int(script.get("chapter", -1)) != chapter_number:
        raise DocumentaryMediaError("Script chapter number does not match the requested chapter.")
    narration = str(script.get("narration_en", "")).strip()
    translation = str(script.get("subtitle_fa", "")).strip()
    if not narration or not translation:
        raise DocumentaryMediaError("Both English narration and Persian translation are required.")
    edge_tts = shutil.which("edge-tts")
    ffprobe = shutil.which("ffprobe")
    if not edge_tts or not ffprobe:
        raise DocumentaryMediaError("Install the cloud extra and FFmpeg tools (edge-tts, ffprobe).")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    audio = root / f"chapter-{chapter_number:02d}-en.mp3"
    subtitles = root / f"chapter-{chapter_number:02d}-fa.srt"
    result = subprocess.run([edge_tts, "--voice", voice, "--text", narration,
                             "--write-media", str(audio)], capture_output=True, text=True)
    if result.returncode or not audio.is_file() or audio.stat().st_size < 1024:
        raise DocumentaryMediaError(f"Edge TTS failed: {result.stderr[-1200:]}")
    probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
                           capture_output=True, text=True)
    if probe.returncode:
        raise DocumentaryMediaError(f"Could not inspect generated audio: {probe.stderr[-1000:]}")
    try:
        duration = float(probe.stdout.strip())
    except ValueError as exc:
        raise DocumentaryMediaError("ffprobe returned an invalid audio duration.") from exc
    if duration <= 0:
        raise DocumentaryMediaError("Generated audio has an invalid duration.")
    cue_count = _write_estimated_srt(translation, duration, subtitles)
    update_chapter_state(state_path, chapter_number, status="narrated",
                         outputs={"narration_audio": str(audio), "persian_subtitles": str(subtitles)})
    return {"chapter": chapter_number, "status": "narrated", "audio_path": str(audio),
            "subtitle_path": str(subtitles), "audio_duration_seconds": round(duration, 2),
            "subtitle_cues": cue_count, "subtitle_timing": "estimated_from_persian_sentence_lengths",
            "human_timing_review_required": True}
