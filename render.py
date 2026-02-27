"""ECharts marker/renderer helpers for the annotated stock chart."""

import json
from pathlib import Path
from typing import Optional

from template import HTML_TEMPLATE


def build_spans(extreme_records: list[dict]) -> list[dict]:
    """Extract span start/end/direction for JS-side gradient markArea rendering."""
    return [
        {"start": rec["start_date"], "end": rec["end_date"], "up": rec["pct"] > 0}
        for rec in extreme_records
    ]


def build_markers(extreme_records: list[dict]) -> list[dict]:
    """Convert extreme-move span records into ECharts markPoint data."""
    markers = []
    for rec in extreme_records:
        is_up = rec["pct"] > 0
        days = rec["days"]
        event = rec.get("event", "")
        headlines = rec.get("headlines", [])

        label_text = event if event else f"{rec['pct']:+.1f}%"
        start = rec["start_date"]
        end = rec["end_date"]
        span_str = f"{start} → {end}" if start != end else start

        headlines_html = "".join(
            f"<br/>• {h}" for h in headlines
        )
        tooltip_html = (
            f"<b>{span_str}</b><br/>"
            f"{'▲' if is_up else '▼'} {rec['pct']:+.1f}% over {days} day{'s' if days > 1 else ''}<br/>"
            f"Close: ${rec['price']:.2f}<br/>"
            f"<br/><b>{event}</b>"
            f"{headlines_html}"
        )
        markers.append({
            "coord": [rec["date"], rec["price"]],
            "value": label_text,
            "symbol": "triangle",
            "symbolSize": 10,
            "symbolRotate": 0 if is_up else 180,
            "itemStyle": {"color": "#00e676" if is_up else "#ff1744"},
            "label": {
                "show": True,
                "position": "top" if is_up else "bottom",
                "formatter": label_text,
                "color": "#00e676" if is_up else "#ff1744",
                "fontSize": 11,
                "fontWeight": "bold",
                "backgroundColor": "rgba(26,26,46,0.72)",
                "borderRadius": 4,
                "padding": [3, 6],
            },
            "tooltip": {"formatter": tooltip_html},
        })
    return markers


def render_html(
    ticker: str,
    range_label: str,
    dates: list[str],
    prices: list[float],
    extreme_records: list[dict],
    output: Path,
) -> None:
    """Render the annotated ECharts HTML file to disk.

    Args:
        ticker:          Stock ticker symbol.
        range_label:     Human-readable date range string.
        dates:           List of ISO date strings for the x-axis.
        prices:          List of closing prices.
        extreme_records: Span records from find_extreme_moves (may include events).
        output:          Path to write the HTML file.
    """
    markers = build_markers(extreme_records)
    spans = build_spans(extreme_records)
    html = HTML_TEMPLATE.format(
        ticker=ticker,
        range_label=range_label,
        dates=json.dumps(dates),
        prices=json.dumps(prices),
        markers=json.dumps(markers),
        spans=json.dumps(spans),
    )
    output.write_text(html)
