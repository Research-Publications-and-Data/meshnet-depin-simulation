#!/usr/bin/env python3
"""
Multi-seed ensemble runner (NEW — reviewer-requested, CRITICAL).
N_SEEDS random seeds per configuration (8 configs = 240 runs at N=30).

Purpose: Establish confidence intervals on headline metrics.
Determine whether Ki non-monotonicity is structural or stochastic path dependence.

Output: results/multi_seed_results.csv, results/ki_nonmonotonicity_test.csv
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import (run_simulation, SCENARIOS, SEED, N_TARGET,
                           KP_NORM, KI_NORM, KD_NORM, RESULTS_DIR)
import meshnet_model as mm

N_SEEDS = 30
BASE_SEED = 1000


def run_ensemble():
    """Run ensemble of all configs with multiple seeds."""
    print("=" * 60)
    print("MULTI-SEED ENSEMBLE")
    print(f"N_SEEDS={N_SEEDS}, configs=8, total runs={N_SEEDS * 8}")
    print("=" * 60)

    all_records = []
    total_runs = len(SCENARIOS) * 2 * N_SEEDS
    run_count = 0

    for sname, scenario in SCENARIOS.items():
        for use_pid in [True, False]:
            model = "pid" if use_pid else "static"
            for seed_offset in range(N_SEEDS):
                seed = BASE_SEED + seed_offset
                run_count += 1
                if run_count % 20 == 0 or run_count == 1:
                    print(f"  [{run_count}/{total_runs}] {sname}/{model} seed={seed}",
                          file=sys.stderr)

                records = run_simulation(sname, scenario, use_pid, seed)
                final = records[-1]
                final_record = {
                    "scenario": sname,
                    "emission_model": model,
                    "seed": seed,
                    "final_N": final["N"],
                    "final_P": final["P"],
                    "final_C": final["C"],
                    "final_T": final["T"],
                    "bme_max": max(r["bme"] for r in records),
                    "total_emission": sum(r["E"] for r in records),
                    "total_burned": sum(r["B"] for r in records),
                    "slashed_total": final["slashed_total"],
                }
                all_records.append(final_record)

    df = pd.DataFrame(all_records)
    out = RESULTS_DIR / "multi_seed_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")

    # Summary statistics
    print("\n── Ensemble Summary ──")
    summary = df.groupby(["scenario", "emission_model"]).agg(
        N_mean=("final_N", "mean"),
        N_std=("final_N", "std"),
        N_p5=("final_N", lambda x: x.quantile(0.05)),
        N_p95=("final_N", lambda x: x.quantile(0.95)),
        P_mean=("final_P", "mean"),
        P_std=("final_P", "std"),
        bme_max_mean=("bme_max", "mean"),
        bme_max_std=("bme_max", "std"),
    ).round(4)
    print(summary.to_string())

    # Coefficient of variation
    print("\n── Coefficient of Variation (std/mean) ──")
    cv = df.groupby(["scenario", "emission_model"]).apply(
        lambda g: pd.Series({
            "N_cv": g["final_N"].std() / max(g["final_N"].mean(), 1),
            "P_cv": g["final_P"].std() / max(g["final_P"].mean(), 0.001),
        })
    ).round(4)
    print(cv.to_string())

    return df


def ki_nonmonotonicity_test():
    """
    Test whether Ki non-monotonicity in bear scenario is structural.
    Runs 5 Ki values × N_SEEDS seeds × bear scenario only.
    """
    print("\n" + "=" * 60)
    print("Ki NON-MONOTONICITY TEST")
    print(f"Ki values × {N_SEEDS} seeds × bear scenario")
    print("=" * 60)

    ki_values = [0.05, 0.10, 0.15, 0.25, 0.35]
    bear = SCENARIOS["bear"]
    results = []
    total = len(ki_values) * N_SEEDS
    count = 0

    for ki in ki_values:
        for seed_offset in range(N_SEEDS):
            seed = BASE_SEED + seed_offset
            count += 1
            if count % 25 == 0 or count == 1:
                print(f"  [{count}/{total}] Ki={ki:.2f}, seed={seed}", file=sys.stderr)

            records = run_simulation("bear", bear, True, seed,
                                     kp=KP_NORM, ki=ki, kd=KD_NORM)
            final_N = records[-1]["N"]
            results.append({"ki": ki, "seed": seed, "final_N": final_N})

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "ki_nonmonotonicity_test.csv"
    df.to_csv(out, index=False)

    # Test: for each seed, rank Ki values by final_N (higher = better)
    pivot = df.pivot(index="seed", columns="ki", values="final_N")
    rankings = pivot.rank(axis=1, ascending=False)  # rank 1 = highest N
    modal_rank = rankings.mode().iloc[0]
    consistency = (rankings == modal_rank).mean()

    print(f"\n  Mean final N by Ki value:")
    means = df.groupby("ki")["final_N"].agg(["mean", "std", "min", "max"])
    print(means.to_string())

    print(f"\n  Modal rank ordering: {modal_rank.to_dict()}")
    print(f"\n  Rank consistency across {N_SEEDS} seeds:")
    print(consistency.to_string())

    min_consistency = consistency.min()
    verdict = "STRUCTURAL" if min_consistency > 0.60 else "PATH-DEPENDENT"
    print(f"\n  Min consistency: {min_consistency:.2f}")
    print(f"  Verdict: {verdict}")
    if verdict == "STRUCTURAL":
        print("  → Paper's Ki non-monotonicity claim holds across seeds.")
    else:
        print("  → Paper must downgrade: 'observed in single-seed run; "
              "multi-seed testing shows rank ordering is seed-dependent.'")

    return df


if __name__ == "__main__":
    ensemble_df = run_ensemble()
    ki_df = ki_nonmonotonicity_test()
