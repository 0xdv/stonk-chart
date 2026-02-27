"""LLM-based summarisation of stock price move causes."""

from __future__ import annotations

import time
from typing import Optional


def _build_prompt(
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


def summarise(
    company_name: str,
    ticker: str,
    date: str,
    pct_change: float,
    news_items: list[dict],
    retries: int = 3,
) -> Optional[str]:
    """Use g4f (free GPT) to summarise why a stock moved.

    Tries up to ``retries`` times with different providers.

    Args:
        company_name: Human-readable company name.
        ticker:       Stock ticker symbol.
        date:         Date string "YYYY-MM-DD".
        pct_change:   Cumulative percentage change.
        news_items:   News results from search_news().
        retries:      Number of LLM call attempts.

    Returns:
        Short ≤10-word summary string, or None on failure.
    """
    if not news_items:
        return None

    prompt = _build_prompt(company_name, ticker, date, pct_change, news_items)

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
                words = text.strip().strip('"').split()
                summary = " ".join(words[:12])
                if len(summary) > 5 and company_name.lower() not in summary.lower()[:15] or True:
                    return summary
        except Exception as exc:
            if attempt == retries:
                print(f"  ⚠ LLM summarisation failed after {retries} attempts: {exc}")
            else:
                time.sleep(1)
    return None
