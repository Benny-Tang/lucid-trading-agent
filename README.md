[README (1).md](https://github.com/user-attachments/files/31360389/README.1.md)
# Lucid — Reasoning-Transparent Paper Trading Agent

Built for the **Alpaca AI Trading Agents Hackathon** (lablab.ai x Alpaca), 28 Aug – 4 Sep 2026.

## What this is

Lucid is a paper-trading agent whose entire selling point is **you can see why**.
Every decision — a trade entered, a size chosen, or a candidate refused — comes
with a plain-language explanation traceable to a named signal or rule, never a
black-box "AI score." Wins and losses are logged the same way, in full; nothing
curated out.

This is a deliberate contrast to the retail trading-bot market's usual
playbook — signal-sellers, prop-firm challenge funnels, curated-green trade
histories — built after researching that space directly.

## How it works

```
Watchlist → Analyst → Valuation Gate → Risk Manager → Execution → Alpaca (paper)
```

- **Analyst** — generates a candidate trade idea from a small, named rule set
  (e.g. a 20/50 moving-average crossover). No proprietary scoring.
- **Valuation Gate** — a value-investing-inspired sanity check. Blocks ideas
  that are fundamentally expensive relative to a simple fair-value estimate,
  regardless of how strong the technical signal looks. This is what produces
  the "blocked trade" entries in the log.
- **Risk Manager** — sizes the position and decides whether it can execute
  autonomously or needs human sign-off, based on pre-set guardrails (position
  size, daily loss cap, watchlist, approval thresholds).
- **Execution** — submits the paper order to Alpaca if autonomous, or queues
  it for manual approval if not.

Every run produces a reasoning-trail entry — see `ARCHITECTURE_SPEC.md` for
the full JSON schema.

## Repo contents

| File | What it is |
|---|---|
| `ARCHITECTURE_SPEC.md` | Full agent design — roles, reasoning-trail schema, deployment plan, open items |
| `guardrails.yaml` | Proposed risk/position guardrail numbers (position size, loss caps, valuation margin of safety, approval thresholds) |
| `lucid_pipeline_demo.py` | Working demo of the Analyst → Valuation Gate → Risk Manager pipeline on mock data shaped like Alpaca's paper API |

## Running the demo

```bash
pip install pyyaml
python3 lucid_pipeline_demo.py
```

Prints a reasoning trail (JSON) for a small mock watchlist — showing at least
one blocked trade and one skipped trade, by design.

Note: `execute_order()` in the demo is stubbed. Real Alpaca paper-API calls
are intended to run via a scheduled GitHub Actions job, not locally, keeping
the same guardrail logic upstream unchanged.

## Status

Architecture and guardrails drafted, demo pipeline working on mock data.
Not yet connected to live Alpaca paper-trading keys — waiting on the
hackathon's technology-provider announcement before finalizing the
multi-agent split and wiring in real data sources.

---
generated 2026-08-24
