import json
from unittest.mock import patch

import pytest

from nextgen_academy.llm import LLMError, _parse_json, generate_json


def test_parse_json_from_fenced_response():
    assert _parse_json("```json\n{\"ok\": true}\n```") == {"ok": True}


def test_cloud_provider_fallback_uses_first_configured_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_ORDER", "gemini,groq")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setenv("GROQ_API_KEY", "fake2")
    with patch("nextgen_academy.llm._gemini", side_effect=RuntimeError("temporary")):
        with patch("nextgen_academy.llm._openai_compatible", return_value='{"scenes": []}') as fallback:
            assert generate_json("system", "user") == {"scenes": []}
            fallback.assert_called_once()


def test_cloud_llm_fails_when_no_provider_is_configured(monkeypatch):
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(LLMError, match="No cloud LLM"):
        generate_json("system", "user")
