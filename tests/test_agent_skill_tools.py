"""Smoke tests for vendored YouTube editorial skill helpers."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"


def run(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_hookscore_returns_ranked_json():
    result = run(SKILLS / "yt-script" / "hookscore.py", "--json", "--hook",
                 "Why does this documented process fail after three important steps?")
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert 0 <= rows[0]["verdict"] <= 100
    assert rows[0]["hook"].startswith("Why")


def test_title_linter_returns_json():
    result = run(SKILLS / "yt-package" / "title.py", "--json", "--title",
                 "How Solar Storms Affect Earth in 2026", "--thumb", "THE SUN")
    rows = json.loads(result.stdout)
    assert len(rows) == 1
    assert rows[0]["title"].startswith("How Solar Storms")


def test_chapter_tool_imports_shared_transcript_parser():
    result = run(SKILLS / "yt-chapters" / "chapters.py")
    assert "chapters.py" in result.stdout


def test_edit_tool_imports_and_prints_usage():
    result = run(SKILLS / "yt-edit" / "deadair.py")
    assert "edit decision list" in result.stdout.lower()


def test_retention_tool_prints_usage():
    result = run(SKILLS / "yt-retention" / "retention.py")
    assert "audience-retention" in result.stdout.lower()


def test_viral_tool_imports_hook_formula_catalogue():
    result = run(SKILLS / "yt-viral" / "swipe.py")
    assert "rank collected videos" in result.stdout.lower()


def test_hook_catalogue_contains_multiple_formulas():
    data = json.loads((SKILLS / "yt-script" / "hooks.json").read_text(encoding="utf-8"))
    assert len(data["hooks"]) >= 15
