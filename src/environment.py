"""I implement a long-only single-asset trading environment with an auditable ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from .data_pipeline import MarketRow


HOLD, BUY, SELL = 0, 1, 2
ACTION_NAMES = {HOLD: "Hold", BUY: "Buy", SELL: "Sell"}


@dataclass(frozen=True)
class Transition:
    """I record every value needed to reconcile one simulated decision."""

    date: str
    close: float
    sma_10: float
    delta_sma: float
    rsi_14: float
    requested_action: int
    executed_action: int
    quantity: int
    fee: float
    cash_before: float
    cash_after: float
    holdings_before: int
    holdings_after: int
    portfolio_value: float
    reward: float
    rejected_reason: str

    def to_dict(self) -> dict[str, object]:
        """I convert the immutable record for JSON and CSV output."""
        return asdict(self)


class TradingEnvironment:
    """I simulate fixed-size trades with fees and explicit invalid-action handling."""

    def __init__(self, rows: list[MarketRow], initial_cash: float = 10_000.0, fee_rate: float = 0.001):
        if len(rows) < 2:
            raise ValueError("I require at least two market rows.")
        self.rows = rows
        self.initial_cash = float(initial_cash)
        self.fee_rate = float(fee_rate)
        self.reset()

    def reset(self) -> MarketRow:
        """I restore the initial portfolio and return the first observation."""
        self.index = 0
        self.cash = self.initial_cash
        self.holdings = 0
        self.previous_value = self.initial_cash
        self.ledger: list[Transition] = []
        return self.rows[0]

    def step(self, action: int) -> tuple[MarketRow | None, float, bool, Transition]:
        """I execute one action at the current close and then advance chronologically."""
        if action not in ACTION_NAMES:
            raise ValueError(f"I reject unknown action token {action}.")
        row = self.rows[self.index]
        cash_before, holdings_before = self.cash, self.holdings
        executed, quantity, fee, rejected = action, 0, 0.0, ""
        if action == BUY:
            unit_cost = row.close * (1 + self.fee_rate)
            if self.cash >= unit_cost:
                quantity = max(1, int((self.cash * 0.25) // unit_cost))
                fee = quantity * row.close * self.fee_rate
                self.cash -= quantity * row.close + fee
                self.holdings += quantity
            else:
                executed, rejected = HOLD, "Insufficient cash"
        elif action == SELL:
            if self.holdings > 0:
                quantity = max(1, self.holdings // 2)
                fee = quantity * row.close * self.fee_rate
                self.cash += quantity * row.close - fee
                self.holdings -= quantity
            else:
                executed, rejected = HOLD, "No holdings available"
        portfolio_value = self.cash + self.holdings * row.close
        reward = portfolio_value - self.previous_value
        self.previous_value = portfolio_value
        transition = Transition(
            date=row.date,
            close=row.close,
            sma_10=row.sma_10,
            delta_sma=row.delta_sma,
            rsi_14=row.rsi_14,
            requested_action=action,
            executed_action=executed,
            quantity=quantity,
            fee=fee,
            cash_before=cash_before,
            cash_after=self.cash,
            holdings_before=holdings_before,
            holdings_after=self.holdings,
            portfolio_value=portfolio_value,
            reward=reward,
            rejected_reason=rejected,
        )
        self.ledger.append(transition)
        self.index += 1
        done = self.index >= len(self.rows)
        return (None if done else self.rows[self.index], reward, done, transition)
