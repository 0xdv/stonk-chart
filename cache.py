"""Two-layer file cache for price data and news/LLM annotations.

Prices  →  cache/{TICKER}_{start}_{end}.csv
Annotations  →  cache/{TICKER}_annotations.json
    keyed by "start_date|end_date" so the same span is never re-queried.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

CACHE_DIR = Path(__file__).parent / "cache"


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(exist_ok=True)


# ── Price cache ─────────────────────────────────────────────────────────

def _prices_path(ticker: str, start: str, end: str) -> Path:
    return CACHE_DIR / f"{ticker}_{start}_{end}.csv"


def load_prices(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """Return cached DataFrame or None."""
    path = _prices_path(ticker, start, end)
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def save_prices(ticker: str, start: str, end: str, df: pd.DataFrame) -> None:
    _ensure_cache_dir()
    df.to_csv(_prices_path(ticker, start, end))


# ── Annotation cache ───────────────────────────────────────────────────

def _annotations_path(ticker: str) -> Path:
    return CACHE_DIR / f"{ticker}_annotations.json"


def _load_annotations_store(ticker: str) -> dict:
    path = _annotations_path(ticker)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_annotations_store(ticker: str, store: dict) -> None:
    _ensure_cache_dir()
    with _annotations_path(ticker).open("w") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def _span_key(rec: dict) -> str:
    return f"{rec['start_date']}|{rec['end_date']}"


def get_cached_annotation(ticker: str, rec: dict) -> Optional[dict]:
    """Return cached {event, headlines} for a span, or None."""
    store = _load_annotations_store(ticker)
    return store.get(_span_key(rec))


def save_annotation(ticker: str, rec: dict) -> None:
    """Persist event + headlines for one span."""
    store = _load_annotations_store(ticker)
    store[_span_key(rec)] = {
        "event": rec.get("event", ""),
        "headlines": rec.get("headlines", []),
    }
    _save_annotations_store(ticker, store)


def clear_cache(ticker: Optional[str] = None) -> int:
    """Delete cached files.  If ticker is given, only that ticker's files.

    Returns number of files removed.
    """
    if not CACHE_DIR.exists():
        return 0

    removed = 0
    pattern = f"{ticker}_*" if ticker else "*"
    for f in CACHE_DIR.glob(pattern):
        f.unlink()
        removed += 1
    return removed
