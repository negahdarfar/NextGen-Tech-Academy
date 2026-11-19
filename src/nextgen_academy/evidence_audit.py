"""Fetch source pages and create a transparent, non-authoritative evidence audit.

This module checks page availability and textual overlap only. It never labels a
claim true or verified; human review remains mandatory before publication.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.description = ""
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}:
            self._skip_depth += 1
        if tag.lower() == "meta" and attrs_dict.get("name", "").lower() in {"description", "og:description"}:
            self.description = attrs_dict.get("content", "") or self.description

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        if tag.lower() in {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        clean = re.sub(r"\s+", " ", data).strip()
        if not clean:
            return
        if self._in_title:
            self.title_parts.append(clean)
        if not self._skip_depth:
            self.text_parts.append(clean)


def _fetch_page(url: str, timeout: int = 12, max_bytes: int = 1_000_000) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Only absolute HTTPS source URLs are allowed.")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NextGen-Tech-Academy/1.0 (+source-audit; contact: repository owner)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        final = urlparse(final_url)
        if final.scheme != "https" or not final.netloc:
            raise ValueError("Source redirected away from HTTPS.")
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type and "text/" not in content_type:
            raise ValueError(f"Unsupported source content type: {content_type or 'unknown'}")
        charset = response.headers.get_content_charset() or "utf-8"
    decoded = raw.decode(charset, errors="replace")
    parser = _PageParser()
    parser.feed(decoded)
    excerpt = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    return {
        "status": "reachable",
        "final_url": final_url,
        "page_title": " ".join(parser.title_parts)[:400],
        "description": parser.description[:1000],
        "extracted_text": excerpt[:6000],
        "extracted_chars": len(excerpt),
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def enrich_sources(sources: list[dict[str, Any]], timeout: int = 12) -> list[dict[str, Any]]:
    """Attach fetched page evidence to RSS leads; failures remain visible, not fatal."""
    enriched: list[dict[str, Any]] = []
    for source in sources:
        item = dict(source)
        try:
            item["audit"] = _fetch_page(str(source.get("url", "")), timeout=timeout)
        except Exception as exc:
            item["audit"] = {
                "status": "unavailable",
                "error": f"{type(exc).__name__}: {str(exc)[:300]}",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        enriched.append(item)
    return enriched


def _terms(text: str) -> set[str]:
    return {word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9'-]{3,}", text)}


def audit_storyboard_claims(storyboard: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Report source reachability and lexical overlap; this is not truth verification."""
    by_id = {str(source.get("id", "")): source for source in sources}
    claim_rows = []
    for index, claim in enumerate(storyboard.get("claims", []), 1):
        claim_text = str(claim.get("text", "")).strip()
        claim_terms = _terms(claim_text)
        source_rows = []
        for source_id in claim.get("source_ids", []):
            source = by_id.get(str(source_id))
            if not source:
                source_rows.append({"source_id": source_id, "status": "unknown_source_id"})
                continue
            audit = source.get("audit", {})
            evidence_text = " ".join([
                str(source.get("title", "")),
                str(source.get("summary", "")),
                str(audit.get("page_title", "")),
                str(audit.get("description", "")),
                str(audit.get("extracted_text", "")),
            ])
            matched = sorted(claim_terms & _terms(evidence_text))
            ratio = round(len(matched) / len(claim_terms), 3) if claim_terms else 0.0
            source_rows.append({
                "source_id": source_id,
                "status": audit.get("status", "not_fetched"),
                "url": source.get("url", ""),
                "matched_terms": matched[:30],
                "term_overlap_ratio": ratio,
                "interpretation": "textual_overlap_only_not_proof",
            })
        claim_rows.append({
            "claim_index": index,
            "claim": claim_text,
            "source_ids": claim.get("source_ids", []),
            "sources": source_rows,
            "human_verification": "required",
        })
    return {
        "topic": storyboard.get("topic", ""),
        "audit_type": "source_reachability_and_lexical_overlap",
        "is_fact_checked": False,
        "human_review_required": True,
        "claims": claim_rows,
        "limitations": [
            "A reachable page is not necessarily authoritative or accurate.",
            "Text overlap does not establish that a source supports or proves a claim.",
            "RSS summaries and extracted page text may be incomplete or misleading.",
            "A human reviewer must open each source and verify every factual claim.",
        ],
    }


def write_evidence_audit(storyboard: dict[str, Any], sources: list[dict[str, Any]],
                         output_path: str | Path) -> Path:
    report = audit_storyboard_claims(storyboard, sources)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
