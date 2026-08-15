"""I evaluate policies, produce ledgers and calculate risk-aware metrics."""

from __future__ import annotations

import math
from statistics import mean, pstdev
from .data_pipeline import MarketRow
from .environment import TradingEnvironment
from .explanations import explain


def metrics(values: list[float], initial: float) -> dict[str, float]:
    """I calculate return, annualised volatility, Sharpe ratio and drawdown."""
    returns = [values[i] / values[i - 1] - 1 for i in range(1, len(values)) if values[i - 1]]
    volatility = pstdev(returns) * math.sqrt(252) if len(returns) > 1 else 0.0
    sharpe = (mean(returns) / pstdev(returns) * math.sqrt(252)) if len(returns) > 1 and pstdev(returns) else 0.0
    peak = initial
    maximum_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        maximum_drawdown = min(maximum_drawdown, value / peak - 1)
    return {
        "total_return_pct": (values[-1] / initial - 1) * 100,
        "annualised_volatility_pct": volatility * 100,
        "sharpe_ratio": sharpe,
        "maximum_drawdown_pct": maximum_drawdown * 100,
    }


def run_policy(rows: list[MarketRow], policy, initial_cash: float = 10_000.0, fee_rate: float = 0.001) -> dict[str, object]:
    """I execute a frozen policy and retain one source of truth for the dashboard."""
    environment = TradingEnvironment(rows, initial_cash, fee_rate)
    row = environment.reset()
    records: list[dict[str, object]] = []
    while True:
        action = policy.act(row)
        next_row, _, done, transition = environment.step(action)
        explanation, matched_rules = explain(transition, policy.name)
        record = transition.to_dict()
        record.update({"action_name": ("Hold", "Buy", "Sell")[transition.executed_action], "explanation": explanation, "matched_rules": matched_rules})
        records.append(record)
        if done:
            break
        row = next_row
    values = [initial_cash] + [float(record["portfolio_value"]) for record in records]
    summary = metrics(values, initial_cash)
    summary.update({"final_value": values[-1], "trades": sum(int(record["quantity"]) > 0 for record in records), "fees": sum(float(record["fee"]) for record in records)})
    return {"policy": policy.name, "summary": summary, "records": records}
