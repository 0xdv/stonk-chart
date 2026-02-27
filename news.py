"""V3 — News/event lookup and LLM summarisation for stock chart annotations."""

from __future__ import annotations

import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from xml.etree import ElementTree

from cache import get_cached_annotation, save_annotation
from llm import summarise


def search_news(
    company_name: str,
    date: str,
    max_results: int = 5,
    window_days: int = 3,
) -> list[dict]:
    """Search Google News RSS for a company around a specific date.

    Uses Google News RSS with ``after:/before:`` date operators so results
    actually fall within a window around the target date.

    Args:
        company_name: Human-readable company name (e.g. "Apple").
        date: Date string "YYYY-MM-DD".
        max_results: Number of results to fetch.
        window_days: Days before/after *date* to include.

    Returns:
        List of dicts with keys: title, body, url, date, source.
    """
    dt = datetime.strptime(date, "%Y-%m-%d")
    after = (dt - timedelta(days=window_days)).strftime("%Y-%m-%d")
    before = (dt + timedelta(days=window_days)).strftime("%Y-%m-%d")
    raw_query = f"{company_name} stock"
    query = urllib.parse.quote(raw_query)
    url = (
        f"https://news.google.com/rss/search?"
        f"q={query}+after:{after}+before:{before}"
        f"&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        xml_bytes = resp.read()
        root = ElementTree.fromstring(xml_bytes)

        results: list[dict] = []
        for item in root.findall(".//item"):
            title_raw = item.findtext("title", "")
            source = item.findtext("source", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            # Google News appends " - Source" to titles; strip it
            title = title_raw.rsplit(" - ", 1)[0] if " - " in title_raw else title_raw
            results.append({
                "title": title,
                "body": "",
                "url": link,
                "date": pub_date,
                "source": source,
            })
            if len(results) >= max_results:
                break

        return results
    except Exception as exc:
        print(f"  ⚠ Google News search failed for '{raw_query}' ({date}): {exc}")
        return []


def annotate_events(
    records: list[dict],
    ticker: str,
    company_name: Optional[str] = None,
    delay: float = 1.0,
) -> list[dict]:
    """Enrich extreme-move records with news headlines and LLM summaries.

    For each record, searches DuckDuckGo for news around the *start* date
    of the price span, then asks an LLM to summarise the cause.

    Args:
        records: List of span dicts from find_extreme_moves().
        ticker: Stock ticker symbol.
        company_name: Human-readable name. If None, uses ticker.
        delay: Seconds to wait between API calls (rate-limit courtesy).

    Returns:
        Same list, with added keys ``event`` and ``headlines`` on each record.
    """
    if company_name is None:
        company_name = ticker

    total = len(records)
    cached_count = 0
    for i, rec in enumerate(records, 1):
        # Check annotation cache first
        cached = get_cached_annotation(ticker, rec)
        if cached is not None:
            rec["event"] = cached["event"]
            rec["headlines"] = cached["headlines"]
            cached_count += 1
            print(f"  [{i}/{total}] Cached: {rec['event']}")
            continue

        search_date = rec["start_date"]
        print(f"  [{i}/{total}] Searching news for {search_date} ({rec['pct']:+.1f}%)…")

        news = search_news(company_name, search_date)
        if news:
            print(f"         News articles found ({len(news)}):")
            for n in news:
                art_date = n.get("date", "?")
                source = n.get("source", "?")
                title = n.get("title", "")
                print(f"           [{art_date}] [{source}] {title}")
        else:
            print(f"         No news articles found.")
        rec["headlines"] = [
            f"[{n['source']}] {n['title']}" if n.get("source") else n["title"]
            for n in news[:3]
        ]

        summary = summarise(
            company_name, ticker, search_date, rec["pct"], news
        )
        rec["event"] = summary or f"{rec['pct']:+.1f}% move"

        # Persist to cache
        save_annotation(ticker, rec)

        print(f"         → {rec['event']}")

        if i < total:
            time.sleep(delay)

    if cached_count:
        print(f"  ({cached_count}/{total} loaded from cache)")

    return records
