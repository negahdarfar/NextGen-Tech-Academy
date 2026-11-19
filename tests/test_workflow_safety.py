"""Regression tests for safe YouTube publishing defaults."""
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "auto-publish.yml"
)


def test_manual_publish_defaults_to_private():
    source = WORKFLOW.read_text(encoding="utf-8")
    privacy = source.split("privacy_status:", 1)[1].split("approve_publication:", 1)[0]
    assert "default: private" in privacy


def test_public_publish_requires_separate_explicit_approval():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "approve_publication:" in source
    assert "default: false" in source
    assert "inputs.approve_publication == true" in source
    assert "No video generation or upload will start." in source


def test_scheduled_runs_cannot_enable_public_visibility():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch'" in source
    assert "|| 'false'" in source
    assert "scheduled runs remain private" in source
