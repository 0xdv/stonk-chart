"""Data fetching and analysis for the annotated stock chart."""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from cache import load_prices, save_prices


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
    start_str = f"{start_dt:%Y-%m-%d}"
    end_str = f"{end_dt:%Y-%m-%d}"

    cached = load_prices(ticker, start_str, end_str)
    if cached is not None:
        print(f"Using cached {ticker} data ({range_label})")
        return cached, range_label

    print(f"Downloading {ticker} data ({range_label})…")
    df = yf.download(ticker, start=start_dt, end=end_dt, auto_adjust=True)
    if df.empty:
        raise SystemExit(f"No data returned for {ticker}")

    # yfinance may return MultiIndex columns; flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    save_prices(ticker, start_str, end_str, df)
    return df, range_label


def find_extreme_moves(
    df: pd.DataFrame,
    min_pct: float = 5.0,
    top_n: Optional[int] = None,
    noise_pct: float = 0.0,
) -> list[dict]:
    """Identify all *consecutive* price moves that exceed a minimum threshold.

    A "span" is a streak of consecutive trading days where the daily
    change stays in the same direction (all positive or all negative).
    All spans whose absolute cumulative move >= min_pct are returned,
    sorted by absolute move descending.  Pass top_n to cap the result.

    Args:
        df:        DataFrame with a "Close" column (DatetimeIndex).
        min_pct:   Minimum absolute cumulative % move to include (default 5.0).
        top_n:     Optional hard cap on number of results.
        noise_pct: Ignore daily counter-moves smaller than this %% (default 0.0).
                   E.g. noise_pct=1.0 absorbs ±1% blips into the prevailing trend.

    Returns:
        List of dicts with keys:
            start_date, end_date, date (=end_date, for marker placement),
            price (close at end), pct (cumulative %), days.
    """
    daily_pct = df["Close"].pct_change() * 100  # in percent

    # group consecutive same-direction days into spans,
    # treating small counter-moves (<= noise_pct) as continuation
    spans: list[dict] = []
    span_start = None
    prev_sign = 0

    for idx, pct_val in daily_pct.items():
        if pct_val == 0 or pd.isna(pct_val):
            continue
        sign = 1 if pct_val > 0 else -1

        if sign != prev_sign and prev_sign != 0:
            # counter-move: absorb if it's just noise
            if abs(pct_val) <= noise_pct:
                # keep prev_sign, extend the span
                prev_idx = idx
                continue
            # real reversal — close previous span
            if span_start is not None:
                spans.append(_make_span(df, span_start, prev_idx))
            span_start = idx
        elif span_start is None:
            span_start = idx

        prev_sign = sign
        prev_idx = idx

    # close last span
    if span_start is not None:
        spans.append(_make_span(df, span_start, prev_idx))

    # filter by threshold, then rank by absolute cumulative move
    spans = [s for s in spans if abs(s["pct"]) >= min_pct]
    spans.sort(key=lambda s: abs(s["pct"]), reverse=True)
    if top_n is not None:
        spans = spans[:top_n]
    return spans


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
