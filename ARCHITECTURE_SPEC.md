# Lucid — Agent Architecture Spec
Alpaca AI Trading Agents Hackathon (lablab.ai x Alpaca) — solo entry

## 1. Objective

A reasoning-transparent paper-trading agent. Every trade decision — including
refusals — must be traceable to a concrete signal, rule, or gate, never a
black-box score. The pipeline is three sequential agents plus an execution
layer, matching the reasoning-trail UI already built in the dashboard demo.

```
Watchlist → Analyst → Valuation Gate → Risk Manager → Execution → Alpaca (paper)
                 |            |               |
             reasoning    reasoning       reasoning
                 └──────────────┴───────────────┘
                                │
                        Reasoning Trail (logged, always — approved or blocked)
```

## 2. Agent Roles

### 2.1 Analyst
- **Input:** one ticker from the watchlist, latest price/volume/fundamentals snapshot.
- **Job:** generate a candidate idea (long/short/skip) from a small, named rule
  set — e.g. moving-average trend confirmation, RSI extremes, earnings-surprise
  drift. No proprietary "AI score" — each signal must map to a stated rule.
- **Output:** `{ticker, direction, signal_name, signal_value, rationale}` or
  `skip` with a reason (e.g. "no signal triggered").

### 2.2 Valuation Gate
- **Input:** Analyst's candidate idea.
- **Job:** value-investing-inspired sanity filter. Rejects ideas that are
  fundamentally expensive relative to a simple intrinsic estimate, regardless
  of how strong the technical signal is. This is the gate that makes "hype
  momentum with no valuation backing" get blocked and shown in the log as a
  blocked trade — the differentiator from signal-seller bots.
- **Method (proposed, simple and explainable):**
  - Estimate fair value via trailing P/E vs. sector median, or a basic
    Graham-style formula — whichever is cheaper to source reliably from
    Alpaca/free fundamentals data.
  - Require a **margin of safety** between current price and fair-value
    estimate (see guardrails below).
- **Output:** `pass` or `blocked`, with the numbers used and the threshold
  compared against — never just "fails valuation check."

### 2.3 Risk Manager
- **Input:** Valuation-gate-approved idea.
- **Job:** decide position size, and whether this trade can execute
  autonomously or needs human approval.
- **Checks, in order:**
  1. Daily loss cap not already breached → else hard block, log, halt for the day.
  2. Watchlist membership confirmed (no drift outside the pre-set universe).
  3. Position size computed from guardrail rules (below).
  4. Size/aggregate checked against human-approval thresholds → route to
     "pending approval" queue if exceeded, otherwise auto-execute.
- **Output:** `{approved_size, autonomous: true/false, reason}`.

### 2.4 Execution
- Places the paper order via Alpaca's trading API/MCP if `autonomous: true`.
- If `autonomous: false`, writes to a pending-approval queue surfaced on the
  dashboard; nothing is sent to Alpaca until Benny approves it there.
- Every outcome (filled, blocked, pending) gets one reasoning-trail entry —
  wins, losses, and refusals all logged the same way, nothing curated out.

## 3. Reasoning Trail Schema (matches dashboard's expandable log entries)

```json
{
  "id": "trade_2026-08-24_001",
  "timestamp": "2026-08-24T09:15:00Z",
  "ticker": "AAPL",
  "outcome": "blocked",
  "analyst": {
    "signal_name": "20/50 MA crossover",
    "signal_value": "bullish crossover, +1.8%",
    "rationale": "Short MA crossed above long MA on rising volume."
  },
  "valuation_gate": {
    "result": "blocked",
    "fair_value_estimate": 178.40,
    "current_price": 231.10,
    "margin_of_safety_required": 0.20,
    "margin_of_safety_actual": -0.30,
    "rationale": "Price is 30% above fair-value estimate; required 20% margin of safety not met."
  },
  "risk_manager": null,
  "final_reason": "Blocked at valuation gate before risk sizing was evaluated."
}
```

For an approved trade, `valuation_gate.result` is `"pass"` and `risk_manager`
is populated with size, autonomy flag, and reason — same schema, no fields hidden.

## 4. Deployment Mapping

- **GitHub Actions (public repo):** scheduled cron job runs the agent loop
  (Analyst → Gate → Risk Manager → Execution) against Alpaca's paper API.
  Actions has network access to alpaca.markets; this sandbox does not, so all
  live-API testing happens there, not here.
- **Hugging Face Spaces (CPU-basic, free tier):** hosts the public dashboard,
  reading the reasoning-trail log (e.g. from a repo-committed JSON/SQLite file
  or a lightweight API) — no paid hosting, no Codespaces.
- **No GitHub push happens without your explicit approval, per standing rule.**

## 5. Open Items / Assumptions Needing Your Confirmation

1. Fundamentals data source for the Valuation Gate (Alpaca's own fundamentals
   coverage is limited — likely need a free supplementary source; needs a pick).
2. Exact watchlist universe (proposed default in guardrails doc — confirm or replace).
3. Whether Analyst's rule set should start with just 1-2 signals for the hackathon
   deadline (recommended, given the 28 Aug–4 Sep window) or more.

---
Spec v1 — generated 2026-08-24
