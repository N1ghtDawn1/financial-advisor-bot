"""I provide reproducible baseline and tabular reinforcement-learning policies."""

from __future__ import annotations

import random
from .data_pipeline import MarketRow
from .environment import BUY, HOLD, SELL


def discretise(row: MarketRow) -> tuple[int, int]:
    """I compress SMA deviation and RSI into an interpretable state."""
    trend = -1 if row.delta_sma < -0.015 else (1 if row.delta_sma > 0.015 else 0)
    momentum = -1 if row.rsi_14 < 40 else (1 if row.rsi_14 > 60 else 0)
    return trend, momentum


class IndicatorPolicy:
    """I use transparent thresholds as a deterministic baseline."""

    name = "Indicator baseline"

    def act(self, row: MarketRow) -> int:
        """I buy oversold states, sell overbought states and otherwise hold."""
        if row.delta_sma <= -0.015 or row.rsi_14 < 40:
            return BUY
        if row.delta_sma >= 0.018 or row.rsi_14 > 62:
            return SELL
        return HOLD


class QLearningPolicy:
    """I learn action values from repeated chronological training episodes."""

    name = "Q-learning agent"

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.q: dict[tuple[int, int], list[float]] = {}

    def values(self, row: MarketRow) -> list[float]:
        """I return the three action values for the row's discretised state."""
        return self.q.setdefault(discretise(row), [0.0, 0.0, 0.0])

    def act(self, row: MarketRow, epsilon: float = 0.0) -> int:
        """I select an exploratory or highest-valued action reproducibly."""
        if self.rng.random() < epsilon:
            return self.rng.choice([HOLD, BUY, SELL])
        values = self.values(row)
        return max(range(3), key=lambda action: (values[action], -action))

    def update(self, row: MarketRow, action: int, reward: float, next_row: MarketRow | None, alpha: float = 0.15, gamma: float = 0.97) -> None:
        """I apply the standard one-step Q-learning update."""
        values = self.values(row)
        target = reward if next_row is None else reward + gamma * max(self.values(next_row))
        values[action] += alpha * (target - values[action])
