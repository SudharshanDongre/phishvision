"""Standalone cyber threat news fetching and caching utilities."""

from __future__ import annotations

import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


DEFAULT_REFRESH_MINUTES = int(os.getenv("CYBER_NEWS_REFRESH_MINUTES", "20"))
MIN_REFRESH_MINUTES = 15
MAX_REFRESH_MINUTES = 30
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("CYBER_NEWS_TIMEOUT_SECONDS", "10"))
USER_AGENT = os.getenv(
    "CYBER_NEWS_USER_AGENT",
    "PhishVision/1.0 (+https://github.com/)"
)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()

_NEWS_CACHE: Dict[str, dict] = {}


@dataclass
class NewsItem:
    headline: str
    source: str
    published: str
    summary: str
    link: str
    topic: str = "Cyber Threat"


def _clamp_refresh_minutes(refresh_minutes: int) -> int:
    try:
        value = int(refresh_minutes)
    except Exception:
        value = DEFAULT_REFRESH_MINUTES
    return max(MIN_REFRESH_MINUTES, min(MAX_REFRESH_MINUTES, value))


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _format_published(value: Optional[str]) -> str:
    if not value:
        return "Recently"
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%b %d, %I:%M %p")
    except Exception:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone().strftime("%b %d, %I:%M %p")
        except Exception:
            return value


def _compact_summary(text: str, limit: int = 240) -> str:
    cleaned = _strip_html(text)
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0]
    return f"{cut}..."


def _cache_key(refresh_minutes: int, max_items: int) -> str:
    return json.dumps({"refresh_minutes": refresh_minutes, "max_items": max_items}, sort_keys=True)


def _request(url: str) -> requests.Response:
    return requests.get(
        url,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml,application/rss+xml,application/json"},
    )


def _parse_rss_feed(feed_url: str, source_name: str, topic: str, max_items: int) -> List[NewsItem]:
    response = _request(feed_url)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    items: List[NewsItem] = []

    for entry in root.findall(".//item")[: max_items * 2]:
        title = _strip_html(entry.findtext("title", default="")).strip()
        link = (entry.findtext("link", default="") or "").strip()
        summary = entry.findtext("description", default="") or entry.findtext("summary", default="") or ""
        source = entry.findtext("source", default=source_name) or source_name
        published_raw = (
            entry.findtext("pubDate")
            or entry.findtext("published")
            or entry.findtext("updated")
            or entry.findtext("dc:date")
        )
        if not title or not link:
            continue
        items.append(
            NewsItem(
                headline=title,
                source=_strip_html(source),
                published=_format_published(published_raw),
                summary=_compact_summary(summary),
                link=link,
                topic=topic,
            )
        )

    return items


def _fetch_newsapi(max_items: int) -> List[NewsItem]:
    if not NEWSAPI_KEY:
        return []

    query = 'phishing OR malware OR ransomware OR "data breach" OR "cyber threat"'
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={quote_plus(query)}&language=en&sortBy=publishedAt&pageSize={max_items}&apiKey={quote_plus(NEWSAPI_KEY)}"
    )
    response = _request(url)
    response.raise_for_status()
    payload = response.json()
    articles = payload.get("articles", [])
    items: List[NewsItem] = []

    for article in articles[:max_items]:
        title = (article.get("title") or "").strip()
        link = (article.get("url") or "").strip()
        if not title or not link:
            continue
        items.append(
            NewsItem(
                headline=title,
                source=(article.get("source") or {}).get("name") or "NewsAPI",
                published=_format_published(article.get("publishedAt")),
                summary=_compact_summary(article.get("description") or article.get("content") or ""),
                link=link,
                topic="NewsAPI",
            )
        )

    return items


def _dedupe(items: List[NewsItem], max_items: int) -> List[NewsItem]:
    seen = set()
    unique: List[NewsItem] = []
    for item in items:
        fingerprint = (item.headline.lower(), item.link)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(item)
        if len(unique) >= max_items:
            break
    return unique


def _build_fallback_items(max_items: int) -> List[NewsItem]:
    return [
        NewsItem(
            headline="Cyber threat feed temporarily unavailable",
            source="PhishVision",
            published="Just now",
            summary="Live sources could not be reached. The dropdown will retry automatically and restore the latest cached stories when the feed becomes available again.",
            link="https://thehackernews.com/",
            topic="Fallback",
        ),
        NewsItem(
            headline="Monitor phishing, malware, ransomware, and breach alerts from trusted security sources",
            source="PhishVision",
            published="Just now",
            summary="When the feed recovers, the panel resumes showing fresh stories with source, time, summary, and an external read-more link without changing the dashboard layout.",
            link="https://www.bleepingcomputer.com/",
            topic="Fallback",
        ),
    ][:max_items]


def get_cyber_news(refresh_minutes: int = DEFAULT_REFRESH_MINUTES, max_items: int = 6, force_refresh: bool = False) -> dict:
    refresh_minutes = _clamp_refresh_minutes(refresh_minutes)
    max_items = max(1, int(max_items))
    key = _cache_key(refresh_minutes, max_items)
    ttl_seconds = refresh_minutes * 60
    now = time.time()
    cached = _NEWS_CACHE.get(key)

    if cached and not force_refresh and (now - cached["fetched_at"] < ttl_seconds):
        result = dict(cached)
        result["cached"] = True
        return result

    sources: List[NewsItem] = []
    errors: List[str] = []

    fetch_plan = [
        (lambda: _fetch_newsapi(max_items), "NewsAPI"),
        (lambda: _parse_rss_feed("https://feeds.feedburner.com/TheHackersNews", "The Hacker News", "Phishing / Malware / Ransomware", max_items), "The Hacker News"),
        (lambda: _parse_rss_feed("https://www.bleepingcomputer.com/feed/", "BleepingComputer", "Data Breach / Cyber Threats", max_items), "BleepingComputer"),
        (lambda: _parse_rss_feed(
            "https://news.google.com/rss/search?q=" + quote_plus('phishing malware ransomware "data breach" "cyber threat"') + "&hl=en-US&gl=US&ceid=US:en",
            "Google News",
            "Cyber Threat Search",
            max_items,
        ), "Google News"),
    ]

    for fetch_fn, label in fetch_plan:
        try:
            fetched = fetch_fn()
            if fetched:
                sources.extend(fetched)
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    items = _dedupe(sources, max_items)
    stale = False

    if not items and cached:
        items = cached.get("items", [])
        stale = True
    if not items:
        items = [asdict(item) for item in _build_fallback_items(max_items)]
        stale = True
    else:
        items = [asdict(item) for item in items]

    result = {
        "items": items,
        "fetched_at": now,
        "fetched_at_label": datetime.now().strftime("%b %d, %I:%M %p"),
        "cached": False,
        "stale": stale,
        "refresh_minutes": refresh_minutes,
        "errors": errors,
    }
    _NEWS_CACHE[key] = result
    return result