"""
V3 — Annotated stock chart with news/event lookup and LLM summaries.
- Accept ticker, date range, and N as function arguments
- Detect biggest price moves (consecutive same-direction spans)
- Search Google News for news around the start of each span
- Summarise the cause with g4f (free GPT)
- Render ECharts chart with event labels and rich tooltips
"""

import argparse
import webbrowser
from pathlib import Path
from typing import Optional

from cache import clear_cache
from data import download_prices, find_extreme_moves
from news import annotate_events
from render import render_html

OUTPUT = Path(__file__).parent / "chart.html"


def build_chart(
    ticker: str = "AAPL",
    start: Optional[str] = None,
    end: Optional[str] = None,
    min_pct: float = 5.0,
    top_n: Optional[int] = None,
    output: Optional[Path] = None,
    no_news: bool = False,
    noise_pct: float = 0.0,
) -> Path:
    """Download data, find extreme moves, and generate an annotated HTML chart.

    Args:
        ticker:    Stock ticker symbol (e.g. "AAPL").
        start:     Start date as "YYYY-MM-DD". Defaults to 1 year ago.
        end:       End date as "YYYY-MM-DD". Defaults to today.
        min_pct:   Minimum absolute % move for a span to be annotated (default 5.0).
        top_n:     Optional cap on number of annotations.
        output:    Path for the HTML file. Defaults to chart.html next to script.
        no_news:   If True, skip news search and LLM summarisation.
        noise_pct: Absorb daily counter-moves <= this %% into the trend (default 0).

    Returns:
        Path to the generated HTML file.
    """
    if output is None:
        output = OUTPUT

    df, range_label = download_prices(ticker, start, end)
    extreme_records = find_extreme_moves(df, min_pct=min_pct, top_n=top_n, noise_pct=noise_pct)

    print(f"{len(extreme_records)} moves >= {min_pct:g}%:")
    for r in extreme_records:
        span = f"{r['start_date']}→{r['end_date']}" if r["days"] > 1 else r["date"]
        print(f"  {span}  {r['pct']:+.1f}%  ({r['days']}d)")

    if not no_news and extreme_records:
        print("\nSearching news & summarising with LLM…")
        annotate_events(extreme_records, ticker)

    dates = df.index.strftime("%Y-%m-%d").tolist()
    prices = [round(float(v), 2) for v in df["Close"].values]
    render_html(ticker, range_label, dates, prices, extreme_records, output)
    print(f"Chart saved to {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Generate an annotated stock chart.")
    parser.add_argument("ticker", nargs="?", default="AAPL", help="Stock ticker symbol (default: AAPL)")
    parser.add_argument("--start", "-s", help="Start date YYYY-MM-DD (default: 1 year ago)")
    parser.add_argument("--end", "-e", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--min-pct", "-p", type=float, default=5.0, help="Min absolute %% move to annotate (default: 5.0)")
    parser.add_argument("--top", "-n", type=int, default=None, help="Max number of annotations (default: all above threshold)")
    parser.add_argument("--output", "-o", type=Path, help="Output HTML path (default: chart.html)")
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    parser.add_argument("--no-news", action="store_true", help="Skip news search & LLM summarisation")
    parser.add_argument("--noise-pct", type=float, default=1.0, help="Absorb daily counter-moves <= this %% into trend (default: 0)")
    parser.add_argument("--clear-cache", action="store_true", help="Delete cached data before running")
    args = parser.parse_args()

    if args.clear_cache:
        n = clear_cache(args.ticker)
        print(f"Cleared {n} cached file(s) for {args.ticker}")

    out = build_chart(args.ticker, args.start, args.end, args.min_pct, args.top, args.output, args.no_news, args.noise_pct)
    if not args.no_open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
