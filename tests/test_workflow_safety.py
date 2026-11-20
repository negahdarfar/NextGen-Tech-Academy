"""Regression tests for the explicitly configured public YouTube publishing policy."""
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "auto-publish.yml"
)


def test_manual_publish_defaults_to_public():
    source = WORKFLOW.read_text(encoding="utf-8")
    privacy = source.split("privacy_status:", 1)[1].split("schedule:", 1)[0]
    assert "default: public" in privacy
    assert "- public" in privacy


def test_public_visibility_is_enabled_for_manual_public_and_scheduled_runs():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event_name == 'schedule' && 'public'" in source
    assert "inputs.privacy_status == 'public'" in source
    assert "YOUTUBE_ALLOW_PUBLIC:" in source


def test_scheduled_runs_upload_publicly():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event_name == 'schedule' || inputs.privacy_status == 'public'" in source
    assert "Automatic public publishing enabled." in source
