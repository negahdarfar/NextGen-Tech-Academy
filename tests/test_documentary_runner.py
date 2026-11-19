import pytest

from nextgen_academy.documentary_runner import produce_documentary, DocumentaryRunError


def test_runner_requires_confirmation_before_initializing_state(tmp_path):
    state = tmp_path / "run.json"
    with pytest.raises(DocumentaryRunError, match="confirm-provider-requests"):
        produce_documentary("AI", state_path=state, output_dir=tmp_path / "out")
    assert not state.exists()


def test_zero_budget_preflight_rejects_missing_pexels_before_llm_or_tts(tmp_path, monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "placeholder")
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(DocumentaryRunError, match="PEXELS_API_KEY"):
        produce_documentary("AI", state_path=tmp_path / "run.json",
                            output_dir=tmp_path / "out",
                            confirm_provider_requests=True)
    assert not (tmp_path / "run.json").exists()


def test_agnes_requires_separate_cost_acknowledgement(tmp_path, monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "placeholder")
    with pytest.raises(DocumentaryRunError, match="chargeable"):
        produce_documentary("AI", provider="agnes",
                            state_path=tmp_path / "run.json",
                            output_dir=tmp_path / "out",
                            confirm_provider_requests=True)
    assert not (tmp_path / "run.json").exists()
