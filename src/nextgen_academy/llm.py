"""Cloud LLM adapters with provider fallback; no local Ollama dependency."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from .free_model_router import discover_free_models


class LLMError(RuntimeError):
    pass


def generate_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    order = [p.strip().lower() for p in os.getenv("LLM_PROVIDER_ORDER", "freellmapi,omniroute,gemini,groq,openrouter").split(",") if p.strip()]
    failures: list[str] = []
    for provider in order:
        try:
            if provider == "freellmapi" and os.getenv("FREELLMAPI_CLOUD_BASE_URL") and os.getenv("FREELLMAPI_CLOUD_API_KEY"):
                raw = _freellmapi(system_prompt, user_prompt)
            elif provider == "omniroute" and os.getenv("OMNIROUTE_BASE_URL"):
                raw = _omniroute(system_prompt, user_prompt)
            elif provider == "gemini" and os.getenv("GEMINI_API_KEY"):
                raw = _gemini(system_prompt, user_prompt)
            elif provider == "groq" and os.getenv("GROQ_API_KEY"):
                raw = _openai_compatible("https://api.groq.com/openai/v1/chat/completions",
                                         os.environ["GROQ_API_KEY"],
                                         os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                                         system_prompt, user_prompt)
            elif provider == "openrouter" and os.getenv("OPENROUTER_API_KEY"):
                model = os.getenv("OPENROUTER_MODEL", "").strip()
                if not model:
                    continue
                if not model.endswith(":free") and os.getenv("ALLOW_PAID_LLM", "").lower() != "true":
                    raise LLMError(
                        "OpenRouter model is not marked :free. Configure a free model or explicitly set ALLOW_PAID_LLM=true."
                    )
                raw = _openai_compatible("https://openrouter.ai/api/v1/chat/completions",
                                         os.environ["OPENROUTER_API_KEY"],
                                         model, system_prompt, user_prompt)
            else:
                continue
            return _parse_json(raw)
        except Exception as exc:
            failures.append(f"{provider}: {str(exc)[:300]}")
    if not failures:
        raise LLMError("No cloud LLM provider is configured. Set OMNIROUTE_BASE_URL or add GEMINI_API_KEY, GROQ_API_KEY or OPENROUTER_API_KEY.")
    raise LLMError("All configured LLM providers failed: " + " | ".join(failures))



def _freellmapi(system_prompt: str, user_prompt: str) -> str:
    """Use only models explicitly identified as free by a cloud gateway catalogue."""
    base_url = os.getenv("FREELLMAPI_CLOUD_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip()
    if not base_url or not api_key:
        raise LLMError("FREELLMAPI cloud URL and API key must both be configured.")
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


def _post(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 120) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={**headers, "Content-Type": "application/json"},
                                     method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _omniroute(system_prompt: str, user_prompt: str) -> str:
    """Call the self-hosted OmniRoute OpenAI-compatible gateway."""
    base_url = os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise LLMError("OMNIROUTE_BASE_URL must be an http(s) URL")
    if base_url.endswith("/chat/completions"):
        url = base_url
    elif base_url.endswith("/v1"):
        url = base_url + "/chat/completions"
    else:
        url = base_url + "/v1/chat/completions"
    model = os.getenv("OMNIROUTE_MODEL", "gemini/gemini-2.5-flash").strip()
    if not model:
        raise LLMError("OMNIROUTE_MODEL must not be empty")
    headers = {}
    if os.getenv("OMNIROUTE_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["OMNIROUTE_API_KEY"]
    data = _post(url, {"model": model, "temperature": 0.35,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}]},
                 headers, timeout=180)
    return data["choices"][0]["message"]["content"]

def _gemini(system_prompt: str, user_prompt: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    key = urllib.parse.quote(os.environ["GEMINI_API_KEY"], safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"systemInstruction": {"parts": [{"text": system_prompt}]},
               "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
               "generationConfig": {"responseMimeType": "application/json", "temperature": 0.35}}
    data = _post(url, payload, {}, timeout=180)
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _openai_compatible(url: str, key: str, model: str,
                       system_prompt: str, user_prompt: str) -> str:
    data = _post(url, {"model": model, "temperature": 0.35,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}]},
                 {"Authorization": f"Bearer {key}"}, timeout=180)
    return data["choices"][0]["message"]["content"]


def _parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("Provider did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("Provider JSON root must be an object")
    return data
