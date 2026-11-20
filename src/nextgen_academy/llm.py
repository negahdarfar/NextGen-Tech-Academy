"""Free-tier LLM routing with live zero-price checks for OpenRouter models."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any


class LLMError(RuntimeError):
    pass


def generate_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    errors = []
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        try:
            return _parse_json(_openrouter_free(system_prompt, user_prompt))
        except Exception as exc:
            errors.append(f"OpenRouter free tier: {str(exc)[:300]}")
            print(f"OpenRouter free models unavailable; checking explicitly free FreeLLMAPI model: {exc}")
    configured_model = os.getenv("FREELLMAPI_MODEL", "").strip()
    if (os.getenv("FREELLMAPI_CLOUD_BASE_URL", "").strip()
            and os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip()
            and configured_model.endswith(":free")):
        try:
            return _parse_json(_freellmapi(system_prompt, user_prompt))
        except Exception as exc:
            errors.append(f"FreeLLMAPI free model: {str(exc)[:300]}")
    elif os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip():
        errors.append("FreeLLMAPI skipped: set FREELLMAPI_MODEL to a model ID ending in :free; auto/unknown pricing is blocked.")
    raise LLMError("No verified zero-priced LLM route succeeded. " + " | ".join(errors))

def _freellmapi(system_prompt: str, user_prompt: str) -> str:
    base_url = os.getenv("FREELLMAPI_CLOUD_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("FREELLMAPI_CLOUD_API_KEY", "").strip()
    if not base_url or not api_key:
        raise LLMError("FreeLLMAPI cloud URL and API key must both be configured.")
    if not base_url.startswith(("http://", "https://")):
        raise LLMError("FREELLMAPI_CLOUD_BASE_URL must be an http(s) URL.")
    model = os.getenv("FREELLMAPI_MODEL", "").strip()\n    if not model.endswith(":free"):\n        raise LLMError("FreeLLMAPI model must be explicitly configured with a :free suffix.")
    if base_url.endswith("/chat/completions"):
        endpoint = base_url
    elif base_url.endswith("/v1"):
        endpoint = base_url + "/chat/completions"
    else:
        endpoint = base_url + "/v1/chat/completions"
    try:
        return _openai_compatible(endpoint, api_key, model, system_prompt, user_prompt)
    except Exception as exc:
        raise LLMError(f"FreeLLMAPI request failed (model={model}): {str(exc)[:500]}") from exc


def _openrouter_free(system_prompt: str, user_prompt: str) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://github.com/negahdarfar/NextGen-Tech-Academy",
               "X-Title": "NextGen Tech Academy"}
    req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                 headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=45) as response:
        catalogue = json.loads(response.read().decode("utf-8")).get("data", [])
    preferred = os.getenv("OPENROUTER_MODEL", "").strip()
    free_models = []
    for item in catalogue:
        model_id = str(item.get("id", ""))
        pricing = item.get("pricing") or {}
        try:
            zero_price = (Decimal(str(pricing.get("prompt", "NaN"))) == 0 and
                          Decimal(str(pricing.get("completion", "NaN"))) == 0)
        except (InvalidOperation, TypeError):
            zero_price = False
        if model_id.endswith(":free") and zero_price and int(item.get("context_length", 0) or 0) >= 4096:
            free_models.append(model_id)
    if preferred:
        if preferred not in free_models:
            raise LLMError("Configured OPENROUTER_MODEL is not currently listed with zero input/output pricing.")
        free_models = [preferred] + [m for m in free_models if m != preferred]
    if not free_models:
        raise LLMError("OpenRouter currently advertises no verified zero-priced :free models.")
    failures = []
    for model in free_models[:6]:
        try:
            return _openai_compatible("https://openrouter.ai/api/v1/chat/completions",
                                      key, model, system_prompt, user_prompt, headers=headers)
        except Exception as exc:
            failures.append(f"{model}: {str(exc)[:180]}")
            print(f"Free model {model} unavailable; rotating to next verified free model.")
    raise LLMError("All checked free OpenRouter models failed: " + " | ".join(failures))


def _openai_compatible(url: str, key: str, model: str, system_prompt: str,
                       user_prompt: str, headers: dict[str, str] | None = None) -> str:
    payload = {"model": model, "temperature": 0.35,
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}]}
    request_headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers=request_headers, method="POST")
    retryable_statuses = {408, 429, 500, 502, 503, 504}
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            if exc.code not in retryable_statuses or attempt == 2:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = min(max(float(retry_after), 0.0), 12.0) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            time.sleep(delay)


def _parse_json(raw: str) -> dict[str, Any]:
    content = raw.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM provider did not return valid JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("LLM JSON root must be an object")
    return data
