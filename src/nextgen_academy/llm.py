"""Cloud LLM adapter with explicitly-free FreeLLMAPI first and Agnes fallback."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from .free_model_router import discover_free_models


class LLMError(RuntimeError):
    pass


def generate_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Try configured providers in order; never silently select unknown-price FreeLLMAPI models."""
    providers = {
        "freellmapi": _freellmapi,
        "agnes": _agnes,
    }
    order = [
        item.strip().lower()
        for item in os.getenv("LLM_PROVIDER_ORDER", "freellmapi,agnes").split(",")
        if item.strip()
    ]
    failures: list[str] = []
    for provider in order:
        generate = providers.get(provider)
        if generate is None:
            failures.append(f"{provider}: unsupported provider")
            continue
        try:
            raw = generate(system_prompt, user_prompt)
            return _parse_json(raw)
        except Exception as exc:
            failures.append(f"{provider}: {str(exc)[:300]}")
            print(f"LLM provider {provider} failed; trying next configured provider.", flush=True)
    raise LLMError("All configured LLM providers failed: " + " | ".join(failures))


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

    endpoint = _chat_endpoint(base_url)
    failures = []
    for model in models:
        try:
            return _openai_compatible(endpoint, api_key, model, system_prompt, user_prompt)
        except Exception as exc:
            failures.append(f"{model}: {str(exc)[:200]}")
    raise LLMError("All explicitly free FreeLLMAPI models failed: " + " | ".join(failures))


def _agnes(system_prompt: str, user_prompt: str) -> str:
    """Use Agnes' OpenAI-compatible text endpoint as the configured secondary provider."""
    api_key = os.getenv("AGNES_API_KEY", "").strip()
    if not api_key:
        raise LLMError("Agnes fallback selected but AGNES_API_KEY is not configured.")
    base_url = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise LLMError("AGNES_BASE_URL must be an http(s) URL.")
    model = os.getenv("AGNES_LLM_MODEL", "agnes-2.5-flash").strip() or "agnes-2.5-flash"
    return _openai_compatible(_chat_endpoint(base_url), api_key, model, system_prompt, user_prompt)


def _chat_endpoint(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return base_url + "/chat/completions"
    return base_url + "/v1/chat/completions"


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
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM provider did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("LLM provider JSON root must be an object")
    return data
