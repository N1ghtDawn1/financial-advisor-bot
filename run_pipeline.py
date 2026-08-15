"""I train, evaluate and export the complete simulated-advisor evidence bundle."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.agents import IndicatorPolicy, QLearningPolicy
from src.data_pipeline import generate_sample_csv, load_market_data
from src.environment import TradingEnvironment
from src.evaluation import metrics, run_policy


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "sample_market.csv"
RESULTS = ROOT / "results"


def train_q_learning(rows, episodes: int = 180) -> QLearningPolicy:
    """I train only on the chronological training interval with fixed seeds."""
    agent = QLearningPolicy(seed=42)
    for episode in range(episodes):
        environment = TradingEnvironment(rows)
        row = environment.reset()
        epsilon = max(0.03, 0.35 * (1 - episode / episodes))
        while True:
            action = agent.act(row, epsilon=epsilon)
            next_row, reward, done, _ = environment.step(action)
            agent.update(row, action, reward, next_row)
            if done:
                break
            row = next_row
    return agent


def buy_and_hold(rows, initial: float = 10_000.0) -> dict[str, object]:
    """I calculate the passive benchmark on the same unseen dates."""
    shares = int(initial // rows[0].close)
    cash = initial - shares * rows[0].close
    values = [cash + shares * row.close for row in rows]
    summary = metrics(values, initial)
    summary.update({"final_value": values[-1], "trades": 1, "fees": 0.0})
    records = [{"date": row.date, "portfolio_value": value, "close": row.close} for row, value in zip(rows, values)]
    return {"policy": "Buy and hold", "summary": summary, "records": records}


def main() -> None:
    """I generate data when absent and export reproducible train/test results."""
    if not DATA.exists():
        generate_sample_csv(DATA)
    rows = load_market_data(DATA)
    split = int(len(rows) * 0.70)
    training_rows, testing_rows = rows[:split], rows[split:]
    agent = train_q_learning(training_rows)
    q_result = run_policy(testing_rows, agent)
    indicator_result = run_policy(testing_rows, IndicatorPolicy())
    benchmark_result = buy_and_hold(testing_rows)
    bundle = {
        "metadata": {
            "asset": "EDU-SIM",
            "scope": "Educational simulation; not financial advice",
            "seed": 42,
            "fee_rate": 0.001,
            "initial_cash": 10_000,
            "training_observations": len(training_rows),
            "test_observations": len(testing_rows),
            "test_start": testing_rows[0].date,
            "test_end": testing_rows[-1].date,
        },
        "strategies": [q_result, indicator_result, benchmark_result],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "evaluation.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    (ROOT / "public" / "evaluation.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    with (RESULTS / "evaluation_ledger.csv").open("w", newline="", encoding="utf-8") as handle:
        records = q_result["records"]
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    model = {f"{state[0]},{state[1]}": values for state, values in sorted(agent.q.items())}
    (RESULTS / "q_table.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(json.dumps({"metadata": bundle["metadata"], "summaries": {item["policy"]: item["summary"] for item in bundle["strategies"]}}, indent=2))


if __name__ == "__main__":
    main()
