#!/usr/bin/env python3
"""
Governance voting power exponent sweep (NEW — reviewer-requested).
Analytical calculation using operator population from final timestep of bull/PID.

V(i) = τ(i) × (1 + R(i))^p

Exponents: p = [0.5 (sqrt), 1.0 (linear), 1.5, 2.0 (current), 3.0 (cubic)]
Also: V(i) = τ(i) × (1 + log(1 + R(i))) (logarithmic)

Key question: Is quadratic (p=2) optimal for capture resistance?
Output: results/exponent_sensitivity_results.csv
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import (run_simulation, SCENARIOS, SEED, N_TARGET,
                           TOTAL_SUPPLY, RESULTS_DIR)

EXPONENTS = [0.5, 1.0, 1.5, 2.0, 3.0]


def compute_governance_metrics(agents, exponent=None, use_log=False):
    """Compute Gini, HHI, top-1%, top-10%, whale test for a given voting power formula."""
    active = [a for a in agents if a["active"]]
    if not active:
        return {}

    # Compute voting power
    powers = []
    for a in active:
        tau = a["stake"]
        R = a["reputation"]
        if use_log:
            v = tau * (1 + np.log(1 + R))
        else:
            v = tau * (1 + R) ** exponent
        powers.append(v)

    powers = np.array(powers, dtype=float)
    total_power = powers.sum()
    if total_power == 0:
        return {}

    shares = powers / total_power
    n = len(shares)

    # Gini coefficient
    sorted_shares = np.sort(shares)
    cumulative = np.cumsum(sorted_shares)
    gini = 1 - 2 * np.sum(cumulative) / n + 1 / n

    # HHI
    hhi = float(np.sum(shares ** 2))

    # Top-1% and top-10% share
    sorted_desc = np.sort(shares)[::-1]
    top1_count = max(1, int(np.ceil(n * 0.01)))
    top10_count = max(1, int(np.ceil(n * 0.10)))
    top1_share = float(sorted_desc[:top1_count].sum())
    top10_share = float(sorted_desc[:top10_count].sum())

    # Whale test: entity with 20% of total supply and R=0
    whale_tokens = int(TOTAL_SUPPLY * 0.20)
    if use_log:
        whale_power = whale_tokens * (1 + np.log(1 + 0))
    else:
        whale_power = whale_tokens * (1 + 0) ** exponent
    whale_share = whale_power / (total_power + whale_power)

    return {
        "gini": round(gini, 4),
        "hhi": round(hhi, 6),
        "top1_pct_share": round(top1_share * 100, 2),
        "top10_pct_share": round(top10_share * 100, 2),
        "whale_20pct_power_share": round(whale_share * 100, 2),
        "n_active": n,
    }


def main():
    print("=" * 60)
    print("GOVERNANCE EXPONENT SWEEP (ANALYTICAL)")
    print("=" * 60)

    # Run bull/PID to get final operator population
    print("\nRunning bull/PID simulation to extract operator population...")
    scenario = SCENARIOS["bull"]
    seed = SEED  # bull is first scenario

    # We need access to the agents, so we'll re-run the sim and capture agents
    from meshnet_model import (create_operators, create_whales, compute_demand,
                                pid_emission, static_emission, burn_tokens,
                                update_operators, update_reputation, update_price,
                                TIMESTEPS, BASE_EMISSION, PID_CADENCE,
                                KP_NORM, KI_NORM, KD_NORM)

    rng = np.random.default_rng(seed)
    C, T, N, F_daily, P = 200_000_000, 150_000_000, 2_000, 500.0, 0.10
    E, B = BASE_EMISSION, 0.0
    integral, prev_error = 0.0, 0.0
    slashed_total, fraud_total, cost_mult = 0, 0.0, 1.0
    agents = create_operators(N, rng)
    whales = create_whales(rng)

    for t in range(TIMESTEPS):
        F_daily = compute_demand(t, N, P, scenario, rng, cost_mult)
        result = pid_emission(N, integral, prev_error, t)
        if result[0] is not None:
            E, integral, prev_error = result
        B = burn_tokens(F_daily, P)
        agents, slashed, fraud, treas_subsidy = update_operators(
            agents, E, F_daily, N, P, scenario, t, rng, T, cost_mult)
        slashed_total += slashed
        agents = update_reputation(agents, t)
        P = update_price(P, F_daily, C, scenario.get("price_drift", 0), rng)
        C = max(0, min(TOTAL_SUPPLY, C + E - B - slashed))
        T = max(0, T + slashed - treas_subsidy)
        N = max(1, sum(1 for a in agents if a["active"]))

    active_count = sum(1 for a in agents if a["active"])
    print(f"  Final bull/PID: N={active_count}, P=${P:.4f}")

    # Compute governance metrics for each exponent
    results = []
    for p in EXPONENTS:
        metrics = compute_governance_metrics(agents, exponent=p)
        metrics["exponent"] = p
        metrics["formula"] = f"τ × (1+R)^{p}"
        results.append(metrics)
        print(f"\n  p={p}: Gini={metrics['gini']:.4f}, HHI={metrics['hhi']:.6f}, "
              f"Top-1%={metrics['top1_pct_share']:.1f}%, "
              f"Whale(20%,R=0)={metrics['whale_20pct_power_share']:.1f}%")

    # Logarithmic formula
    log_metrics = compute_governance_metrics(agents, use_log=True)
    log_metrics["exponent"] = "log"
    log_metrics["formula"] = "τ × (1 + log(1+R))"
    results.append(log_metrics)
    print(f"\n  log: Gini={log_metrics['gini']:.4f}, HHI={log_metrics['hhi']:.6f}, "
          f"Top-1%={log_metrics['top1_pct_share']:.1f}%, "
          f"Whale(20%,R=0)={log_metrics['whale_20pct_power_share']:.1f}%")

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "exponent_sensitivity_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")

    # Recommendation
    print("\n── Recommendation ──")
    # Find exponent minimizing whale power while keeping Gini reasonable
    numeric = df[df["exponent"] != "log"].copy()
    numeric["exponent"] = numeric["exponent"].astype(float)
    best_idx = numeric["whale_20pct_power_share"].idxmin()
    best = numeric.loc[best_idx]
    print(f"  Best whale resistance: p={best['exponent']} "
          f"(whale share={best['whale_20pct_power_share']:.1f}%)")
    current = numeric[numeric["exponent"] == 2.0].iloc[0]
    print(f"  Current (p=2.0): whale share={current['whale_20pct_power_share']:.1f}%, "
          f"Gini={current['gini']:.4f}")


if __name__ == "__main__":
    main()
