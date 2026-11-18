"""Enforce channel-level publishing constraints for rendered video metadata."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

MIN_DURATION_SECONDS = 60
REQUIRED_FORMAT = "long_form"

def validate_video(metadata: dict) -> list[str]:
    errors: list[str] = []
    duration = metadata.get("duration_seconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        errors.append("duration_seconds must be a number")
    elif duration < MIN_DURATION_SECONDS:
        errors.append(f"duration must be at least {MIN_DURATION_SECONDS} seconds")
    if metadata.get("format") != REQUIRED_FORMAT:
        errors.append('format must be "long_form" (standard YouTube video)')
    if metadata.get("is_short") is True:
        errors.append("Shorts are disabled for primary channel uploads")
    if metadata.get("narration_language") != "en":
        errors.append('narration_language must be "en"')
    if metadata.get("subtitle_language") != "fa":
        errors.append('subtitle_language must be "fa"')
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a NextGen Tech Academy video manifest")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        metadata = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    errors = validate_video(metadata)
    if errors:
        print("REJECTED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ACCEPTED: standard long-form video policy passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
