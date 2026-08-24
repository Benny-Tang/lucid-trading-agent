"""
Lucid — Analyst / Valuation Gate / Risk Manager pipeline (demo mode)

Runs against mock market data shaped like Alpaca's paper API responses.
The `execute_order()` function is stubbed — it prints what WOULD be sent to
Alpaca's paper trading API. Real calls need to run where alpaca.markets is
reachable (this sandbox can't reach it); wire in `alpaca-py` there and
swap the stub for a real client call, keeping the same guardrail checks
upstream unchanged.

Guardrail numbers are loaded from guardrails.yaml — proposed defaults,
confirm/adjust before this touches a real paper account.
"""

import json
import yaml
from datetime import datetime, timezone

with open("guardrails.yaml") as f:
    GUARDRAILS = yaml.safe_load(f)

# ---- Mock market data, shaped like what an Alpaca paper-API snapshot gives you ----
MOCK_SNAPSHOTS = [
    {"ticker": "AAPL", "price": 231.10, "ma20": 229.50, "ma50": 224.80,
     "volume_trend": "rising", "sector_median_pe": 24.0, "trailing_pe": 31.2, "eps": 7.41},
    {"ticker": "KO", "price": 61.20, "ma20": 60.80, "ma50": 61.90,
     "volume_trend": "flat", "sector_median_pe": 22.0, "trailing_pe": 19.5, "eps": 3.14},
    {"ticker": "NVDA", "price": 118.40, "ma20": 112.00, "ma50": 104.30,
     "volume_trend": "rising", "sector_median_pe": 30.0, "trailing_pe": 55.0, "eps": 2.15},
]

WATCHLIST = [s["ticker"] for s in MOCK_SNAPSHOTS]  # stand-in for guardrails.watchlist.universe


def analyst(snapshot):
    """Simple, named-rule signal: 20/50 MA crossover only, for the hackathon MVP."""
    ticker = snapshot["ticker"]
    if snapshot["ma20"] > snapshot["ma50"] and snapshot["volume_trend"] == "rising":
        pct = round((snapshot["ma20"] / snapshot["ma50"] - 1) * 100, 2)
        return {
            "ticker": ticker,
            "direction": "long",
            "signal_name": "20/50 MA crossover",
            "signal_value": f"bullish crossover, +{pct}%",
            "rationale": "Short MA above long MA on rising volume.",
        }
    return {"ticker": ticker, "direction": "skip", "rationale": "No qualifying signal triggered."}


def valuation_gate(idea, snapshot):
    if idea["direction"] == "skip":
        return {"result": "n/a"}, idea

    fair_value = round(snapshot["eps"] * snapshot["sector_median_pe"], 2)
    price = snapshot["price"]
    margin_actual = round((fair_value - price) / price, 4)
    required = GUARDRAILS["valuation_gate"]["margin_of_safety_required_pct"] / 100

    passed = margin_actual >= required
    gate_result = {
        "result": "pass" if passed else "blocked",
        "fair_value_estimate": fair_value,
        "current_price": price,
        "margin_of_safety_required": required,
        "margin_of_safety_actual": margin_actual,
        "rationale": (
            f"Price is {abs(round(margin_actual*100,1))}% "
            f"{'below' if margin_actual >= 0 else 'above'} fair-value estimate; "
            f"required margin of safety is {required*100:.0f}%."
        ),
    }
    return gate_result, idea


def risk_manager(idea, gate_result, equity=100000, day_loss_pct_so_far=0.0, open_positions=0):
    if gate_result["result"] != "pass":
        return None

    caps = GUARDRAILS
    if day_loss_pct_so_far >= caps["loss_caps"]["daily_loss_cap_pct"]:
        return {"approved_size": 0, "autonomous": False,
                "reason": "Daily loss cap already breached — new trades halted for the day."}

    if open_positions >= caps["position_sizing"]["max_concurrent_positions"]:
        return {"approved_size": 0, "autonomous": False,
                "reason": "Max concurrent positions reached."}

    size_pct = caps["position_sizing"]["max_per_trade_pct"]
    size_usd = round(equity * size_pct / 100, 2)
    autonomous = size_pct <= caps["human_approval_thresholds"]["single_trade_pct_over"]

    return {
        "approved_size": size_usd,
        "approved_size_pct": size_pct,
        "autonomous": autonomous,
        "reason": "Within per-trade and portfolio guardrails." if autonomous
                   else "Exceeds single-trade human-approval threshold — routed for approval.",
    }


def execute_order(ticker, risk_result):
    """STUB — replace with a real Alpaca paper-trading order call in GitHub Actions."""
    if not risk_result or risk_result.get("approved_size", 0) == 0:
        return "not_submitted"
    if not risk_result["autonomous"]:
        return "pending_approval"
    print(f"[STUB] Would submit paper order: BUY {ticker} ~${risk_result['approved_size']}")
    return "filled_demo"


def run_once():
    trail = []
    for snapshot in MOCK_SNAPSHOTS:
        idea = analyst(snapshot)
        gate_result, idea = valuation_gate(idea, snapshot)
        risk_result = risk_manager(idea, gate_result) if idea["direction"] != "skip" else None
        outcome = execute_order(snapshot["ticker"], risk_result) if risk_result else "skipped"

        entry = {
            "id": f"trade_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{snapshot['ticker']}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": snapshot["ticker"],
            "outcome": outcome,
            "analyst": idea,
            "valuation_gate": gate_result,
            "risk_manager": risk_result,
        }
        trail.append(entry)
    return trail


if __name__ == "__main__":
    reasoning_trail = run_once()
    print(json.dumps(reasoning_trail, indent=2))

# generated 2026-08-24
