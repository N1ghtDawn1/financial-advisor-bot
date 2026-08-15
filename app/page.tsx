"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Summary = {
  total_return_pct: number;
  annualised_volatility_pct: number;
  sharpe_ratio: number;
  maximum_drawdown_pct: number;
  final_value: number;
  trades: number;
  fees: number;
};

type RecordRow = {
  date: string;
  close: number;
  sma_10?: number;
  delta_sma?: number;
  rsi_14?: number;
  action_name?: string;
  quantity?: number;
  fee?: number;
  cash_after?: number;
  holdings_after?: number;
  portfolio_value: number;
  explanation?: string;
  matched_rules?: string[];
  rejected_reason?: string;
};

type Strategy = { policy: string; summary: Summary; records: RecordRow[] };
type Bundle = {
  metadata: {
    asset: string;
    scope: string;
    seed: number;
    fee_rate: number;
    initial_cash: number;
    training_observations: number;
    test_observations: number;
    test_start: string;
    test_end: string;
  };
  strategies: Strategy[];
};

const formatMoney = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

function EquityChart({ strategies }: { strategies: Strategy[] }) {
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const element = canvas.current;
    if (!element || strategies.length === 0) return;
    const scale = window.devicePixelRatio || 1;
    const width = element.clientWidth;
    const height = element.clientHeight;
    element.width = width * scale;
    element.height = height * scale;
    const context = element.getContext("2d");
    if (!context) return;
    context.scale(scale, scale);
    context.clearRect(0, 0, width, height);
    const all = strategies.flatMap((strategy) => strategy.records.map((row) => row.portfolio_value));
    const low = Math.min(...all) * 0.995;
    const high = Math.max(...all) * 1.005;
    const padding = { top: 18, right: 18, bottom: 26, left: 54 };
    context.strokeStyle = "#dbe6e2";
    context.lineWidth = 1;
    context.font = "11px Arial";
    context.fillStyle = "#678078";
    for (let line = 0; line <= 4; line += 1) {
      const y = padding.top + ((height - padding.top - padding.bottom) * line) / 4;
      context.beginPath();
      context.moveTo(padding.left, y);
      context.lineTo(width - padding.right, y);
      context.stroke();
      const value = high - ((high - low) * line) / 4;
      context.fillText(`$${Math.round(value).toLocaleString()}`, 3, y + 4);
    }
    const colors = ["#0f766e", "#d97706", "#64748b"];
    strategies.forEach((strategy, strategyIndex) => {
      context.strokeStyle = colors[strategyIndex];
      context.lineWidth = strategyIndex === 0 ? 3 : 2;
      context.beginPath();
      strategy.records.forEach((row, index) => {
        const x = padding.left + ((width - padding.left - padding.right) * index) / Math.max(1, strategy.records.length - 1);
        const y = padding.top + ((high - row.portfolio_value) / (high - low)) * (height - padding.top - padding.bottom);
        if (index === 0) context.moveTo(x, y);
        else context.lineTo(x, y);
      });
      context.stroke();
    });
  }, [strategies]);

  return <canvas ref={canvas} className="equity-chart" role="img" aria-label="Equity curves for the Q-learning agent, indicator baseline and buy-and-hold benchmark" />;
}

