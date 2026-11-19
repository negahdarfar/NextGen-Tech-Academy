"""Command-line entry point for safe, local planning."""

from __future__ import annotations

import argparse
import json

from .config import Settings
from .planning import build_plan, plan_as_dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nextgen-academy",
        description="Plan an educational YouTube video (no publishing or API calls).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="create a production plan")
    plan_parser.add_argument("--topic", required=True, help="video topic")
    plan_parser.add_argument(
        "--audience",
        default="curious general audience",
        help="intended audience",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    Settings.from_env()  # Validate local configuration even in plan-only mode.

    if args.command == "plan":
        plan = build_plan(args.topic, args.audience)
        print(json.dumps(plan_as_dict(plan), ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
