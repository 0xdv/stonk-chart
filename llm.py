"""LLM-based summarisation of stock price move causes."""

from __future__ import annotations

import random
import time
from typing import Optional

_SMART_MODELS = [
    "gpt-4o",
    "gpt-4.1",
    "gemini-2.5-pro",
    "grok-3",
    "deepseek-r1",
    "o3-mini",
]


_MAX_BODY_CHARS = 300  # max chars of body text per news item


def _build_prompt(
    company_name: str,
    ticker: str,
    date: str,
    pct_change: float,
    news_items: list[dict],
) -> str:
    """Build a prompt asking the LLM to identify the cause of a price move."""
    direction = "rose" if pct_change > 0 else "dropped"

    news_blocks = []
    for item in news_items:
        title = item.get("title", "").strip()
        body = item.get("body", item.get("text", item.get("summary", ""))).strip()
        source = item.get("source", "?")
        if body:
            body_snippet = body[:_MAX_BODY_CHARS]
            if len(body) > _MAX_BODY_CHARS:
                body_snippet += "…"
            news_blocks.append(f"[{source}] {title}\n  {body_snippet}")
        else:
            news_blocks.append(f"[{source}] {title}")

    news_text = "\n\n".join(news_blocks)

    return (
        f"On {date}, {company_name} ({ticker}) stock {direction} {abs(pct_change):.1f}%.\n\n"
        f"Your task: identify the ROOT CAUSE of this price move based on the news below.\n\n"
        f"News articles:\n{news_text}\n\n"
        f"Instructions:\n"
        f"- Focus on the specific event, announcement, or factor that most directly caused the move.\n"
        f"- If multiple causes, pick the most impactful one.\n"
        f"- Reply in ≤10 words. No intro, no explanation, just the cause.\n"
        f"Cause:"
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

    print(prompt)

    from g4f.client import Client

    for attempt in range(1, retries + 1):
        try:
            client = Client()
            response = client.chat.completions.create(
                # model=random.choice(_SMART_MODELS),
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
