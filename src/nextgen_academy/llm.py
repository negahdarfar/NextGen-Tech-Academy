"""FreeLLMAPI-only cloud LLM adapter; no direct provider fallback."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from .free_model_router import discover_free_models


class LLMError(RuntimeError):
    pass


def generate_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Generate structured text exclusively through explicitly free FreeLLMAPI models."""
    raw = _freellmapi(system_prompt, user_prompt)
    return _parse_json(raw)


def _freellmapi(system_prompt: str, user_prompt: str) -> str:
    """Use only models explicitly identified as free by the FreeLLMAPI catalogue."""
    base_url = os.getenv("FREELLMAPI_CLOUD_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip()
    if not base_url or not api_key:
        raise LLMError("FreeLLMAPI cloud URL and API key must both be configured.")
    if not base_url.startswith(("http://", "https://")):
        raise LLMError("FREELLMAPI_CLOUD_BASE_URL must be an http(s) URL.")

    preferred = os.getenv("FREELLMAPI_MODEL", "auto").strip() or "auto"
    models = discover_free_models(base_url, api_key, task="general", preferred=preferred)
    if not models:
        raise LLMError("FreeLLMAPI catalogue exposed no explicitly free models; paid or unknown-price models were skipped.")

    if base_url.endswith("/chat/completions"):
        endpoint = base_url
    elif base_url.endswith("/v1"):
        endpoint = base_url + "/chat/completions"
    else:
        endpoint = base_url + "/v1/chat/completions"

    failures = []
    for model in models:
        try:
            return _openai_compatible(endpoint, api_key, model, system_prompt, user_prompt)
        except Exception as exc:
            failures.append(f"{model}: {str(exc)[:200]}")
    raise LLMError("All explicitly free FreeLLMAPI models failed: " + " | ".join(failures))


def _openai_compatible(url: str, key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": model,
        "temperature": 0.35,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("FreeLLMAPI did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("FreeLLMAPI JSON root must be an object")
    return data
