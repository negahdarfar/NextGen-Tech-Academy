import pytest
from unittest.mock import patch

from nextgen_academy.llm import LLMError, _parse_json, generate_json


def test_parse_json_from_fenced_response():
    assert _parse_json("```json\\n{\\\"ok\\\": true}\\n```") == {"ok": True}


def test_generate_json_uses_only_freellmapi(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "gemini,groq,openrouter")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", return_value='{"ok": true}') as free:
        assert generate_json("system", "user") == {"ok": True}
        free.assert_called_once_with("system", "user")


def test_generate_json_does_not_fallback_when_freellmapi_fails(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", side_effect=RuntimeError("gateway down")):
        with pytest.raises(RuntimeError, match="gateway down"):
            generate_json("system", "user")


def test_generate_json_requires_freellmapi_even_if_other_keys_exist(monkeypatch):
    monkeypatch.delenv("FREELLMAPI_CLOUD_BASE_URL", raising=False)
    monkeypatch.delenv("FREELLMAPI_CLOUD_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "other-provider-key")
    with pytest.raises(LLMError, match="FreeLLMAPI cloud URL and API key"):
        generate_json("system", "user")
