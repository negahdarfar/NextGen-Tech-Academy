"""Editorial quality gate for a four-scene, one-minute video script."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def review_storyboard(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    sources = data.get("sources", [])
    claims = data.get("claims", [])
    errors: list[str] = []
    warnings: list[str] = []

    if len(scenes) != 4:
        errors.append("Storyboard must contain exactly four scenes.")
    for i, scene in enumerate(scenes, 1):
        english = str(scene.get("narration_en", "")).strip()
        persian = str(scene.get("subtitle_fa", "")).strip()
        if not english:
            errors.append(f"Scene {i}: English narration is missing.")
        if not persian:
            errors.append(f"Scene {i}: Persian subtitle is missing.")
        count = len(english.split())
        if english and count < 20:
            warnings.append(f"Scene {i}: only {count} English words; narration may leave silence.")
        if count > 38:
            warnings.append(f"Scene {i}: {count} English words may be too long for 15 seconds.")

    valid_source_ids: set[str] = set()
    for i, source in enumerate(sources, 1):
        source_id = str(source.get("id", "")).strip()
        url = str(source.get("url", "")).strip()
        parsed = urlparse(url)
        if not source_id or parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"Source {i}: requires a unique id and valid HTTPS URL.")
            continue
        if source_id in valid_source_ids:
            errors.append(f"Source {i}: duplicate source id '{source_id}'.")
        valid_source_ids.add(source_id)
        if not source.get("checked", False):
            warnings.append(f"Source '{source_id}' is not marked as manually checked.")
        if not str(source.get("publisher", "")).strip():
            warnings.append(f"Source '{source_id}' has no publisher name.")

    if len(valid_source_ids) < 2:
        errors.append("At least two valid HTTPS sources are required.")
    if not claims:
        errors.append("Add factual claims and map each to supporting source_ids.")
    for i, claim in enumerate(claims, 1):
        text = str(claim.get("text", "")).strip()
        refs = claim.get("source_ids", [])
        if not text:
            errors.append(f"Claim {i}: claim text is empty.")
        if not refs or any(ref not in valid_source_ids for ref in refs):
            errors.append(f"Claim {i}: source_ids must reference valid sources.")

    return {
        "topic": data.get("topic", ""),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "source_count": len(valid_source_ids),
        "claim_count": len(claims),
        "scene_word_counts": [len(str(s.get("narration_en", "")).split()) for s in scenes],
        "note": "Automated structure checks only; a human must open sources and verify each claim.",
    }


def write_review_report(storyboard_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    report = review_storyboard(storyboard_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
