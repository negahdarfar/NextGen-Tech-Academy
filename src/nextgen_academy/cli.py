"""Command-line entry point for the one-minute video production workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .planning import build_plan, plan_as_dict
from .script import default_storyboard, save_script_package, storyboard_subtitles
from .video_jobs import submit_segments
from .video_pipeline import poll_and_download, render_video
from .video_segments import VideoSegment, build_segments, segments_as_dicts
from .vidogrid import VidoGridClient, VidoGridSettings
from .tts import synthesize_storyboard
from .youtube_package import build_youtube_package
from .script_review import write_review_report
from .ollama_writer import draft_storyboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nextgen-academy",
        description="Produce one-minute, 16:9 technology documentary videos.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="create a research/production plan")
    plan.add_argument("--topic", required=True)
    plan.add_argument("--audience", default="curious general audience")

    storyboard = sub.add_parser("storyboard", help="create a four-scene, one-minute storyboard")
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
                       help="use the edited storyboard by default")
    clips.add_argument("--style", default="cinematic documentary, realistic detail, natural motion")
    clips.add_argument("--output", default="output/video-plan.json")

    submit = sub.add_parser("video-submit", help="submit clips to VidoGrid (uses credits)")
    submit.add_argument("--manifest", default="output/video-plan.json")
    submit.add_argument("--jobs-output", default="output/vidogrid-jobs.json")
    submit.add_argument("--confirm-paid-api", action="store_true")

    download = sub.add_parser("video-download", help="poll VidoGrid and download completed clips")
    download.add_argument("--jobs-manifest", default="output/vidogrid-jobs.json")
    download.add_argument("--output-dir", default="output/clips")
    download.add_argument("--timeout", type=int, default=1800)
    download.add_argument("--poll-interval", type=int, default=8)

    render = sub.add_parser("video-render", help="join downloaded clips into a final MP4")
    render.add_argument("--jobs-manifest", default="output/vidogrid-jobs.json")
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    Settings.from_env()

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
        storyboard_path = Path(args.storyboard)
        if not args.scene and storyboard_path.is_file():
            storyboard_payload = json.loads(storyboard_path.read_text(encoding="utf-8"))
            if storyboard_payload.get("topic") != args.topic:
                raise SystemExit("Storyboard topic does not match --topic.")
            storyboard_scenes = storyboard_payload.get("scenes", [])
            scenes = [item["scene"] for item in storyboard_scenes]
        else:
            scenes = args.scene or [item["scene"] for item in default_storyboard(args.topic)]
        if len(scenes) != 4:
            raise SystemExit("The current one-minute preset requires exactly four scenes.")
        segments = build_segments(args.topic, scenes, args.style, duration_seconds=15)
        segment_data = segments_as_dicts(segments)
        if storyboard_scenes:
            for index, scene in enumerate(storyboard_scenes):
                segment_data[index]["narration"] = scene.get("narration_en", "")
                segment_data[index]["subtitle"] = scene.get("subtitle_fa", "")
        payload = {
            "topic": args.topic, "target_duration_seconds": 60,
            "clip_duration_target_seconds": 15, "aspect_ratio": "16:9",
            "visual_style": args.style, "segments": segment_data,
        }
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Created 4 linked clips (target 60 seconds): {target}")
        return 0

    if args.command == "video-submit":
        if not args.confirm_paid_api:
            raise SystemExit("API may consume credits. Add --confirm-paid-api to acknowledge.")
        payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        segments = [VideoSegment(**item) for item in payload["segments"]]
        client = VidoGridClient(VidoGridSettings.from_env())
        account = client.account()
        print("VidoGrid account and credit balance:")
        print(json.dumps(account, ensure_ascii=False, indent=2))
        if input("Submit these 4 clips now? [y/N] ").strip().lower() != "y":
            print("Cancelled; no generation jobs were sent.")
            return 0
        manifest = submit_segments(segments, client, args.jobs_output)
        print(f"Accepted job records: {len(manifest['jobs'])}; manifest: {args.jobs_output}")
        return 0

    if args.command == "video-download":
        client = VidoGridClient(VidoGridSettings.from_env())
        manifest = poll_and_download(client, args.jobs_manifest, args.output_dir,
                                     args.timeout, args.poll_interval)
        print(f"Downloaded {len(manifest['jobs'])} clips to {args.output_dir}")
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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
