"""Low-cost RSS research discovery. Sources are leads, not verified evidence."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from typing import Any


class ResearchError(RuntimeError):
    pass


def discover_sources(topic: str, limit: int = 12) -> list[dict[str, Any]]:
    topic = topic.strip()
    if not topic:
        raise ValueError("topic is required")
    if not 1 <= limit <= 30:
        raise ValueError("limit must be between 1 and 30")
    query = urllib.parse.quote(topic)
    feeds = [
        ("Google News", f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"),
        ("arXiv", f"https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={min(limit, 10)}&sortBy=submittedDate&sortOrder=descending"),
    ]
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for publisher, url in feeds:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "NextGen-Tech-Academy/0.2 research-bot"})
            with urllib.request.urlopen(request, timeout=20) as response:
                root = ET.fromstring(response.read())
        except Exception:
            continue
        for item in root.findall(".//item") + root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = _clean(_child_text(item, "title", "{http://www.w3.org/2005/Atom}title"))
            link = _child_text(item, "link")
            if not link:
                atom_link = item.find("{http://www.w3.org/2005/Atom}link")
                link = atom_link.attrib.get("href", "") if atom_link is not None else ""
            summary = _clean(_child_text(item, "description", "{http://www.w3.org/2005/Atom}summary"))
            published = _child_text(item, "pubDate", "{http://www.w3.org/2005/Atom}published")
            if not title or not link.startswith("https://") or link in seen:
                continue
            seen.add(link)
            results.append({
                "id": f"src{len(results)+1}",
                "title": title[:300],
                "publisher": publisher,
                "url": link,
                "published": published[:100],
                "summary": summary[:1200],
                "checked": False,
                "discovery_source": publisher,
            })
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
    if not results:
        raise ResearchError("No RSS sources were found. Check network access or try another topic.")
    return results


def save_research(topic: str, output_path: str | Path, limit: int = 12) -> Path:
    sources = discover_sources(topic, limit)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"topic": topic, "created_at": int(time.time()), "sources": sources},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _child_text(element: ET.Element, *names: str) -> str:
    for name in names:
        child = element.find(name)
        if child is not None:
            return "".join(child.itertext()).strip()
    return ""


def _clean(value: str) -> str:
    value = unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()
