#!/usr/bin/env python3
"""
PID cadence sensitivity sweep (NEW — reviewer-requested).
Sweeps PID evaluation cadence: 7, 14, 21, 30 days.
4 cadences × 4 scenarios = 16 runs. PID only.

Key question: Does 14-day cadence outperform 7-day on noise filtering
while outperforming 30-day on shock responsiveness?
Output: results/cadence_sensitivity_results.csv
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import (run_simulation, SCENARIOS, SEED, N_TARGET,
                           BASE_EMISSION, PID_MIN, PID_MAX, RESULTS_DIR,
                           KP_NORM, KI_NORM, KD_NORM)
import meshnet_model as mm

CADENCES = [7, 14, 21, 30]


def main():
    print("=" * 60)
    print("CADENCE SENSITIVITY SWEEP")
    print(f"Cadences: {CADENCES} × {len(SCENARIOS)} scenarios = {len(CADENCES)*len(SCENARIOS)} runs")
    print("=" * 60)

    results = []
    total = len(CADENCES) * len(SCENARIOS)
    count = 0

    original_cadence = mm.PID_CADENCE

    for cadence in CADENCES:
        # Temporarily set PID cadence
        mm.PID_CADENCE = cadence

        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            count += 1
            seed = SEED + scenario_idx
            print(f"  [{count}/{total}] cadence={cadence}d, {sname}", file=sys.stderr)

            records = run_simulation(sname, scenario, True, seed)
            final = records[-1]

            n_series = [r["N"] for r in records]
            e_series = [r["E"] for r in records]

            # Count emission adjustments (times E changed)
            adjustments = sum(1 for i in range(1, len(e_series))
                              if e_series[i] != e_series[i-1])

            # Time at floor/ceiling
            at_floor = sum(1 for e in e_series if e <= PID_MIN + 1)
            at_ceiling = sum(1 for e in e_series if e >= PID_MAX - 1)

            # Emission volatility
            e_std = float(np.std(e_series))

            # Response time to shock (if shock exists)
            shock_month = scenario.get("shock_month")
            response_time = None
            if shock_month:
                shock_day = shock_month * 30
                pre_shock_e = e_series[max(0, shock_day - 10):shock_day]
                if pre_shock_e:
                    pre_mean = np.mean(pre_shock_e)
                    for t in range(shock_day, min(shock_day + 180, len(e_series))):
                        if abs(e_series[t] - pre_mean) / max(pre_mean, 1) > 0.05:
                            response_time = t - shock_day
                            break

            results.append({
                "cadence_days": cadence,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": round(abs(final["N"] - N_TARGET) / N_TARGET, 4),
                "n_adjustments": adjustments,
                "at_floor_steps": at_floor,
                "at_ceiling_steps": at_ceiling,
                "total_emission": sum(e_series),
                "emission_volatility": round(e_std, 1),
                "response_time_days": response_time,
                "final_P": final["P"],
            })

    # Restore original cadence
    mm.PID_CADENCE = original_cadence

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "cadence_sensitivity_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")

    # Summary
    print("\n── Cadence Comparison ──")
    summary = df.groupby("cadence_days").agg(
        mean_dev=("dev_from_target", "mean"),
        mean_adjustments=("n_adjustments", "mean"),
        mean_emission_vol=("emission_volatility", "mean"),
        mean_at_floor=("at_floor_steps", "mean"),
    ).round(3)
    print(summary.to_string())


if __name__ == "__main__":
    main()
