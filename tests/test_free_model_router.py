import json
from unittest.mock import patch

import pytest

from nextgen_academy.free_model_router import discover_free_models, is_explicitly_free
from nextgen_academy.llm import LLMError, _freellmapi, generate_json


def test_only_explicit_free_ids_or_metadata_are_eligible():
    assert is_explicitly_free("vendor/model:free")
    assert is_explicitly_free("kilo-auto/free")
    assert is_explicitly_free("vendor/model", {"is_free": True})
    assert is_explicitly_free("vendor/model", {"pricing": {"prompt": "0", "completion": "0"}})
    assert not is_explicitly_free("vendor/unknown-price")
    assert not is_explicitly_free("vendor/model", {"pricing": {"prompt": "0", "completion": "0.0001"}})


@patch("nextgen_academy.free_model_router.urllib.request.urlopen")
def test_discovery_returns_only_explicit_free_models(urlopen):
    payload = {"data": [
        {"id": "vendor/paid"},
        {"id": "vendor/free-flash:free"},
        {"id": "vendor/free-metadata", "free_tier": True},
        {"id": "vendor/unknown"},
    ]}
    urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    models = discover_free_models("https://gateway.example/v1", "test-key")
    assert set(models) == {"vendor/free-flash:free", "vendor/free-metadata"}


def test_freellmapi_uses_gateway_auto_router(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.delenv("FREELLMAPI_MODEL", raising=False)
    with patch("nextgen_academy.llm._openai_compatible", return_value='{"ok": true}') as call:
        assert _freellmapi("system", "user") == '{"ok": true}'
        assert call.call_args.args[:3] == (
            "https://gateway.example/v1/chat/completions", "test-key", "auto"
        )


def test_freellmapi_respects_explicit_model_override(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("FREELLMAPI_MODEL", "provider/model-name")
    with patch("nextgen_academy.llm._openai_compatible", return_value='{"ok": true}') as call:
        _freellmapi("system", "user")
        assert call.call_args.args[2] == "provider/model-name"


def test_freellmapi_requires_gateway_credentials(monkeypatch):
    monkeypatch.delenv("FREELLMAPI_CLOUD_BASE_URL", raising=False)
    monkeypatch.delenv("FREELLMAPI_CLOUD_API_KEY", raising=False)
    with pytest.raises(LLMError, match="cloud URL and API key"):
        _freellmapi("system", "user")


def test_generate_json_uses_only_freellmapi(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,gemini,openrouter")
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", return_value='{"provider": "gateway"}') as gateway:
        assert generate_json("system", "user") == {"provider": "gateway"}
        gateway.assert_called_once()


def test_generate_json_stops_when_freellmapi_fails(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,gemini")
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", side_effect=RuntimeError("gateway down")):
        with pytest.raises(RuntimeError, match="gateway down"):
            generate_json("system", "user")
