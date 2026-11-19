"""Command-line entry point for the one-minute video production workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings, load_dotenv
from .ollama_writer import draft_storyboard
from .planning import build_plan, plan_as_dict
from .script import default_storyboard, save_script_package, storyboard_subtitles
from .script_review import write_review_report
from .tts import synthesize_storyboard
from .video_pipeline import poll_and_download, render_video
from .video_segments import VideoSegment, build_segments, segments_as_dicts
from .youtube_package import build_youtube_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nextgen-academy",
        description="Produce one-minute, 16:9 technology documentary videos.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    documentary = sub.add_parser("documentary-plan", help="create a long-form documentary production blueprint")
    documentary.add_argument("--topic", required=True)
    documentary.add_argument("--minutes", type=int, choices=(15, 30, 60), default=15)
    documentary.add_argument("--clip-seconds", type=int, choices=(4, 6, 8, 10, 12), default=12)
    documentary.add_argument("--output", default="output/documentary-plan.json")

    run_init = sub.add_parser("documentary-init", help="initialize a resumable documentary run from a blueprint")
    run_init.add_argument("--plan", default="output/documentary-plan.json")
    run_init.add_argument("--state", default="output/documentary-run.json")

    run_progress = sub.add_parser("documentary-progress", help="record progress for one documentary chapter")
    run_progress.add_argument("--state", default="output/documentary-run.json")
    run_progress.add_argument("--chapter", type=int, required=True)
    run_progress.add_argument("--status", choices=("planned", "researched", "scripted", "narrated", "assembled", "reviewed"))
    run_progress.add_argument("--output-name")
    run_progress.add_argument("--output-path")
    run_progress.add_argument("--error")

    plan = sub.add_parser("plan", help="create a research/production plan")
    plan.add_argument("--topic", required=True)
    plan.add_argument("--audience", default="curious general audience")

    storyboard = sub.add_parser("storyboard", help="create an empty four-scene storyboard")
    storyboard.add_argument("--topic", required=True)
    storyboard.add_argument("--output", default="output/storyboard.json")

    draft = sub.add_parser("draft-script", help="draft English narration and Persian subtitles using local Ollama")
    draft.add_argument("--topic", required=True)
    draft.add_argument("--output", default="output/storyboard.json")
    draft.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    draft.add_argument("--model", default="qwen2.5:3b")
    draft.add_argument("--timeout", type=int, default=180)

    clips = sub.add_parser("video-plan", help="create four linked 15-second clip prompts")
    clips.add_argument("--topic", required=True)
    clips.add_argument("--scene", action="append",
                       help="scene description; repeat four times to override storyboard scenes")
    clips.add_argument("--storyboard", default="output/storyboard.json",
                       help="use scene descriptions from this storyboard when present")
    clips.add_argument("--style", default="cinematic documentary, realistic detail, natural motion")
    clips.add_argument("--output", default="output/video-plan.json")

    render = sub.add_parser("video-render", help="join downloaded clips into a final MP4")
    render.add_argument("--jobs-manifest", default="output/pexels-jobs.json")
    render.add_argument("--output", default="output/final-video.mp4")
    render.add_argument("--subtitles", default=None)
    render.add_argument("--narration-audio", default=None)

    voice = sub.add_parser("voiceover", help="synthesize English narration locally with Piper")
    voice.add_argument("--storyboard", default="output/storyboard.json")
    voice.add_argument("--model", required=True, help="path to a Piper .onnx voice model")
    voice.add_argument("--output", default="output/narration.wav")
    voice.add_argument("--speaker-id", type=int, default=None)

    subs = sub.add_parser("subtitles", help="create timed Persian subtitles from the storyboard")
    subs.add_argument("--manifest", default="output/storyboard.json")
    subs.add_argument("--output", default="output/persian.srt")

    package = sub.add_parser("youtube-package", help="create editable title, description, chapters and tags")
    package.add_argument("--storyboard", default="output/storyboard.json")
    package.add_argument("--output", default="output/youtube-package.json")

    review = sub.add_parser("script-check", help="check script completeness, sources and claim references")
    review.add_argument("--storyboard", default="output/storyboard.json")
    review.add_argument("--output", default="output/script-review.json")

    auto = sub.add_parser("auto-run", help="run cloud production without Ollama")
    auto.add_argument("--topic", default="", help="leave blank for automatic RSS topic discovery")
    auto.add_argument("--output-dir", default="output")
    auto.add_argument("--upload", action="store_true", help="upload the finished video to YouTube (private by default)")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_dotenv()
    Settings.from_env()

    if args.command == "documentary-plan":
        from .documentary_plan import build_documentary_plan, save_documentary_plan
        plan = build_documentary_plan(args.topic, args.minutes, args.clip_seconds)
        path = save_documentary_plan(plan, args.output)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        print(f"Saved documentary production blueprint: {path}")
        return 0

    if args.command == "documentary-init":
        from .documentary_state import initialize_documentary_run
        path = initialize_documentary_run(args.plan, args.state)
        print(f"Initialized resumable documentary run: {path}")
        return 0

    if args.command == "documentary-progress":
        from .documentary_state import update_chapter_state
        outputs = None
        if args.output_name or args.output_path:
            if not args.output_name or not args.output_path:
                raise SystemExit("--output-name and --output-path must be supplied together.")
            outputs = {args.output_name: args.output_path}
        state = update_chapter_state(args.state, args.chapter, args.status,
                                     outputs=outputs, error=args.error)
        chapter = next(item for item in state["chapters"] if item["chapter"] == args.chapter)
        print(json.dumps(chapter, ensure_ascii=False, indent=2))
        print(f"Run status: {state['status']}")
        return 0

    if args.command == "plan":
        print(json.dumps(plan_as_dict(build_plan(args.topic, args.audience)),
                         ensure_ascii=False, indent=2))
        return 0

    if args.command == "storyboard":
        path = save_script_package(args.topic, default_storyboard(args.topic), args.output)
        print(f"Created four-scene / 60-second storyboard: {path}")
        return 0

    if args.command == "draft-script":
        path = draft_storyboard(args.topic, args.output, args.ollama_url, args.model, args.timeout)
        print(f"Created bilingual AI draft (not fact-checked): {path}")
        return 0

    if args.command == "video-plan":
        storyboard_scenes = None
        if args.scene:
            scenes = args.scene
        else:
            storyboard_path = Path(args.storyboard)
            if storyboard_path.is_file():
                storyboard_payload = json.loads(storyboard_path.read_text(encoding="utf-8"))
                if storyboard_payload.get("topic") != args.topic:
                    raise SystemExit("Storyboard topic does not match --topic.")
                storyboard_scenes = storyboard_payload.get("scenes", [])
                scenes = [item["scene"] for item in storyboard_scenes]
            else:
                scenes = [item["scene"] for item in default_storyboard(args.topic)]

        if len(scenes) != 4:
            raise SystemExit("The current one-minute preset requires exactly four scenes.")
        segments = build_segments(args.topic, scenes, args.style, duration_seconds=15)
        segment_data = segments_as_dicts(segments)
        if storyboard_scenes:
            for index, scene in enumerate(storyboard_scenes):
                segment_data[index]["narration"] = scene.get("narration_en", "")
                segment_data[index]["subtitle"] = scene.get("subtitle_fa", "")

        payload = {
            "topic": args.topic,
            "target_duration_seconds": 60,
            "clip_duration_target_seconds": 15,
            "aspect_ratio": "16:9",
            "visual_style": args.style,
            "segments": segment_data,
        }
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created 4 linked clips (target 60 seconds): {target}")
        return 0

    if args.command == "video-render":
        path = render_video(args.jobs_manifest, args.output, args.subtitles,
                            args.narration_audio)
        print(f"Rendered final video: {path}")
        return 0

    if args.command == "voiceover":
        path = synthesize_storyboard(args.storyboard, args.output, args.model,
                                     speaker_id=args.speaker_id)
        print(f"Created English narration audio: {path}")
        return 0

    if args.command == "subtitles":
        path = storyboard_subtitles(args.manifest, args.output)
        print(f"Created Persian subtitle file: {path}")
        return 0

    if args.command == "youtube-package":
        path = build_youtube_package(args.storyboard, args.output)
        print(f"Created editable YouTube publishing package: {path}")
        return 0

    if args.command == "script-check":
        report = write_review_report(args.storyboard, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1

    if args.command == "auto-run":
        from .automation import run_automated
        result = run_automated(args.topic, args.output_dir, publish=args.upload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
