"""
V1 — MVP: Detect biggest price moves and mark them on the chart.
- Accept ticker, date range, and N as function arguments
- Calculate daily percentage change, identify top-N absolute moves
- Use ECharts markPoint with colored markers (green ▲ / red ▼)
"""

import argparse
import json
import webbrowser
from pathlib import Path
from typing import Optional

from data import download_prices, find_extreme_moves
from template import HTML_TEMPLATE

OUTPUT = Path(__file__).parent / "chart.html"


def _build_markers(extreme_records: list[dict]) -> list[dict]:
    """Convert extreme-move span records into ECharts markPoint data."""
    markers = []
    for rec in extreme_records:
        is_up = rec["pct"] > 0
        days = rec["days"]
        label_text = f"{rec['pct']:+.1f}% ({days}d)"
        start = rec["start_date"]
        end = rec["end_date"]
        span_str = f"{start} → {end}" if start != end else start
        tooltip_html = (
            f"<b>{span_str}</b><br/>"
            f"{'▲' if is_up else '▼'} {rec['pct']:+.1f}% over {days} day{'s' if days > 1 else ''}<br/>"
            f"Close: ${rec['price']:.2f}"
        )
        markers.append({
            "coord": [rec["date"], rec["price"]],
            "value": label_text,
            "symbol": "triangle",
            "symbolSize": 20,
            "symbolRotate": 0 if is_up else 180,
            "itemStyle": {"color": "#00e676" if is_up else "#ff1744"},
            "label": {
                "show": True,
                "position": "top" if is_up else "bottom",
                "formatter": label_text,
                "color": "#00e676" if is_up else "#ff1744",
                "fontSize": 11,
                "fontWeight": "bold",
            },
            "tooltip": {"formatter": tooltip_html},
        })
    return markers


def build_chart(
    ticker: str = "AAPL",
    start: Optional[str] = None,
    end: Optional[str] = None,
    min_pct: float = 5.0,
    top_n: Optional[int] = None,
    output: Optional[Path] = None,
) -> Path:
    """Download data, find extreme moves, and generate an annotated HTML chart.

    Args:
        ticker:  Stock ticker symbol (e.g. "AAPL").
        start:   Start date as "YYYY-MM-DD". Defaults to 1 year ago.
        end:     End date as "YYYY-MM-DD". Defaults to today.
        min_pct: Minimum absolute % move for a span to be annotated (default 5.0).
        top_n:   Optional cap on number of annotations.
        output:  Path for the HTML file. Defaults to chart.html next to script.

    Returns:
        Path to the generated HTML file.
    """
    if output is None:
        output = OUTPUT

    df, range_label = download_prices(ticker, start, end)
    extreme_records = find_extreme_moves(df, min_pct=min_pct, top_n=top_n)

    print(f"{len(extreme_records)} moves >= {min_pct:g}%:")
    for r in extreme_records:
        span = f"{r['start_date']}→{r['end_date']}" if r["days"] > 1 else r["date"]
        print(f"  {span}  {r['pct']:+.1f}%  ({r['days']}d)")

    dates = df.index.strftime("%Y-%m-%d").tolist()
    prices = [round(float(v), 2) for v in df["Close"].values]
    markers = _build_markers(extreme_records)

    html = HTML_TEMPLATE.format(
        ticker=ticker,
        range_label=range_label,
        dates=json.dumps(dates),
        prices=json.dumps(prices),
        markers=json.dumps(markers),
    )

    output.write_text(html)
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
    args = parser.parse_args()

    out = build_chart(args.ticker, args.start, args.end, args.min_pct, args.top, args.output)
    if not args.no_open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
