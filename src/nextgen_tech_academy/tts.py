"""Offline narration adapter for the Piper command-line TTS engine."""
from __future__ import annotations
import argparse
import shutil
import subprocess
import wave
from pathlib import Path

def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        if rate <= 0:
            raise ValueError("Invalid WAV sample rate")
        return audio.getnframes() / rate

def synthesize(script_path: Path, model_path: Path, output_path: Path,
               executable: str = "piper", minimum_seconds: float = 60.0) -> float:
    if not shutil.which(executable):
        raise RuntimeError("Piper CLI not found. Install Piper and add it to PATH.")
    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Piper voice model not found: {model_path}")
    text = script_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Narration script is empty")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([executable, "--model", str(model_path), "--output_file", str(output_path)],
                   input=text, text=True, check=True)
    duration = wav_duration(output_path)
    if duration < minimum_seconds:
        output_path.unlink(missing_ok=True)
        raise ValueError(f"Generated narration is {duration:.1f}s; minimum is {minimum_seconds:.0f}s")
    return duration

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate offline English narration with Piper")
    parser.add_argument("script", type=Path)
    parser.add_argument("--model", required=True, type=Path, help="Downloaded Piper .onnx voice model")
    parser.add_argument("--output", default=Path("build/narration-en.wav"), type=Path)
    parser.add_argument("--minimum-seconds", default=60.0, type=float)
    args = parser.parse_args()
    try:
        duration = synthesize(args.script, args.model, args.output,
                              minimum_seconds=args.minimum_seconds)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"TTS FAILED: {exc}\n")
    print(f"NARRATION READY: {args.output} ({duration:.1f}s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
