"""Optional Edge neural TTS adapter for cloud runners; provider terms may change."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class CloudTTSError(RuntimeError):
    pass


def synthesize_cloud_narration(storyboard_path: str | Path, output_wav: str | Path,
                               voice: str = "en-US-AriaNeural") -> Path:
    payload = json.loads(Path(storyboard_path).read_text(encoding="utf-8"))
    scenes = payload.get("scenes", [])
    if len(scenes) != 4:
        raise CloudTTSError("Exactly four scenes are required.")
    if not shutil.which("ffmpeg"):
        raise CloudTTSError("FFmpeg is required.")
    root = Path(output_wav).parent / "voice_parts"
    root.mkdir(parents=True, exist_ok=True)
    tracks = []
    for index, scene in enumerate(scenes, 1):
        text = str(scene.get("narration_en", "")).strip()
        if not text:
            raise CloudTTSError(f"Scene {index} has no English narration.")
        mp3 = root / f"scene_{index:02d}.mp3"
        wav = root / f"scene_{index:02d}_15s.wav"
        result = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice,
                                 "--text", text, "--write-media", str(mp3)],
                                capture_output=True, text=True)
        if result.returncode or not mp3.is_file():
            raise CloudTTSError(f"Edge TTS failed on scene {index}: {result.stderr[-1000:]}")
        result = subprocess.run(["ffmpeg", "-y", "-i", str(mp3), "-af",
                                 "apad=whole_dur=15,atrim=duration=15",
                                 "-ar", "44100", "-ac", "2", str(wav)],
                                capture_output=True, text=True)
        if result.returncode:
            raise CloudTTSError(f"Audio normalization failed: {result.stderr[-1000:]}")
        tracks.append(wav)
    concat = root / "concat.txt"
    concat.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in tracks), encoding="utf-8")
    output = Path(output_wav)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                             str(concat), "-c:a", "pcm_s16le", str(output)],
                            capture_output=True, text=True)
    if result.returncode:
        raise CloudTTSError(f"Could not join narration: {result.stderr[-1500:]}")
    return output
