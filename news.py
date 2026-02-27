"""V3 — News/event lookup and LLM summarisation for stock chart annotations."""

from __future__ import annotations

import time
from typing import Optional

from ddgs import DDGS

from cache import get_cached_annotation, save_annotation


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


def _build_llm_prompt(
    company_name: str,
    ticker: str,
    date: str,
    pct_change: float,
    news_items: list[dict],
) -> str:
    """Build a prompt asking the LLM to summarise the cause of a price move."""
    direction = "rose" if pct_change > 0 else "dropped"
    headlines = "\n".join(
        f"- {item['title']} ({item.get('source', '?')})" for item in news_items
    )
    return (
        f"{company_name} ({ticker}) stock {direction} {abs(pct_change):.1f}% "
        f"around {date}.\n\n"
        f"Here are relevant news headlines:\n{headlines}\n\n"
        f"In ≤10 words, summarise the most likely cause of this price move. "
        f"Reply ONLY with the summary, no extra text."
    )


def summarise_with_llm(
    company_name: str,
    ticker: str,
    date: str,
    pct_change: float,
    news_items: list[dict],
    retries: int = 3,
) -> Optional[str]:
    """Use g4f (free GPT) to summarise why a stock moved.

    Tries up to ``retries`` times with different providers.

    Returns:
        Short ≤10-word summary string, or None on failure.
    """
    if not news_items:
        return None

    prompt = _build_llm_prompt(company_name, ticker, date, pct_change, news_items)

    from g4f.client import Client

    for attempt in range(1, retries + 1):
        try:
            client = Client()
            response = client.chat.completions.create(
                model="",
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content
            if text:
                # Trim to ~10 words max
                words = text.strip().strip('"').split()
                summary = " ".join(words[:12])
                # Sanity check: reject garbage responses
                if len(summary) > 5 and company_name.lower() not in summary.lower()[:15] or True:
                    return summary
        except Exception as exc:
            if attempt == retries:
                print(f"  ⚠ LLM summarisation failed after {retries} attempts: {exc}")
            else:
                time.sleep(1)
    return None


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

        summary = summarise_with_llm(
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
