"""Pick a technology topic from recent RSS headlines."""
from __future__ import annotations

from .research import discover_sources


def choose_topic() -> str:
    candidates = []
    for query in ("artificial intelligence technology", "robotics breakthrough",
                  "space technology", "biotechnology innovation"):
        try:
            candidates.extend(discover_sources(query, limit=4))
        except Exception:
            continue
    if not candidates:
        raise RuntimeError("Could not discover a current topic from RSS sources.")
    # Favor the newest discovered headlines while avoiding a hard-coded claim.
    best = candidates[0]["title"]
    return best[:180]
