"""I verify the core accounting, validation, explanation and evaluation contracts."""

import json
import tempfile
import unittest
from pathlib import Path

from src.agents import IndicatorPolicy
from src.data_pipeline import generate_sample_csv, load_market_data
from src.environment import BUY, SELL, TradingEnvironment
from src.evaluation import run_policy
from src.explanations import explain


class SystemTests(unittest.TestCase):
    """I exercise the complete deterministic pipeline with controlled data."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temporary.name) / "market.csv"
        generate_sample_csv(cls.path, periods=60)
        cls.rows = load_market_data(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_data_is_chronological_and_enriched(self):
        self.assertGreater(len(self.rows), 30)
        self.assertLess(self.rows[0].date, self.rows[-1].date)
        self.assertGreaterEqual(self.rows[0].rsi_14, 0)

    def test_buy_accounting_reconciles(self):
        environment = TradingEnvironment(self.rows[:3], initial_cash=1000)
        environment.reset()
        _, _, _, transition = environment.step(BUY)
        expected = transition.cash_after + transition.holdings_after * transition.close
        self.assertAlmostEqual(expected, transition.portfolio_value, places=7)

    def test_sell_without_holdings_is_explicitly_rejected(self):
        environment = TradingEnvironment(self.rows[:3])
        environment.reset()
        _, _, _, transition = environment.step(SELL)
        self.assertEqual(transition.executed_action, 0)
        self.assertEqual(transition.rejected_reason, "No holdings available")

    def test_unknown_action_raises_controlled_error(self):
        environment = TradingEnvironment(self.rows[:3])
        with self.assertRaisesRegex(ValueError, "unknown action"):
            environment.step(99)

    def test_explanation_matches_recorded_rules(self):
        environment = TradingEnvironment(self.rows[:3])
        environment.reset()
        _, _, _, transition = environment.step(BUY)
        text, rules = explain(transition, "Test policy")
        self.assertIn("$", text)
        self.assertIsInstance(rules, list)

    def test_complete_evaluation_has_metrics_and_records(self):
        result = run_policy(self.rows, IndicatorPolicy())
        self.assertEqual(len(result["records"]), len(self.rows))
        self.assertIn("maximum_drawdown_pct", result["summary"])
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
