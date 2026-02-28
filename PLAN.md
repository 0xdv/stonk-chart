# Annotated Stock Chart — Incremental Build Plan

## Goal
Create a Python script that generates an **interactive HTML page** with an ECharts
stock price chart, highlighting the most dramatic price movements and labeling
them with relevant real-world events.

**Output format:** Self-contained `.html` file (no server needed, just open in browser).

### Implementation guideline
If any source file exceeds **150 lines**, treat it as a signal to split it into
smaller modules (e.g. separate data fetching, analysis, rendering, CLI).

---

## V0 — PoC (Proof of Concept)
**Goal:** Confirm we can download data and render an ECharts chart in HTML.
- Download OHLCV data via `yfinance` (hardcoded `AAPL`, last 1 year)
- Generate a self-contained HTML file with ECharts CDN
- Render a basic line chart of closing prices
- Open the file in the default browser
- **Output:** `chart.html` with an interactive price line

## V1 — MVP (Minimum Viable Product)
**Goal:** Detect biggest price moves and mark them on the chart.
- Accept ticker, date range, and N as function arguments
- Calculate daily percentage change
- Identify top-N absolute moves (up + down)
- Use ECharts `markPoint` to place colored markers (green ▲ / red ▼)
- **Output:** Interactive chart with clickable extreme-day markers

## V2 — Annotations
**Goal:** Add text labels to the markers.
- Labels = date + percent change (placeholder for real news)
- Use ECharts `markPoint.label` for inline text
- Rich tooltips on hover showing OHLCV data + % change
- **Output:** Chart with annotated markers and rich tooltips

## V3 — News / Event Lookup
**Goal:** Replace placeholder labels with real event descriptions.
- Use Google News RSS search (no API key)
- Query: `"{company name} stock {date}"` → extract top headline
- Truncate to ≤10 words
- Show event text in tooltip and as markPoint label
- Fallback: if no result, keep "date + %change"
- **Output:** Chart with real-world event annotations

## V4 — Smart Label Positioning
**Goal:** Readable labels even with many annotations.
- Alternate label placement above/below price line
- Use ECharts label `offset` and `position` to avoid overlap
- Add `markLine` vertical lines from annotation to x-axis
- Collapsible annotation list in a sidebar/legend
- **Output:** Clean, readable annotations with leader lines

## V5 — Professional Infographic Styling
**Goal:** Make it publication-quality interactive infographic.
- Dark/light theme toggle
- Gradient area fill under the price line
- DataZoom slider for date range selection
- Volume bars as secondary y-axis
- Custom color palette, typography via CSS
- Responsive layout (works on mobile)
- Title, subtitle with metadata (ticker, range, source)
- **Output:** Polished, interactive HTML infographic

## V6 — CLI + Final Polish
**Goal:** Usable as a command-line tool.
- `argparse` CLI: `python chart.py AAPL --start 2023-01-01 --end 2024-01-01 --top 5`
- `--output chart.html` path for the HTML file
- `--no-news` flag to skip slow web lookups
- `--open` flag to auto-open in browser (default: true)
- Error handling, progress bar, caching of downloaded data
- Docstrings, type hints, clean structure
- **Output:** Complete, distributable script
