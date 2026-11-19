from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "longform-documentary.yml"


def test_longform_workflow_requires_explicit_generation_confirmation():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "confirm_generation:" in source
    assert "default: false" in source
    assert "if: ${{ inputs.confirm_generation == true }}" in source


def test_longform_workflow_is_free_only_by_default():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert 'ALLOW_PAID_LLM: "false"' in source
    assert 'LLM_PROVIDER_ORDER: "freellmapi,openrouter"' in source
    assert 'default: auto' in source
    assert 'Auto/Pexels zero-budget mode requires PEXELS_API_KEY.' in source
    assert 'Agnes potential-cost acknowledgement is required.' in source


def test_longform_workflow_never_uploads_to_youtube():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "documentary-produce" in source
    assert "--confirm-provider-requests" in source
    assert "--upload" not in source
    assert "YOUTUBE_TOKEN_JSON" not in source


def test_longform_workflow_restores_and_saves_resume_cache():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/cache/restore@v4" in source
    assert "actions/cache/save@v4" in source
    assert "restore-keys:" in source
    assert "if: always()" in source
