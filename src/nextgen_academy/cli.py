"""Command-line entry point for planning and submitting video clips."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .planning import build_plan, plan_as_dict
from .video_jobs import submit_segments
from .video_segments import VideoSegment, build_segments, segments_as_dicts
from .vidogrid import VidoGridClient, VidoGridSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nextgen-academy",
        description="Plan educational YouTube videos and generate video clip jobs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="create a production plan")
    plan_parser.add_argument("--topic", required=True, help="video topic")
    plan_parser.add_argument("--audience", default="curious general audience")

    clips_parser = subparsers.add_parser(
        "video-plan", help="create a chained 15-second clip prompt manifest"
    )
    clips_parser.add_argument("--topic", required=True)
    clips_parser.add_argument(
        "--scene", action="append", required=True,
        help="ordered scene description; repeat this option for each clip",
    )
    clips_parser.add_argument(
        "--style",
        default="cinematic documentary, realistic detail, natural motion",
    )
    clips_parser.add_argument("--output", default="output/video-plan.json")

    submit_parser = subparsers.add_parser(
        "video-submit", help="submit planned clips to VidoGrid (uses API credits)"
    )
    submit_parser.add_argument("--manifest", default="output/video-plan.json")
    submit_parser.add_argument("--jobs-output", default="output/vidogrid-jobs.json")
    submit_parser.add_argument(
        "--confirm-paid-api", action="store_true",
        help="required acknowledgement that API jobs may consume paid credits",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    Settings.from_env()

    if args.command == "plan":
        plan = build_plan(args.topic, args.audience)
        print(json.dumps(plan_as_dict(plan), ensure_ascii=False, indent=2))
        return 0

    if args.command == "video-plan":
        segments = build_segments(args.topic, args.scene, args.style)
        payload = {
            "topic": args.topic,
            "visual_style": args.style,
            "clip_duration_target_seconds": 15,
            "aspect_ratio": "16:9",
            "segments": segments_as_dicts(segments),
        }
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Created {len(segments)} clip prompts: {target}")
        return 0

    if args.command == "video-submit":
        if not args.confirm_paid_api:
            raise SystemExit(
                "VidoGrid API may consume credits. Re-run with --confirm-paid-api."
            )
        payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        segments = [VideoSegment(**item) for item in payload["segments"]]
        client = VidoGridClient(VidoGridSettings.from_env())
        account = client.account()
        print("VidoGrid account/credit response:")
        print(json.dumps(account, ensure_ascii=False, indent=2))
        answer = input("Submit these clips to VidoGrid now? [y/N] ").strip().lower()
        if answer != "y":
            print("Submission cancelled; no generation jobs were sent.")
            return 0
        manifest = submit_segments(segments, client, args.jobs_output)
        print(f"Submitted {len(manifest['jobs'])} jobs: {args.jobs_output}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
