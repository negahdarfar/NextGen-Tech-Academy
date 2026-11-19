"""Assemble the complete resumable documentary from chapter assets."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .documentary_state import load_run_state, update_chapter_state


class DocumentaryAssemblyError(RuntimeError):
    pass


def _run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise DocumentaryAssemblyError((result.stderr or result.stdout)[-3000:])
    return result.stdout.strip()


def _duration(ffprobe: str, path: Path) -> float:
    value = _run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    try:
        result = float(value)
    except ValueError as exc:
        raise DocumentaryAssemblyError(f"Invalid media duration for {path}") from exc
    if result <= 0:
        raise DocumentaryAssemblyError(f"Invalid media duration for {path}")
    return result


def _parse_srt(path: Path, offset: float, start_index: int) -> tuple[list[str], int]:
    import re
    text = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", text.strip())
    output = []
    count = start_index
    stamp = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
    def to_seconds(value: str) -> float:
        m = stamp.fullmatch(value)
        if not m:
            raise DocumentaryAssemblyError(f"Malformed SRT timestamp in {path}: {value}")
        h, minute, sec, ms = map(int, m.groups())
        return h * 3600 + minute * 60 + sec + ms / 1000
    def to_stamp(value: float) -> str:
        millis = max(0, int(round(value * 1000)))
        h, millis = divmod(millis, 3600000)
        minute, millis = divmod(millis, 60000)
        sec, millis = divmod(millis, 1000)
        return f"{h:02d}:{minute:02d}:{sec:02d},{millis:03d}"
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        times = lines[1].split(" --> ")
        if len(times) != 2:
            raise DocumentaryAssemblyError(f"Malformed SRT cue in {path}")
        begin, end = to_seconds(times[0]) + offset, to_seconds(times[1]) + offset
        count += 1
        output.append(f"{count}\n{to_stamp(begin)} --> {to_stamp(end)}\n" + "\n".join(lines[2:]))
    return output, count


def assemble_documentary_run(state_path: str | Path,
                              output_file: str | Path = "output/documentary/final-documentary.mp4") -> dict[str, Any]:
    state = load_run_state(state_path)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise DocumentaryAssemblyError("FFmpeg and ffprobe are required.")
    if not state.get("chapters"):
        raise DocumentaryAssemblyError("Run has no chapters.")
    chapter_inputs = []
    for chapter in state["chapters"]:
        outputs = chapter.get("outputs", {})
        required = ("narration_audio", "persian_subtitles", "visual_manifest")
        missing = [key for key in required if not outputs.get(key)]
        if missing:
            raise DocumentaryAssemblyError(f"Chapter {chapter['chapter']} missing outputs: {', '.join(missing)}")
        audio, subtitles, manifest = (Path(outputs[key]) for key in required)
        if not audio.is_file() or not subtitles.is_file() or not manifest.is_file():
            raise DocumentaryAssemblyError(f"Chapter {chapter['chapter']} has missing output files.")
        visual = json.loads(manifest.read_text(encoding="utf-8"))
        shots = visual.get("shots", [])
        if visual.get("status") != "complete" or not shots:
            raise DocumentaryAssemblyError(f"Chapter {chapter['chapter']} visual manifest is incomplete.")
        for shot in shots:
            clip = Path(shot.get("local_path", ""))
            if not clip.is_file() or clip.stat().st_size < 1024:
                raise DocumentaryAssemblyError(f"Chapter {chapter['chapter']} has a missing visual clip.")
        chapter_inputs.append((chapter, audio, subtitles, shots))

    target_seconds = float(state.get("target_duration_seconds") or 0)
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nextgen-longform-") as temp:
        work = Path(temp)
        video_files, audio_files, subtitle_blocks = [], [], []
        timeline_offset = 0.0
        cue_index = 0
        for chapter, audio, subtitles, shots in chapter_inputs:
            chapter_duration = _duration(ffprobe, audio)
            clip_duration = chapter_duration / len(shots)
            normalized_audio = work / f"audio-{chapter['chapter']:02d}.wav"
            _run([ffmpeg, "-y", "-i", str(audio), "-vn", "-ac", "2", "-ar", "48000",
                  "-c:a", "pcm_s16le", str(normalized_audio)])
            audio_files.append(normalized_audio)
            for shot_index, shot in enumerate(shots, 1):
                clip = Path(shot["local_path"])
                normalized = work / f"video-{chapter['chapter']:02d}-{shot_index:03d}.mp4"
                _run([ffmpeg, "-y", "-stream_loop", "-1", "-i", str(clip), "-an",
                      "-t", f"{clip_duration:.4f}",
                      "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                             "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p",
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                      "-movflags", "+faststart", str(normalized)])
                video_files.append(normalized)
            blocks, cue_index = _parse_srt(subtitles, timeline_offset, cue_index)
            subtitle_blocks.extend(blocks)
            timeline_offset += chapter_duration

        concat_video = work / "video-list.txt"
        concat_video.write_text("".join(f"file '{p.as_posix()}'\n" for p in video_files), encoding="utf-8")
        silent = work / "picture.mp4"
        _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_video),
              "-c", "copy", str(silent)])
        concat_audio = work / "audio-list.txt"
        concat_audio.write_text("".join(f"file '{p.as_posix()}'\n" for p in audio_files), encoding="utf-8")
        full_audio = work / "narration.wav"
        _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_audio),
              "-c:a", "pcm_s16le", str(full_audio)])
        srt = work / "persian-full.srt"
        srt.write_text("\n\n".join(subtitle_blocks) + "\n", encoding="utf-8-sig")
        _run([ffmpeg, "-y", "-i", str(silent), "-i", str(full_audio), "-i", str(srt),
              "-map", "0:v:0", "-map", "1:a:0", "-map", "2:0",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              "-c:s", "mov_text", "-movflags", "+faststart", "-shortest", str(output)])

    actual = _duration(ffprobe, output)
    tolerance = max(30.0, target_seconds * 0.20)
    if target_seconds and abs(actual - target_seconds) > tolerance:
        output.unlink(missing_ok=True)
        raise DocumentaryAssemblyError(
            f"Rendered duration {actual:.1f}s differs from blueprint {target_seconds:.1f}s "
            f"by more than allowed {tolerance:.1f}s; output rejected."
        )
    for chapter, *_ in chapter_inputs:
        update_chapter_state(state_path, int(chapter["chapter"]), status="assembled",
                             outputs={"final_documentary": str(output)})
    return {"status": "assembled_pending_human_review", "output": str(output),
            "duration_seconds": round(actual, 2), "target_duration_seconds": target_seconds,
            "chapter_count": len(chapter_inputs), "visual_shot_count": len(video_files),
            "resolution": "1920x1080", "frame_rate": 30,
            "subtitle_track": "Persian soft subtitle (SRT converted to mov_text)",
            "public_upload": False, "human_review_required": True}
