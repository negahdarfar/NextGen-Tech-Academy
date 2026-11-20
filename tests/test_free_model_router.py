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


def test_freellmapi_uses_only_discovered_free_model(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    with patch("nextgen_academy.llm.discover_free_models", return_value=["vendor/model:free"]):
        with patch("nextgen_academy.llm._openai_compatible", return_value='{"ok": true}') as call:
            assert _freellmapi("system", "user") == '{"ok": true}'
            assert call.call_args.args[:3] == (
                "https://gateway.example/v1/chat/completions", "test-key", "vendor/model:free"
            )


def test_freellmapi_refuses_unknown_or_paid_catalogue(monkeypatch):
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    with patch("nextgen_academy.llm.discover_free_models", return_value=[]):
        with pytest.raises(LLMError, match="explicitly free"):
            _freellmapi("system", "user")


def test_generate_json_ignores_alternate_provider_order(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,gemini,openrouter")
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", return_value='{"provider": "free"}') as free:
        with patch("nextgen_academy.llm._gemini") as gemini:
            assert generate_json("system", "user") == {"provider": "free"}
            free.assert_called_once()
            gemini.assert_not_called()


def test_generate_json_stops_when_freellmapi_fails(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "freellmapi,gemini")
    monkeypatch.setenv("FREELLMAPI_CLOUD_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("FREELLMAPI_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    with patch("nextgen_academy.llm._freellmapi", side_effect=RuntimeError("gateway down")):
        with patch("nextgen_academy.llm._gemini") as gemini:
            with pytest.raises(RuntimeError, match="gateway down"):
                generate_json("system", "user")
            gemini.assert_not_called()
