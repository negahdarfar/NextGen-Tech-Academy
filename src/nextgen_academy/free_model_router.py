#!/usr/bin/env python3
"""Discover and rank explicitly free OpenAI-compatible models from a cloud gateway.

Discovery only calls GET /models (no inference). A model is eligible only when
its ID or structured catalogue metadata explicitly advertises a free tier, or
all advertised input/output token prices are exactly zero. Unknown pricing is
never assumed free.
"""
import json
import urllib.error
import urllib.request

FREE_MARKERS = (":free", "/free", "-free", "_free")
ROUTER_MARKERS = ("kilo-auto/free", "openrouter/free")
PRICE_KEYS = (
    ("prompt", "completion"),
    ("input", "output"),
    ("input_cost_per_token", "output_cost_per_token"),
    ("input_price", "output_price"),
)


def _is_zero_price(value):
    if isinstance(value, bool) or value is None:
        return False
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _metadata_is_free(metadata):
    """Recognize only unambiguous, machine-readable free-tier declarations."""
    if not isinstance(metadata, dict):
        return False

    for key in ("is_free", "free", "free_tier"):
        if metadata.get(key) is True:
            return True
    for key in ("pricing", "cost", "prices"):
        pricing = metadata.get(key)
        if isinstance(pricing, dict):
            for input_key, output_key in PRICE_KEYS:
                if input_key in pricing and output_key in pricing:
                    if _is_zero_price(pricing[input_key]) and _is_zero_price(pricing[output_key]):
                        return True
    # Some catalogues put free-tier metadata under a provider object.
    provider = metadata.get("top_provider")
    if isinstance(provider, dict) and _metadata_is_free(provider):
        return True
    return False


def is_explicitly_free(model_id, metadata=None):
    value = str(model_id or "").strip().lower()
    return bool(value) and (
        any(marker in value for marker in FREE_MARKERS)
        or _metadata_is_free(metadata)
    )


def _model_rows(payload):
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise RuntimeError("FreeLLMAPI /models response has no model list.")
    return rows


def _model_ids(payload):
    result = []
    for row in _model_rows(payload):
        if isinstance(row, dict):
            model_id = row.get("id") or row.get("name")
            if model_id and is_explicitly_free(model_id, row):
                result.append(str(model_id))
    return list(dict.fromkeys(result))


def _score(model_id, task):
    value = model_id.lower()
    if value in ROUTER_MARKERS:
        return -100
    score = 0
    if task == "translation":
        for marker, points in (
            ("lightning", 100), ("flash", 85), ("mini", 70),
            ("nano", 60), ("instruct", 45), ("super", 35),
            ("ultra", 25), ("reason", 20),
        ):
            if marker in value:
                score += points
    elif task == "seo":
        for marker, points in (
            ("super", 100), ("ultra", 90), ("reason", 85),
            ("instruct", 70), ("flash", 60), ("lightning", 50),
            ("mini", 40), ("nano", 30),
        ):
            if marker in value:
                score += points
    elif task == "vision":
        score += 100 if any(x in value for x in ("vision", "-vl", "omni")) else 0
    if any(x in value for x in ("vision", "-vl")) and task != "vision":
        score -= 50
    return score


def discover_free_models(base_url, api_key, task="general", preferred="auto", timeout=20):
    """Return best-first explicitly free model IDs from the live gateway catalogue."""
    if not base_url or not api_key:
        return []
    url = base_url.rstrip("/") + "/models"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"FreeLLMAPI model discovery failed: {exc}") from exc

    rows = _model_rows(payload)
    models = _model_ids(payload)
    if not models:
        priced = sum(
            1 for row in rows if isinstance(row, dict)
            and any(isinstance(row.get(key), dict) for key in ("pricing", "cost", "prices"))
        )
        print(
            f"FreeLLMAPI catalogue: {len(rows)} models; {priced} include structured pricing; "
            "none explicitly free. Unknown-price models remain excluded.",
            flush=True,
        )
        return []
    ordered = sorted(models, key=lambda item: (_score(item, task), item.lower()), reverse=True)
    preferred = str(preferred or "auto").strip()
    if preferred.lower() not in ("", "auto") and preferred in models:
        ordered = [preferred] + [item for item in ordered if item != preferred]
    print(f"FreeLLMAPI catalogue: {len(rows)} models; {len(ordered)} explicitly free candidates.", flush=True)
    return ordered
