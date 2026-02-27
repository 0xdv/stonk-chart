"""
V1 — MVP: Detect biggest price moves and mark them on the chart.
- Accept ticker, date range, and N as function arguments
- Calculate daily percentage change, identify top-N absolute moves
- Use ECharts markPoint with colored markers (green ▲ / red ▼)
"""

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
        })
    return markers


def build_chart(
    ticker: str = "AAPL",
    start: Optional[str] = None,
    end: Optional[str] = None,
    top_n: int = 5,
    output: Optional[Path] = None,
) -> Path:
    """Download data, find extreme moves, and generate an annotated HTML chart.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        start:  Start date as "YYYY-MM-DD". Defaults to 1 year ago.
        end:    End date as "YYYY-MM-DD". Defaults to today.
        top_n:  Number of most extreme daily moves to highlight.
        output: Path for the HTML file. Defaults to chart.html next to script.

    Returns:
        Path to the generated HTML file.
    """
    if output is None:
        output = OUTPUT

    df, range_label = download_prices(ticker, start, end)
    extreme_records = find_extreme_moves(df, top_n)

    for r in extreme_records:
        span = f"{r['start_date']}→{r['end_date']}" if r["days"] > 1 else r["date"]
        print(f"  {span}  {r['pct']:+.1f}%  ({r['days']}d)")
    print(f"Top-{top_n} consecutive moves shown above.")

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
    out = build_chart()
    webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
