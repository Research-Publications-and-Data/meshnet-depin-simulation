#!/usr/bin/env python3
"""
Wash trading Monte Carlo simulation (100 runs).
Models fraud with and without proof-of-coverage detection.

Model:
- 1,000 node network, 15% mercenary operators with fraud_prob > 0
- WITHOUT detection: mercenaries submit false coverage claims, earn full emissions
- WITH detection (proof-of-coverage): 97% catch rate per challenge,
  50% stake slashing on catch

Output: results/wash_trading_results.csv
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import RESULTS_DIR

N_RUNS = 100
N_NODES = 1000
DAYS = 365  # 1 year
DAILY_EMISSION = 109_589
CATCH_RATE = 0.97
SLASH_FRACTION = 0.50
MERCENARY_FRACTION = 0.15
INITIAL_STAKE = 20_000


def run_wash_trading_sim(seed, with_poc=True):
    """Run one wash trading simulation for 365 days."""
    rng = np.random.default_rng(seed)

    # Initialize operators
    n_mercs = int(N_NODES * MERCENARY_FRACTION)
    n_honest = N_NODES - n_mercs
    stakes = np.full(N_NODES, INITIAL_STAKE, dtype=float)
    is_merc = np.zeros(N_NODES, dtype=bool)
    is_merc[:n_mercs] = True
    rng.shuffle(is_merc)
    active = np.ones(N_NODES, dtype=bool)

    # Mercenary fraud probabilities (varies by operator)
    fraud_probs = np.where(is_merc, rng.uniform(0.1, 0.3, N_NODES), 0.0)

    total_emission = 0
    total_fraud_emission = 0
    total_slashed = 0
    honest_earnings = 0

    for day in range(DAYS):
        n_active = active.sum()
        if n_active == 0:
            break

        per_op_emission = DAILY_EMISSION / n_active

        # Each active operator claims emission
        for i in range(N_NODES):
            if not active[i]:
                continue

            if is_merc[i] and rng.random() < fraud_probs[i]:
                # Fraudulent claim
                if with_poc and rng.random() < CATCH_RATE:
                    # Caught: slash stake
                    slash_amount = stakes[i] * SLASH_FRACTION
                    stakes[i] -= slash_amount
                    total_slashed += slash_amount
                    if stakes[i] <= 0:
                        active[i] = False
                else:
                    # Not caught or no PoC: fraudster earns emission
                    total_fraud_emission += per_op_emission
                    total_emission += per_op_emission
            else:
                # Honest claim
                total_emission += per_op_emission
                if not is_merc[i]:
                    honest_earnings += per_op_emission

    total_emission = max(total_emission, 1)
    fraud_rate = total_fraud_emission / total_emission
    surviving_mercs = sum(1 for i in range(N_NODES) if is_merc[i] and active[i])
    surviving_honest = sum(1 for i in range(N_NODES) if not is_merc[i] and active[i])

    # Honest operator yield impact: how much more/less did honest ops earn
    # vs expected equal share
    expected_honest = DAILY_EMISSION * DAYS * (n_honest / N_NODES)
    yield_impact = (honest_earnings - expected_honest) / max(expected_honest, 1)

    return {
        "fraud_rate_pct": round(fraud_rate * 100, 4),
        "total_slashed": round(total_slashed, 0),
        "honest_yield_impact_pct": round(yield_impact * 100, 2),
        "surviving_mercs": surviving_mercs,
        "surviving_honest": surviving_honest,
        "total_active_final": sum(active),
    }


def main():
    print("=" * 60)
    print("WASH TRADING MONTE CARLO")
    print(f"N={N_RUNS} runs, {N_NODES} nodes, {DAYS} days")
    print("=" * 60)

    results = []

    # WITH proof-of-coverage
    print("\n  Running WITH proof-of-coverage...")
    for i in range(N_RUNS):
        seed = 5000 + i
        r = run_wash_trading_sim(seed, with_poc=True)
        r["poc"] = True
        r["seed"] = seed
        results.append(r)
        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{N_RUNS} done", file=sys.stderr)

    # WITHOUT proof-of-coverage
    print("  Running WITHOUT proof-of-coverage...")
    for i in range(N_RUNS):
        seed = 5000 + i
        r = run_wash_trading_sim(seed, with_poc=False)
        r["poc"] = False
        r["seed"] = seed
        results.append(r)
        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{N_RUNS} done", file=sys.stderr)

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "wash_trading_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")

    # Summary
    print("\n── Results ──")
    for poc_val, label in [(True, "WITH PoC"), (False, "WITHOUT PoC")]:
        sub = df[df["poc"] == poc_val]
        fraud = sub["fraud_rate_pct"]
        print(f"\n  {label}:")
        print(f"    Fraud rate: median={fraud.median():.2f}%, "
              f"mean={fraud.mean():.2f}%, IQR=[{fraud.quantile(0.25):.2f}%, {fraud.quantile(0.75):.2f}%]")
        print(f"    Min/Max: [{fraud.min():.2f}%, {fraud.max():.2f}%]")
        print(f"    Slashed: {sub['total_slashed'].mean():,.0f} tokens (mean)")
        print(f"    Honest yield impact: {sub['honest_yield_impact_pct'].mean():+.2f}%")
        print(f"    Surviving mercs: {sub['surviving_mercs'].mean():.0f}/{int(N_NODES * MERCENARY_FRACTION)}")


if __name__ == "__main__":
    main()
