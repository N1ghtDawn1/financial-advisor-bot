"""I load, validate and enrich chronological OHLCV market data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import math
import random


REQUIRED_COLUMNS = ("date", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class MarketRow:
    """I keep one immutable observation with reproducible technical indicators."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    sma_10: float
    delta_sma: float
    rsi_14: float


def generate_sample_csv(path: Path, periods: int = 180, seed: int = 42) -> None:
    """I generate a deterministic educational price series without a live-data dependency."""
    rng = random.Random(seed)
    start = date(2025, 1, 2)
    price = 100.0
    rows: list[dict[str, object]] = []
    current = start
    for index in range(periods):
        while current.weekday() >= 5:
            current += timedelta(days=1)
        regime = 0.0008 if index < 55 else (-0.0012 if index < 105 else 0.0010)
        shock = rng.gauss(regime, 0.014)
        open_price = price * (1 + rng.gauss(0, 0.003))
        close = max(15.0, price * (1 + shock))
        high = max(open_price, close) * (1 + abs(rng.gauss(0.004, 0.003)))
        low = min(open_price, close) * (1 - abs(rng.gauss(0.004, 0.003)))
        rows.append(
            {
                "date": current.isoformat(),
                "open": f"{open_price:.2f}",
                "high": f"{high:.2f}",
                "low": f"{low:.2f}",
                "close": f"{close:.2f}",
                "volume": int(800_000 + rng.random() * 1_400_000),
            }
        )
        price = close
        current += timedelta(days=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _rsi(closes: list[float], index: int, period: int = 14) -> float:
    """I calculate a simple fourteen-period RSI for one observation."""
    changes = [closes[i] - closes[i - 1] for i in range(index - period + 1, index + 1)]
    gains = sum(max(change, 0.0) for change in changes) / period
    losses = sum(max(-change, 0.0) for change in changes) / period
    if losses == 0:
        return 100.0
    relative_strength = gains / losses
    return 100.0 - (100.0 / (1.0 + relative_strength))


def load_market_data(path: Path) -> list[MarketRow]:
    """I validate schema, types, chronology and indicator warm-up rows."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError(f"I require columns in this order: {', '.join(REQUIRED_COLUMNS)}")
        raw = list(reader)
    if len(raw) < 30:
        raise ValueError("I require at least 30 chronological observations.")
    parsed: list[dict[str, object]] = []
    previous_date = ""
    for row in raw:
        current_date = str(row["date"])
        if current_date <= previous_date:
            raise ValueError("I require unique dates in ascending chronological order.")
        previous_date = current_date
        numeric = {name: float(row[name]) for name in ("open", "high", "low", "close")}
        if not all(math.isfinite(value) and value > 0 for value in numeric.values()):
            raise ValueError(f"I found an invalid price on {current_date}.")
        if numeric["high"] < max(numeric["open"], numeric["close"]):
            raise ValueError(f"I found a high-price inconsistency on {current_date}.")
        if numeric["low"] > min(numeric["open"], numeric["close"]):
            raise ValueError(f"I found a low-price inconsistency on {current_date}.")
        parsed.append({"date": current_date, **numeric, "volume": int(row["volume"])})
    closes = [float(row["close"]) for row in parsed]
    enriched: list[MarketRow] = []
    for index in range(14, len(parsed)):
        row = parsed[index]
        sma = sum(closes[index - 9 : index + 1]) / 10
        close = closes[index]
        enriched.append(
            MarketRow(
                date=str(row["date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=close,
                volume=int(row["volume"]),
                sma_10=sma,
                delta_sma=(close - sma) / sma,
                rsi_14=_rsi(closes, index),
            )
        )
    return enriched
