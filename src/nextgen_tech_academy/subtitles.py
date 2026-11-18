"""Dependency-free SRT validation helpers for English narration / Persian subtitles."""
from __future__ import annotations
import re
from pathlib import Path

TIMESTAMP = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")

def timestamp_ms(value: str) -> int:
    match = TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, millis = map(int, match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError(f"Out-of-range SRT timestamp: {value!r}")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis

def validate_srt(content: str) -> list[str]:
    """Return structural/timing errors; does not assess translation quality."""
    errors: list[str] = []
    blocks = re.split(r"\n\s*\n", content.strip()) if content.strip() else []
    if not blocks:
        return ["subtitle file is empty"]
    previous_end = -1
    for index, block in enumerate(blocks, start=1):
        lines = block.replace("\r\n", "\n").split("\n")
        if len(lines) < 3:
            errors.append(f"cue {index}: expected index, timing, and subtitle text")
            continue
        if lines[0].strip() != str(index):
            errors.append(f"cue {index}: sequence number should be {index}")
        timing = lines[1].split("-->")
        if len(timing) != 2:
            errors.append(f"cue {index}: invalid timing line")
            continue
        try:
            start, end = map(timestamp_ms, timing)
        except ValueError as exc:
            errors.append(f"cue {index}: {exc}")
            continue
        if end <= start:
            errors.append(f"cue {index}: end must be after start")
        if start < previous_end:
            errors.append(f"cue {index}: overlaps or precedes the previous cue")
        if not any(line.strip() for line in lines[2:]):
            errors.append(f"cue {index}: subtitle text is empty")
        previous_end = end
    return errors

def validate_srt_file(path: str | Path) -> list[str]:
    return validate_srt(Path(path).read_text(encoding="utf-8-sig"))
