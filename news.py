"""V3 — News/event lookup and LLM summarisation for stock chart annotations."""

from __future__ import annotations

import time
from typing import Optional

from ddgs import DDGS

from cache import get_cached_annotation, save_annotation
from llm import summarise


def search_news(
    company_name: str,
    date: str,
    max_results: int = 5,
) -> list[dict]:
    """Search DuckDuckGo news for a company around a specific date.

    Args:
        company_name: Human-readable company name (e.g. "Apple").
        date: Date string "YYYY-MM-DD".
        max_results: Number of results to fetch.

    Returns:
        List of dicts with keys: title, body, url, date, source.
    """
    query = f"{company_name} stock {date}"
    try:
        results = DDGS().news(query, max_results=max_results)
        return results
    except Exception as exc:
        print(f"  ⚠ DuckDuckGo search failed for '{query}': {exc}")
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
        rec["headlines"] = [n["title"] for n in news[:3]]

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