export default function Home() {
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [strategyIndex, setStrategyIndex] = useState(0);
  const [dateIndex, setDateIndex] = useState(0);
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    fetch("/evaluation.json").then((response) => response.json()).then((data: Bundle) => {
      setBundle(data);
      setDateIndex(data.strategies[0].records.length - 1);
    });
  }, []);

  const strategy = bundle?.strategies[strategyIndex];
  const decision = strategy?.records[Math.min(dateIndex, (strategy?.records.length ?? 1) - 1)];
  const maxRecords = strategy?.records.length ?? 1;
  const leaderboard = useMemo(() => bundle?.strategies.slice().sort((a, b) => b.summary.total_return_pct - a.summary.total_return_pct) ?? [], [bundle]);

  if (!bundle || !strategy || !decision) {
    return <main className="loading"><div className="loading-mark" /><p>Loading the verified evaluation run…</p></main>;
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#overview" aria-label="Financial Advisor Bot home">
          <span className="brand-mark">FA</span>
          <span><strong>Financial Advisor Bot</strong><small>Transparent simulation lab</small></span>
        </a>
        <nav aria-label="Page sections">
          <a href="#overview">Overview</a><a href="#decision">Decision</a><a href="#evaluation">Evaluation</a><a href="#method">Method</a>
        </nav>
        <span className="simulation-badge">Simulation only</span>
      </header>

      <section className="hero" id="overview">
        <div className="hero-copy">
          <p className="eyebrow">CM3070 · 4 Project Idea 2</p>
          <h1>See the evidence behind<br /><em>every simulated action.</em></h1>
          <p className="lede">I trained a reproducible reinforcement-learning baseline, evaluated it on unseen chronological data, and connected every action to the exact market and portfolio state used in the simulation.</p>
          <div className="hero-actions"><a className="primary" href="#decision">Inspect a decision</a><a className="secondary" href="#evaluation">View evaluation</a></div>
          <div className="run-meta"><span><b>{bundle.metadata.training_observations}</b> training rows</span><span><b>{bundle.metadata.test_observations}</b> unseen test rows</span><span><b>{bundle.metadata.seed}</b> fixed seed</span></div>
        </div>
        <div className="hero-panel">
          <div className="panel-label"><span>Best test result</span><span className="live-dot">Verified run</span></div>
          <strong className="hero-value">{formatMoney(leaderboard[0].summary.final_value)}</strong>
          <span className="positive">+{leaderboard[0].summary.total_return_pct.toFixed(2)}%</span>
          <div className="mini-bars" aria-label="Strategy return comparison">
            {leaderboard.map((item) => <div key={item.policy}><span>{item.policy}</span><div><i style={{ width: `${Math.max(7, 55 + item.summary.total_return_pct * 9)}%` }} /></div><b>{item.summary.total_return_pct.toFixed(2)}%</b></div>)}
          </div>
          <p>Test window · {bundle.metadata.test_start} — {bundle.metadata.test_end}</p>
        </div>
      </section>

      <section className="workspace" id="decision">
        <div className="section-heading"><div><p className="eyebrow">Decision explorer</p><h2>One record. One explanation. No hidden recomputation.</h2></div><p>Move through the unseen test period and audit the selected action, indicators, execution and portfolio state.</p></div>
        <div className="strategy-tabs" role="tablist" aria-label="Select a strategy">
          {bundle.strategies.map((item, index) => <button role="tab" aria-selected={strategyIndex === index} className={strategyIndex === index ? "active" : ""} key={item.policy} onClick={() => { setStrategyIndex(index); setDateIndex(Math.min(dateIndex, item.records.length - 1)); }}>{item.policy}</button>)}
        </div>
        <div className="decision-grid">
          <article className="decision-card">
            <div className="card-top"><span>{decision.date}</span><span>{bundle.metadata.asset}</span></div>
            <div className="action-row"><div><small>Executed action</small><strong className={`action ${decision.action_name?.toLowerCase()}`}>{decision.action_name ?? "Benchmark"}</strong></div><div><small>Market close</small><strong>{formatMoney(decision.close)}</strong></div></div>
            <p className="explanation">{decision.explanation ?? "I hold the passive benchmark continuously for comparison on identical dates."}</p>
            <button className="trace-button" onClick={() => setShowTrace(!showTrace)} aria-expanded={showTrace}>{showTrace ? "Hide evidence trace" : "Reveal evidence trace"}</button>
            {showTrace && <div className="trace"><code>{JSON.stringify({ date: decision.date, action: decision.action_name ?? "Buy and hold", matched_rules: decision.matched_rules ?? ["PASSIVE_BENCHMARK"], delta_sma: decision.delta_sma, rsi_14: decision.rsi_14, quantity: decision.quantity, fee: decision.fee }, null, 2)}</code></div>}
          </article>
          <aside className="evidence-card">
            <h3>Recorded evidence</h3>
            <dl><div><dt>10-day SMA</dt><dd>{decision.sma_10 ? formatMoney(decision.sma_10) : "Passive"}</dd></div><div><dt>SMA deviation</dt><dd>{decision.delta_sma !== undefined ? `${(decision.delta_sma * 100).toFixed(2)}%` : "—"}</dd></div><div><dt>RSI (14)</dt><dd>{decision.rsi_14?.toFixed(1) ?? "—"}</dd></div><div><dt>Quantity</dt><dd>{decision.quantity ?? "Held"}</dd></div><div><dt>Transaction fee</dt><dd>{formatMoney(decision.fee ?? 0)}</dd></div></dl>
          </aside>
          <aside className="portfolio-card">
            <h3>Portfolio after action</h3>
            <strong>{formatMoney(decision.portfolio_value)}</strong>
            <dl><div><dt>Cash</dt><dd>{decision.cash_after !== undefined ? formatMoney(decision.cash_after) : "Benchmark"}</dd></div><div><dt>Shares</dt><dd>{decision.holdings_after ?? "Continuous"}</dd></div><div><dt>Status</dt><dd>{decision.rejected_reason || "Reconciled"}</dd></div></dl>
          </aside>
        </div>
        <div className="timeline"><label htmlFor="date-slider">Observation {dateIndex + 1} of {maxRecords}</label><input id="date-slider" type="range" min="0" max={maxRecords - 1} value={Math.min(dateIndex, maxRecords - 1)} onChange={(event) => setDateIndex(Number(event.target.value))} /><span>{strategy.records[0].date}</span><span>{strategy.records[maxRecords - 1].date}</span></div>
      </section>

      <section className="evaluation" id="evaluation">
        <div className="section-heading light"><div><p className="eyebrow">Unseen-period evaluation</p><h2>Return is only one part of the result.</h2></div><p>I report the same dates, starting capital and cost assumptions for every strategy.</p></div>
        <div className="metric-strip">
          <div><small>Total return</small><strong>{strategy.summary.total_return_pct.toFixed(2)}%</strong></div><div><small>Sharpe ratio</small><strong>{strategy.summary.sharpe_ratio.toFixed(2)}</strong></div><div><small>Max drawdown</small><strong>{strategy.summary.maximum_drawdown_pct.toFixed(2)}%</strong></div><div><small>Annual volatility</small><strong>{strategy.summary.annualised_volatility_pct.toFixed(2)}%</strong></div><div><small>Trades / fees</small><strong>{strategy.summary.trades} / {formatMoney(strategy.summary.fees)}</strong></div>
        </div>
        <div className="chart-card"><div className="chart-head"><div><h3>Portfolio value on the test interval</h3><p>All strategies start from $10,000.</p></div><div className="legend"><span className="teal">Q-learning</span><span className="amber">Indicator</span><span className="slate">Buy & hold</span></div></div><EquityChart strategies={bundle.strategies} /></div>
        <div className="results-table" role="table" aria-label="Strategy results comparison"><div className="table-row table-head" role="row"><span>Strategy</span><span>Final value</span><span>Return</span><span>Sharpe</span><span>Max drawdown</span><span>Trades</span></div>{bundle.strategies.map((item) => <div className="table-row" role="row" key={item.policy}><strong>{item.policy}</strong><span>{formatMoney(item.summary.final_value)}</span><span className={item.summary.total_return_pct >= 0 ? "positive" : "negative"}>{item.summary.total_return_pct.toFixed(2)}%</span><span>{item.summary.sharpe_ratio.toFixed(2)}</span><span>{item.summary.maximum_drawdown_pct.toFixed(2)}%</span><span>{item.summary.trades}</span></div>)}</div>
      </section>

      <section className="method" id="method">
        <div className="section-heading"><div><p className="eyebrow">Reproducible method</p><h2>From source data to visible evidence.</h2></div><p>The interface consumes the stored evaluation log. It does not recalculate the result independently.</p></div>
        <div className="pipeline" aria-label="System architecture"><div><b>01</b><strong>Validated OHLCV</strong><span>Chronological sample data</span></div><i>→</i><div><b>02</b><strong>Trading environment</strong><span>Cash, holdings, fees, reward</span></div><i>→</i><div><b>03</b><strong>Policy</strong><span>Q-learning + baselines</span></div><i>→</i><div><b>04</b><strong>Evidence log</strong><span>Action, state, explanation</span></div><i>→</i><div><b>05</b><strong>Dashboard</strong><span>Auditable presentation</span></div></div>
        <div className="assurance-grid"><article><span>6 / 6</span><h3>Automated system tests</h3><p>Data chronology, accounting reconciliation, rejected actions, unknown tokens, explanation traces and complete evaluation output.</p></article><article><span>42</span><h3>Fixed random seed</h3><p>The training run, data generator and Q-table are reproducible from one documented command.</p></article><article><span>0.10%</span><h3>Transaction fee</h3><p>Each simulated trade deducts the configured proportional cost before portfolio evaluation.</p></article></div>
      </section>

      <footer><div><strong>Financial Advisor Bot</strong><p>University of London · CM3070 Final Project</p></div><p><b>Important:</b> This is an educational simulation using generated historical-style data. It is not financial advice and does not execute real trades.</p></footer>
    </main>
  );
}
