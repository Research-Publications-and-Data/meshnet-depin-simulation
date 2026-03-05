#!/usr/bin/env python3
"""
Ki × Kd interaction grid (NEW — reviewer-requested).
2-D parameter interaction sweep: Ki × Kd, 5×5 = 25 parameter pairs × 4 scenarios = 100 runs.
Kp held at default 0.80.

Key question: Does Ki non-monotonicity in bear scenarios survive when Kd co-varies?
Output: results/interaction_sweep_results.csv
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import (run_simulation, SCENARIOS, SEED, N_TARGET,
                           KP_NORM, PID_MIN, PID_MAX, RESULTS_DIR)

KI_VALUES = [0.05, 0.10, 0.15, 0.25, 0.35]
KD_VALUES = [0.05, 0.10, 0.20, 0.35, 0.50]


def main():
    print("=" * 60)
    print("Ki × Kd INTERACTION SWEEP")
    print(f"Grid: {len(KI_VALUES)}×{len(KD_VALUES)} = {len(KI_VALUES)*len(KD_VALUES)} pairs "
          f"× {len(SCENARIOS)} scenarios = {len(KI_VALUES)*len(KD_VALUES)*len(SCENARIOS)} runs")
    print("=" * 60)

    results = []
    total = len(KI_VALUES) * len(KD_VALUES) * len(SCENARIOS)
    count = 0

    for ki in KI_VALUES:
        for kd in KD_VALUES:
            for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
                count += 1
                seed = SEED + scenario_idx
                print(f"  [{count}/{total}] Ki={ki:.2f}, Kd={kd:.2f}, {sname}",
                      file=sys.stderr)

                records = run_simulation(sname, scenario, True, seed,
                                         kp=KP_NORM, ki=ki, kd=kd)
                final = records[-1]
                n_series = [r["N"] for r in records]
                e_series = [r["E"] for r in records]

                # Count timesteps at floor/ceiling
                at_floor = sum(1 for e in e_series if e <= PID_MIN + 1)
                at_ceiling = sum(1 for e in e_series if e >= PID_MAX - 1)

                results.append({
                    "Ki": ki,
                    "Kd": kd,
                    "Kp": KP_NORM,
                    "scenario": sname,
                    "final_N": final["N"],
                    "dev_from_target": round(abs(final["N"] - N_TARGET) / N_TARGET, 4),
                    "total_emission": sum(r["E"] for r in records),
                    "total_slashed": final["slashed_total"],
                    "final_C": round(final["C"], 0),
                    "final_P": final["P"],
                    "at_floor_steps": at_floor,
                    "at_ceiling_steps": at_ceiling,
                })

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "interaction_sweep_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")

    # Report bear scenario Ki non-monotonicity
    print("\n── Ki Non-Monotonicity in Bear (with Kd co-varying) ──")
    bear = df[df["scenario"] == "bear"]
    pivot = bear.pivot_table(values="dev_from_target", index="Ki", columns="Kd")
    print(pivot.round(3).to_string())

    # Check if ordering is consistent across Kd values
    for kd in KD_VALUES:
        sub = bear[bear["Kd"] == kd].sort_values("Ki")
        devs = sub["dev_from_target"].values
        monotonic = all(devs[i] <= devs[i+1] for i in range(len(devs)-1))
        print(f"  Kd={kd:.2f}: Ki ordering monotonic={monotonic}, "
              f"devs={[f'{d:.3f}' for d in devs]}")


if __name__ == "__main__":
    main()
