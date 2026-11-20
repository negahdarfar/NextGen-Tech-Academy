import pytest
from unittest.mock import patch

from nextgen_academy.llm import LLMError, _parse_json, generate_json


def test_parse_json_from_fenced_response():
    assert _parse_json("```json\n{\"ok\": true}\n```") == {"ok": True}


def test_generate_json_uses_freellmapi_first(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,agnes")
    with patch("nextgen_academy.llm._freellmapi", return_value='{"ok": true}') as free, \
         patch("nextgen_academy.llm._agnes") as agnes:
        assert generate_json("system", "user") == {"ok": True}
        free.assert_called_once_with("system", "user")
        agnes.assert_not_called()


def test_generate_json_falls_back_to_agnes_when_free_catalogue_has_no_free_models(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,agnes")
    with patch("nextgen_academy.llm._freellmapi", side_effect=LLMError("no free models")), \
         patch("nextgen_academy.llm._agnes", return_value='{"provider": "agnes"}') as agnes:
        assert generate_json("system", "user") == {"provider": "agnes"}
        agnes.assert_called_once_with("system", "user")


def test_generate_json_fails_clearly_when_all_providers_fail(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,agnes")
    with patch("nextgen_academy.llm._freellmapi", side_effect=RuntimeError("gateway down")), \
         patch("nextgen_academy.llm._agnes", side_effect=RuntimeError("unauthorized")):
        with pytest.raises(LLMError, match="gateway down.*unauthorized"):
            generate_json("system", "user")


def test_agnes_uses_openai_compatible_endpoint_and_model(monkeypatch):
    from nextgen_academy.llm import _agnes
    monkeypatch.setenv("AGNES_API_KEY", "test-agnes-key")
    monkeypatch.setenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
    with patch("nextgen_academy.llm._openai_compatible", return_value='{"ok": true}') as call:
        assert _agnes("system", "user") == '{"ok": true}'
        assert call.call_args.args[:3] == (
            "https://apihub.agnes-ai.com/v1/chat/completions",
            "test-agnes-key",
            "agnes-2.5-flash",
        )
