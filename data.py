"""Data fetching and analysis for the annotated stock chart."""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf


def download_prices(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """Download OHLCV data and return (DataFrame, range_label).

    Args:
        ticker: Stock ticker symbol.
        start:  Start date "YYYY-MM-DD". Defaults to 1 year ago.
        end:    End date "YYYY-MM-DD". Defaults to today.

    Returns:
        Tuple of (price DataFrame with flat columns, human-readable range label).
    """
    end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.today()
    start_dt = datetime.strptime(start, "%Y-%m-%d") if start else end_dt - timedelta(days=365)
    range_label = f"{start_dt:%Y-%m-%d} → {end_dt:%Y-%m-%d}"

    print(f"Downloading {ticker} data ({range_label})…")
    df = yf.download(ticker, start=start_dt, end=end_dt, auto_adjust=True)
    if df.empty:
        raise SystemExit(f"No data returned for {ticker}")

    # yfinance may return MultiIndex columns; flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df, range_label


def find_extreme_moves(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """Identify the top-N most extreme *consecutive* price moves.

    A "span" is a streak of consecutive trading days where the daily
    change stays in the same direction (all positive or all negative).
    Spans are ranked by absolute cumulative percentage change.

    Args:
        df:    DataFrame with a "Close" column (DatetimeIndex).
        top_n: Number of extreme spans to return.

    Returns:
        List of dicts with keys:
            start_date, end_date, date (=end_date, for marker placement),
            price (close at end), pct (cumulative %), days.
    """
    daily_pct = df["Close"].pct_change()
    signs = daily_pct.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    # group consecutive same-sign days into spans
    spans: list[dict] = []
    span_start = None
    prev_sign = 0

    for idx, sign in signs.items():
        if sign == 0:
            continue
        if sign != prev_sign:
            # close previous span
            if span_start is not None:
                spans.append(_make_span(df, span_start, prev_idx))
            span_start = idx
        prev_sign = sign
        prev_idx = idx

    # close last span
    if span_start is not None:
        spans.append(_make_span(df, span_start, prev_idx))

    # rank by absolute cumulative move
    spans.sort(key=lambda s: abs(s["pct"]), reverse=True)
    return spans[:top_n]


def _make_span(df: pd.DataFrame, start, end) -> dict:
    """Build a span record from start/end index labels."""
    close_before = float(df["Close"].shift(1).loc[start])
    close_end = float(df.loc[end, "Close"])
    pct = ((close_end - close_before) / close_before) * 100
    mask = (df.index >= start) & (df.index <= end)
    days = int(mask.sum())
    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "date": end.strftime("%Y-%m-%d"),   # marker placement
        "price": close_end,
        "pct": round(pct, 2),
        "days": days,
    }
