"""Validate evidence packs before claims are used in an educational video."""
from __future__ import annotations
from urllib.parse import urlparse

def validate_research_pack(pack: dict, minimum_sources: int = 2) -> list[str]:
    errors: list[str] = []
    sources = pack.get("sources")
    claims = pack.get("claims")
    if not isinstance(sources, list) or len(sources) < minimum_sources:
        errors.append(f"at least {minimum_sources} sources are required")
        sources = sources if isinstance(sources, list) else []
    source_ids: set[str] = set()
    domains: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"source {index}: expected an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"source {index}: missing id")
        elif source_id in source_ids:
            errors.append(f"source {index}: duplicate id {source_id}")
        else:
            source_ids.add(source_id)
        url = source.get("url", "")
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme not in ("http", "https") or not parsed.netloc:
            errors.append(f"source {index}: valid http(s) URL required")
        else:
            domains.add(parsed.netloc.lower().removeprefix("www."))
        if not source.get("published_at"):
            errors.append(f"source {index}: published_at is required")
        if not source.get("accessed_at"):
            errors.append(f"source {index}: accessed_at is required")
        if not source.get("publisher"):
            errors.append(f"source {index}: publisher is required")
    if len(domains) < minimum_sources:
        errors.append(f"at least {minimum_sources} distinct source domains are required")
    if not isinstance(claims, list) or not claims:
        errors.append("at least one factual claim is required")
        claims = claims if isinstance(claims, list) else []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict) or not claim.get("text"):
            errors.append(f"claim {index}: claim text is required")
            continue
        refs = claim.get("source_ids")
        if not isinstance(refs, list) or not refs:
            errors.append(f"claim {index}: at least one source_id is required")
            continue
        missing = [ref for ref in refs if ref not in source_ids]
        if missing:
            errors.append(f"claim {index}: unknown source ids: {', '.join(map(str, missing))}")
    return errors
