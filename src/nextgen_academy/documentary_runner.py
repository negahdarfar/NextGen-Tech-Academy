"""Explicitly confirmed, resumable long-form production orchestrator.

No YouTube upload is performed by this command.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .documentary_assembly import assemble_documentary_run
from .documentary_chapters import process_documentary_chapter
from .documentary_media import synthesize_documentary_chapter
from .documentary_metadata import build_documentary_metadata
from .documentary_state import initialize_documentary_run, load_run_state, update_chapter_state
from .documentary_visuals import generate_chapter_visuals


class DocumentaryRunError(RuntimeError):
    pass


def _chapter(state_path: Path, number: int) -> dict[str, Any]:
    state = load_run_state(state_path)
    return next(item for item in state["chapters"] if int(item["chapter"]) == number)


def produce_documentary(
    topic: str,
    minutes: int = 15,
    state_path: str | Path = "output/documentary-run.json",
    output_dir: str | Path = "output/documentary",
    provider: str = "auto",
    voice: str = "en-US-AriaNeural",
    confirm_provider_requests: bool = False,
    allow_agnes_potential_cost: bool = False,
) -> dict[str, Any]:
    """Run research → script → TTS/SRT → resumable visuals → assembly; never upload."""
    if not confirm_provider_requests:
        raise DocumentaryRunError(
            "External LLM, TTS and visual-provider requests require --confirm-provider-requests. "
            "No provider request was sent."
        )
    if provider == "agnes" and not allow_agnes_potential_cost:
        raise DocumentaryRunError(
            "Agnes may be chargeable if its temporary promotion has ended; check pricing and explicitly enable the separate cost confirmation."
        )
    if provider not in {"auto", "agnes", "pexels"}:
        raise DocumentaryRunError("Provider must be auto, pexels, or agnes.")
    if provider in {"auto", "pexels"} and not os.getenv("PEXELS_API_KEY", "").strip():
        raise DocumentaryRunError("Zero-budget auto/Pexels mode requires PEXELS_API_KEY; no LLM or TTS request was sent.")
    if provider == "agnes" and not os.getenv("AGNES_API_KEY", "").strip():
        raise DocumentaryRunError("AGNES_API_KEY is missing; no external request was sent.")
    free_llm_ready = bool(os.getenv("FREELLMAPI_CLOUD_BASE_URL", "").strip()) and bool(os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip())
    if not free_llm_ready:
        raise DocumentaryRunError("FreeLLMAPI is the sole LLM gateway; configure its cloud URL and API key. No external request was sent.")
    os.environ["LLM_PROVIDER_ORDER"] = "freellmapi"
    if not confirm_provider_requests:
        raise DocumentaryRunError(
            "External LLM, TTS and visual-provider requests require --confirm-provider-requests. "
            "No provider request was sent."
        )

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    state_file = Path(state_path)
    if not state_file.exists():
        if not topic.strip():
            raise DocumentaryRunError("A topic is required to initialize a new documentary run.")
        from .documentary_plan import build_documentary_plan, save_documentary_plan
        plan = build_documentary_plan(topic, minutes)
        plan_file = root / "documentary-plan.json"
        save_documentary_plan(plan, plan_file)
        initialize_documentary_run(plan_file, state_file)

    state = load_run_state(state_file)
    if int(state.get("target_duration_seconds") or 0) != minutes * 60:
        raise DocumentaryRunError("The requested minutes do not match the existing run. Resume with the original duration.")
    if topic.strip() and state.get("topic") != topic.strip():
        raise DocumentaryRunError("The supplied topic does not match the existing run manifest.")
    if int(state.get("target_duration_seconds") or 0) not in (900, 1800, 3600):
        raise DocumentaryRunError("Run manifest duration must be 15, 30, or 60 minutes.")

    completed = []
    for snapshot in state["chapters"]:
        number = int(snapshot["chapter"])
        try:
            current = _chapter(state_file, number)["status"]
            script_file = root / f"chapter-{number:02d}-script.json"
            if current in {"planned", "researched"}:
                process_documentary_chapter(state_file, number, root)
                current = _chapter(state_file, number)["status"]
            if current == "scripted":
                synthesize_documentary_chapter(
                    state_file, number, script_file, root / "media", voice
                )
                current = _chapter(state_file, number)["status"]
            if current in {"narrated", "assembled"}:
                generate_chapter_visuals(
                    state_file,
                    number,
                    script_file,
                    root / "visuals",
                    provider,
                    allow_agnes_potential_cost=allow_agnes_potential_cost,
                )
            elif current == "reviewed":
                outputs = _chapter(state_file, number).get("outputs", {})
                if not all(
                    outputs.get(key) and Path(outputs[key]).is_file()
                    for key in ("narration_audio", "persian_subtitles", "visual_manifest")
                ):
                    raise DocumentaryRunError(
                        f"Reviewed chapter {number} is missing one or more production assets."
                    )
            completed.append(number)
        except Exception as exc:
            update_chapter_state(state_file, number, error=str(exc))
            raise DocumentaryRunError(
                f"Chapter {number} stopped safely at its last checkpoint: {exc}"
            ) from exc

    result = assemble_documentary_run(state_file, root / "final-documentary.mp4")
    metadata_path = build_documentary_metadata(
        state_file, root / "youtube-package.json", result["chapter_timeline"]
    )
    result["metadata_path"] = str(metadata_path)
    result.update({
        "topic": state["topic"],
        "completed_chapters": completed,
        "state_path": str(state_file),
        "upload_performed": False,
        "public_upload": False,
    })
    return result
