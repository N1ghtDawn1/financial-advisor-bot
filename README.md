# Financial Advisor Bot

I built this repository for University of London CM3070, using **4 Project Idea 2: Financial Advisor Bot**. It is an educational simulation that connects a reproducible reinforcement-learning policy to an auditable market environment, faithful natural-language explanations and a browser dashboard.

> This project does not execute real trades and does not provide financial advice. The bundled dataset is deterministic, generated historical-style OHLCV data for reproducible assessment.

## What I implemented

- chronological OHLCV generation, validation, SMA and RSI features;
- a long-only trading environment with cash, holdings, fixed sizing, transaction fees, reward and a reconciled ledger;
- a tabular Q-learning policy trained with a fixed seed;
- indicator and buy-and-hold baselines on the same unseen test interval;
- total return, annualised volatility, Sharpe ratio, maximum drawdown, trades and fees;
- explanations generated from the exact immutable transition record;
- controlled handling of unknown actions, insufficient cash and missing holdings;
- a responsive dashboard with a decision slider, evidence trace, portfolio state, equity chart and comparison table;
- automated Python and rendered-interface tests.

## Verified result

The fixed run uses 116 training observations and 50 unseen test observations from 3 July to 10 September 2025.

| Strategy | Final value | Return | Sharpe | Maximum drawdown | Trades |
|---|---:|---:|---:|---:|---:|
| Q-learning agent | $10,084.05 | 0.84% | 0.33 | -7.28% | 15 |
| Indicator baseline | $10,025.63 | 0.26% | 0.16 | -6.60% | 25 |
| Buy and hold | $9,623.50 | -3.76% | -0.76 | -13.33% | 1 |

I treat these as results for the bundled educational dataset, not evidence of future profitability.

## Run the complete project

### 1. Generate the evidence

```powershell
python run_pipeline.py
python -m unittest discover -s tests -p "test_python_system.py" -v
```

The pipeline writes `results/evaluation.json`, `results/evaluation_ledger.csv`, `results/q_table.json` and `public/evaluation.json`.

### 2. Open the dashboard

Install Node.js 22 or later, then run:

```powershell
pnpm install
pnpm dev
```

Open the local address printed in the terminal. The browser reads `public/evaluation.json`, so every decision, value and chart uses the Python evaluation evidence.

## Repository map

```text
financial-advisor-bot/
├── app/                    Browser dashboard
├── data/                   Deterministic OHLCV dataset
├── public/                 Dashboard data and share image
├── results/                Ledger, summary and learned Q-table
├── src/
│   ├── agents.py           Indicator and Q-learning policies
│   ├── data_pipeline.py    Validation, SMA and RSI
│   ├── environment.py      Transactions, fees, reward and ledger
│   ├── evaluation.py       Metrics and policy evaluation
│   └── explanations.py     Evidence-faithful explanations
├── tests/                  Python and interface tests
├── config.json             Reproducible assumptions
└── run_pipeline.py         End-to-end training and evaluation
```

## Suggested four-minute demonstration

1. Open the dashboard and state the template number and simulation boundary.
2. Show the training/test counts and best-result card.
3. Move the decision slider and switch between policies.
4. Reveal an evidence trace and connect it to the explanation.
5. Show cash, holdings, quantity, fee and reconciled portfolio value.
6. Compare all three equity curves and risk metrics.
7. Run the six Python tests and show that they pass.
8. End with the limitations: generated data, one asset, one fixed run and no live trading.

## Academic integrity and limitations

I disclose the dataset generator, seed, fee assumption, split and evaluation code. The policy uses a compact discretised state and the evaluation covers one generated market series. A stronger extension would add licensed real historical data, repeated seeds, multiple assets, walk-forward validation and a pre-registered user-comprehension study.
