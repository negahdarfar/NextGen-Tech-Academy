"""Estimate narration length before recording or TTS generation."""
from __future__ import annotations
import argparse
from pathlib import Path

DEFAULT_WORDS_PER_MINUTE = 145

def estimate_duration_seconds(script: str, words_per_minute: int = DEFAULT_WORDS_PER_MINUTE) -> int:
    if words_per_minute <= 0:
        raise ValueError("words_per_minute must be positive")
    words = len(script.split())
    if words == 0:
        return 0
    return round(words * 60 / words_per_minute)

def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate spoken script duration")
    parser.add_argument("script", type=Path)
    parser.add_argument("--wpm", type=int, default=DEFAULT_WORDS_PER_MINUTE)
    args = parser.parse_args()
    seconds = estimate_duration_seconds(args.script.read_text(encoding="utf-8"), args.wpm)
    print(f"Estimated narration: {seconds // 60}m {seconds % 60}s ({seconds} seconds)")
    if seconds < 60:
        print("REJECTED: expand the script to at least 60 seconds.")
        return 1
    print("PASS: estimated narration meets the 60-second minimum.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
