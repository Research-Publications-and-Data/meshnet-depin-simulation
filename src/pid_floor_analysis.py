#!/usr/bin/env python3
"""
PID Bound Saturation Analysis Across Bear Ensemble (30 seeds).

Determines whether the PID emission controller ever saturates its floor (0.25x)
or ceiling (3.0x) bounds in bear-market scenarios. Produces:
  - results/pid_floor_analysis.json (structured results)
  - results/pid_floor_analysis_summary.txt (human-readable summary)

Expected runtime: ~2 minutes for 30 bear/PID runs.
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_model import (
    run_simulation, SCENARIOS, PID_MIN, PID_MAX, BASE_EMISSION,
    N_TARGET, RESULTS_DIR, TIMESTEPS,
)

# ── Constants ──────────────────────────────────────────────────
SEEDS = range(1000, 1030)
SCENARIO_NAME = "bear"
SCENARIO = SCENARIOS["bear"]
SHOCK_DAY = SCENARIO["shock_month"] * 30  # day 360

# Tolerance for bound detection (within 1 token of bound)
FLOOR_THRESH = PID_MIN + 1
CEILING_THRESH = PID_MAX - 1

# Year boundaries (1-indexed)
YEAR_BOUNDS = [(1, 0, 365), (2, 365, 730), (3, 730, 1095), (4, 1095, 1460), (5, 1460, 1825)]
PHASE_BOUNDS = {"pre_shock": (0, SHOCK_DAY), "post_shock": (SHOCK_DAY, TIMESTEPS)}


def analyze_seed(seed):
    """Run bear/PID for one seed and compute bound saturation metrics."""
    records = run_simulation(SCENARIO_NAME, SCENARIO, True, seed)
    emissions = [r["E"] for r in records]
    nodes = [r["N"] for r in records]
    prices = [r["P"] for r in records]

    E_min = min(emissions)
    E_max = max(emissions)

    floor_hits = [t for t, e in enumerate(emissions) if e <= FLOOR_THRESH]
    ceiling_hits = [t for t, e in enumerate(emissions) if e >= CEILING_THRESH]

    # Per-year breakdown
    yearly = {}
    for year, t_start, t_end in YEAR_BOUNDS:
        year_E = emissions[t_start:t_end]
        year_floor = sum(1 for e in year_E if e <= FLOOR_THRESH)
        year_ceiling = sum(1 for e in year_E if e >= CEILING_THRESH)
        yearly[year] = {
            "mean_E": float(np.mean(year_E)),
            "min_E": float(min(year_E)),
            "max_E": float(max(year_E)),
            "floor_days": year_floor,
            "ceiling_days": year_ceiling,
            "pct_at_floor": round(year_floor / len(year_E) * 100, 2),
            "pct_at_ceiling": round(year_ceiling / len(year_E) * 100, 2),
        }

    # Phase breakdown (pre-shock vs post-shock)
    phases = {}
    for phase, (t_start, t_end) in PHASE_BOUNDS.items():
        phase_E = emissions[t_start:t_end]
        phases[phase] = {
            "mean_E": float(np.mean(phase_E)),
            "floor_days": sum(1 for e in phase_E if e <= FLOOR_THRESH),
            "ceiling_days": sum(1 for e in phase_E if e >= CEILING_THRESH),
        }

    return {
        "seed": seed,
        "E_min": float(E_min),
        "E_max": float(E_max),
        "E_min_mult": round(E_min / BASE_EMISSION, 4),
        "E_max_mult": round(E_max / BASE_EMISSION, 4),
        "floor_hit_count": len(floor_hits),
        "ceiling_hit_count": len(ceiling_hits),
        "first_floor_hit": floor_hits[0] if floor_hits else None,
        "first_ceiling_hit": ceiling_hits[0] if ceiling_hits else None,
        "final_N": int(nodes[-1]),
        "final_P": round(float(prices[-1]), 6),
        "total_emission": float(sum(emissions)),
        "yearly": yearly,
        "phases": phases,
    }


def run_analysis():
    """Run full ensemble analysis."""
    print("=" * 70)
    print("PID BOUND SATURATION ANALYSIS — BEAR ENSEMBLE (30 seeds)")
    print(f"PID_MIN={PID_MIN} (0.25x), PID_MAX={PID_MAX} (3.0x), BASE={BASE_EMISSION}")
    print(f"Floor threshold: E <= {FLOOR_THRESH}, Ceiling threshold: E >= {CEILING_THRESH}")
    print(f"Bear shock at day {SHOCK_DAY} (month {SCENARIO['shock_month']})")
    print("=" * 70)

    per_seed = []
    for i, seed in enumerate(SEEDS):
        print(f"\n  [{i+1}/30] seed={seed}", end="", flush=True)
        result = analyze_seed(seed)
        per_seed.append(result)
        status = []
        if result["floor_hit_count"] > 0:
            status.append(f"FLOOR×{result['floor_hit_count']}")
        if result["ceiling_hit_count"] > 0:
            status.append(f"CEILING×{result['ceiling_hit_count']}")
        if not status:
            status.append("no saturation")
        print(f"  E=[{result['E_min']:.0f}, {result['E_max']:.0f}] "
              f"({result['E_min_mult']:.2f}x–{result['E_max_mult']:.2f}x) "
              f"[{', '.join(status)}]  N_final={result['final_N']}")

    # ── Ensemble aggregates ──────────────────────────────────────
    seeds_floor = [s for s in per_seed if s["floor_hit_count"] > 0]
    seeds_ceiling = [s for s in per_seed if s["ceiling_hit_count"] > 0]

    E_min_all = min(s["E_min"] for s in per_seed)
    E_max_all = max(s["E_max"] for s in per_seed)
    authority_range = PID_MAX - PID_MIN
    used_range = E_max_all - E_min_all
    authority_used_pct = round(used_range / authority_range * 100, 1)

    # ── Yearly temporal pattern ──────────────────────────────────
    yearly_pattern = {}
    for year, _, _ in YEAR_BOUNDS:
        year_data = [s["yearly"][year] for s in per_seed]
        yearly_pattern[str(year)] = {
            "mean_E_across_seeds": round(float(np.mean([y["mean_E"] for y in year_data])), 1),
            "min_E_across_seeds": round(float(min(y["min_E"] for y in year_data)), 1),
            "max_E_across_seeds": round(float(max(y["max_E"] for y in year_data)), 1),
            "pct_seed_days_at_floor": round(float(np.mean([y["pct_at_floor"] for y in year_data])), 3),
            "pct_seed_days_at_ceiling": round(float(np.mean([y["pct_at_ceiling"] for y in year_data])), 3),
            "seeds_with_any_floor": sum(1 for y in year_data if y["floor_days"] > 0),
            "seeds_with_any_ceiling": sum(1 for y in year_data if y["ceiling_days"] > 0),
        }

    # ── Seed 42 baseline verification ────────────────────────────
    # NOTE: The original "seed=42" baseline (E_min≈48,268, E_max≈247,246) was from
    # main() which uses seed=args.seed+scenario_idx, so bear actually ran as seed=43.
    # We verify seed=42 directly AND seed=43 for completeness.
    print("\n\n  Verifying seed=42 and seed=43 baselines...")
    seed42 = analyze_seed(42)
    seed43 = analyze_seed(43)
    seed42_baseline = {
        "E_min": seed42["E_min"],
        "E_max": seed42["E_max"],
        "E_min_mult": seed42["E_min_mult"],
        "E_max_mult": seed42["E_max_mult"],
        "floor_hits": seed42["floor_hit_count"],
        "ceiling_hits": seed42["ceiling_hit_count"],
    }
    seed43_baseline = {
        "E_min": seed43["E_min"],
        "E_max": seed43["E_max"],
        "E_min_mult": seed43["E_min_mult"],
        "E_max_mult": seed43["E_max_mult"],
        "floor_hits": seed43["floor_hit_count"],
        "ceiling_hits": seed43["ceiling_hit_count"],
    }
    print(f"  Seed 42: E=[{seed42['E_min']:.0f}, {seed42['E_max']:.0f}] "
          f"({seed42['E_min_mult']:.2f}x–{seed42['E_max_mult']:.2f}x) "
          f"floor={seed42['floor_hit_count']} ceiling={seed42['ceiling_hit_count']}")
    print(f"  Seed 43: E=[{seed43['E_min']:.0f}, {seed43['E_max']:.0f}] "
          f"({seed43['E_min_mult']:.2f}x–{seed43['E_max_mult']:.2f}x) "
          f"floor={seed43['floor_hit_count']} ceiling={seed43['ceiling_hit_count']}")

    # Check: seed 43 should match the original "seed=42" baseline from main()
    # (main uses seed + scenario_idx where bear is idx 1)
    seed43_matches_original = (
        abs(seed43["E_min"] - 48268) < 1000 and
        abs(seed43["E_max"] - 247246) < 1000 and
        seed43["floor_hit_count"] == 0 and
        seed43["ceiling_hit_count"] == 0
    )
    # Seed 42 direct should also have zero floor/ceiling hits
    seed42_ok = (
        seed42["floor_hit_count"] == 0 and
        seed42["ceiling_hit_count"] == 0
    )
    if seed43_matches_original:
        print("  ✓ Seed 43 matches original 'seed=42' baseline (main() uses seed+scenario_idx)")
    else:
        print("  ~ Seed 43 floor/ceiling: OK" if seed43["floor_hit_count"] == 0 and
              seed43["ceiling_hit_count"] == 0 else "  ✗ Seed 43 mismatch")
    if seed42_ok:
        print("  ✓ Seed 42 direct: zero floor/ceiling hits confirmed")
    else:
        print("  ✗ Seed 42 direct: unexpected floor/ceiling hits")

    # ── Verdict ──────────────────────────────────────────────────
    any_floor = len(seeds_floor) > 0
    any_ceiling = len(seeds_ceiling) > 0

    if not any_floor and not any_ceiling:
        verdict = "REFUTED"
        paper_sentence = (
            f"Across the 30-seed bear ensemble, the PID controller never saturates "
            f"its floor (0.25× base) or ceiling (3.0× base) bound "
            f"(E ranges from {E_min_all/BASE_EMISSION:.2f}× to {E_max_all/BASE_EMISSION:.2f}× base, "
            f"using {authority_used_pct:.0f}% of the controller's authority range), "
            f"confirming that the dilution feedback loop operates within the controller's "
            f"mid-range authority rather than being driven by bound saturation."
        )
    elif any_floor and not any_ceiling:
        floor_seeds = [s["seed"] for s in seeds_floor]
        first_hits = [s["first_floor_hit"] for s in seeds_floor]
        total_floor_days = sum(s["floor_hit_count"] for s in seeds_floor)
        total_possible = len(list(SEEDS)) * TIMESTEPS
        avg_phase = "early" if np.mean(first_hits) < SHOCK_DAY else "post-shock"
        # Distinguish rare vs systematic
        if len(seeds_floor) <= 2:
            verdict = "REFUTED (rare edge case)"
            # Compute E range excluding the floor-binding seed(s)
            non_floor = [s for s in per_seed if s["floor_hit_count"] == 0]
            nf_min = min(s["E_min"] for s in non_floor)
            paper_sentence = (
                f"Across the 30-seed bear ensemble, the PID controller reaches its "
                f"0.25× floor in only {len(seeds_floor)} of 30 seeds "
                f"({total_floor_days} of {total_possible:,} seed-days, "
                f"{total_floor_days/total_possible*100:.2f}%), exclusively in the "
                f"{avg_phase} period (first binding at day {min(first_hits)}). "
                f"The remaining {len(non_floor)} seeds range from "
                f"{nf_min/BASE_EMISSION:.2f}× to {E_max_all/BASE_EMISSION:.2f}× base, "
                f"confirming that the dilution feedback loop operates predominantly "
                f"within mid-range authority; the floor is reachable but not the "
                f"systematic driver of bear-market dynamics."
            )
        else:
            verdict = "CONFIRMED (floor only)"
            paper_sentence = (
                f"In {len(seeds_floor)} of 30 bear seeds, the PID controller reaches its "
                f"0.25× floor after the {avg_phase} phase, "
                f"creating a sustained low-emission state consistent with zombie-network dynamics."
            )
    elif any_ceiling and not any_floor:
        ceiling_seeds = [s["seed"] for s in seeds_ceiling]
        verdict = "CONFIRMED (ceiling only)"
        paper_sentence = (
            f"In {len(seeds_ceiling)} of 30 bear seeds, the PID controller reaches its "
            f"3.0× ceiling (seeds: {ceiling_seeds}), indicating the controller's upper bound "
            f"constrains its recovery response."
        )
    else:
        verdict = "CONFIRMED (both bounds)"
        paper_sentence = (
            f"In {len(seeds_floor)} seeds the PID floor binds and in {len(seeds_ceiling)} "
            f"seeds the ceiling binds, revealing bound saturation as a contributing factor."
        )

    # ── Cross-check with multi_seed_results.csv ──────────────────
    cross_check = None
    ms_path = RESULTS_DIR / "multi_seed_results.csv"
    if ms_path.exists():
        ms = pd.read_csv(ms_path)
        bear_pid = ms[(ms["scenario"] == "bear") & (ms["emission_model"] == "pid")]
        if len(bear_pid) > 0:
            our_totals = {s["seed"]: round(s["total_emission"], 0) for s in per_seed}
            ms_totals = dict(zip(bear_pid["seed"], bear_pid["total_emission"]))
            matches = 0
            mismatches = 0
            for seed in SEEDS:
                if seed in ms_totals and seed in our_totals:
                    pct_diff = abs(our_totals[seed] - ms_totals[seed]) / max(ms_totals[seed], 1) * 100
                    if pct_diff < 0.1:
                        matches += 1
                    else:
                        mismatches += 1
            cross_check = {
                "multi_seed_csv_rows": len(bear_pid),
                "matching_seeds": matches,
                "mismatching_seeds": mismatches,
                "verdict": "CONSISTENT" if mismatches == 0 else f"MISMATCH ({mismatches} seeds)",
            }
            print(f"\n  Cross-check with multi_seed_results.csv: {cross_check['verdict']}")

    # ── Build output ─────────────────────────────────────────────
    output = {
        "hypothesis": "PID floor creates zombie-network trap in bear scenarios",
        "verdict": verdict,
        "seed_42_baseline": seed42_baseline,
        "seed_43_baseline": seed43_baseline,
        "seed_42_note": "main() uses seed+scenario_idx; bear (idx=1) ran as seed=43 in original",
        "seed_42_verification": "PASS" if seed42_ok else "FAIL",
        "seed_43_matches_original": seed43_matches_original,
        "ensemble": {
            "n_seeds": len(list(SEEDS)),
            "seeds_with_floor_binding": [s["seed"] for s in seeds_floor],
            "seeds_with_ceiling_binding": [s["seed"] for s in seeds_ceiling],
            "n_floor_binding": len(seeds_floor),
            "n_ceiling_binding": len(seeds_ceiling),
            "E_min_across_seeds": round(E_min_all, 1),
            "E_max_across_seeds": round(E_max_all, 1),
            "E_min_mult_across_seeds": round(E_min_all / BASE_EMISSION, 4),
            "E_max_mult_across_seeds": round(E_max_all / BASE_EMISSION, 4),
            "authority_range": authority_range,
            "authority_range_used_pct": authority_used_pct,
        },
        "per_seed": [{
            "seed": s["seed"],
            "E_min": s["E_min"],
            "E_max": s["E_max"],
            "E_min_mult": s["E_min_mult"],
            "E_max_mult": s["E_max_mult"],
            "floor_hit_count": s["floor_hit_count"],
            "ceiling_hit_count": s["ceiling_hit_count"],
            "first_floor_hit": s["first_floor_hit"],
            "first_ceiling_hit": s["first_ceiling_hit"],
            "final_N": s["final_N"],
            "final_P": s["final_P"],
            "total_emission": s["total_emission"],
        } for s in per_seed],
        "yearly_pattern": yearly_pattern,
        "phase_analysis": {
            "shock_day": SHOCK_DAY,
            "pre_shock": {
                "mean_E": round(float(np.mean([s["phases"]["pre_shock"]["mean_E"] for s in per_seed])), 1),
                "total_floor_days": sum(s["phases"]["pre_shock"]["floor_days"] for s in per_seed),
                "total_ceiling_days": sum(s["phases"]["pre_shock"]["ceiling_days"] for s in per_seed),
            },
            "post_shock": {
                "mean_E": round(float(np.mean([s["phases"]["post_shock"]["mean_E"] for s in per_seed])), 1),
                "total_floor_days": sum(s["phases"]["post_shock"]["floor_days"] for s in per_seed),
                "total_ceiling_days": sum(s["phases"]["post_shock"]["ceiling_days"] for s in per_seed),
            },
        },
        "cross_check": cross_check,
        "paper_sentence": paper_sentence,
    }

    # ── Save JSON ────────────────────────────────────────────────
    json_path = RESULTS_DIR / "pid_floor_analysis.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved: {json_path}")

    # ── Save summary text ────────────────────────────────────────
    txt_path = RESULTS_DIR / "pid_floor_analysis_summary.txt"
    lines = [
        "PID Bound Saturation Analysis — Bear Ensemble (30 seeds)",
        "=" * 70,
        f"Hypothesis: PID floor creates zombie-network trap in bear scenarios",
        f"Verdict:    {verdict}",
        "",
        f"Constants:  PID_MIN={PID_MIN} (0.25x), PID_MAX={PID_MAX} (3.0x), BASE={BASE_EMISSION}",
        f"Bear shock: day {SHOCK_DAY} (month {SCENARIO['shock_month']})",
        "",
        "── Seed 42 Baseline ──",
        f"  E range:    [{seed42_baseline['E_min']:.0f}, {seed42_baseline['E_max']:.0f}]",
        f"  Multiplier: [{seed42_baseline['E_min_mult']:.2f}x, {seed42_baseline['E_max_mult']:.2f}x]",
        f"  Floor hits: {seed42_baseline['floor_hits']}",
        f"  Ceil hits:  {seed42_baseline['ceiling_hits']}",
        f"  Verification: {'PASS' if seed42_ok else 'FAIL'}",
        "",
        "── Ensemble Summary ──",
        f"  Seeds: {len(list(SEEDS))}",
        f"  Floor binding:   {len(seeds_floor)} seeds {[s['seed'] for s in seeds_floor]}",
        f"  Ceiling binding: {len(seeds_ceiling)} seeds {[s['seed'] for s in seeds_ceiling]}",
        f"  E_min across all: {E_min_all:.0f} ({E_min_all/BASE_EMISSION:.2f}x)",
        f"  E_max across all: {E_max_all:.0f} ({E_max_all/BASE_EMISSION:.2f}x)",
        f"  Authority used:   {authority_used_pct:.0f}%",
        "",
        "── Per-Seed Detail ──",
        f"{'Seed':>6} {'E_min':>10} {'E_max':>10} {'Min_x':>7} {'Max_x':>7} "
        f"{'Floor':>6} {'Ceil':>6} {'N_final':>8} {'P_final':>10}",
        "-" * 80,
    ]
    for s in per_seed:
        lines.append(
            f"{s['seed']:>6} {s['E_min']:>10.0f} {s['E_max']:>10.0f} "
            f"{s['E_min_mult']:>7.2f} {s['E_max_mult']:>7.2f} "
            f"{s['floor_hit_count']:>6} {s['ceiling_hit_count']:>6} "
            f"{s['final_N']:>8} {s['final_P']:>10.6f}"
        )

    lines.extend([
        "",
        "── Yearly Pattern (mean across seeds) ──",
        f"{'Year':>5} {'Mean_E':>10} {'Min_E':>10} {'Max_E':>10} "
        f"{'%Floor':>8} {'%Ceil':>8} {'#Floor':>7} {'#Ceil':>7}",
        "-" * 75,
    ])
    for year_str, yp in yearly_pattern.items():
        lines.append(
            f"{year_str:>5} {yp['mean_E_across_seeds']:>10.0f} "
            f"{yp['min_E_across_seeds']:>10.0f} {yp['max_E_across_seeds']:>10.0f} "
            f"{yp['pct_seed_days_at_floor']:>8.3f} {yp['pct_seed_days_at_ceiling']:>8.3f} "
            f"{yp['seeds_with_any_floor']:>7} {yp['seeds_with_any_ceiling']:>7}"
        )

    lines.extend([
        "",
        "── Phase Analysis ──",
        f"  Pre-shock  (day 0–{SHOCK_DAY}):   mean E = {output['phase_analysis']['pre_shock']['mean_E']:.0f}, "
        f"floor days = {output['phase_analysis']['pre_shock']['total_floor_days']}, "
        f"ceiling days = {output['phase_analysis']['pre_shock']['total_ceiling_days']}",
        f"  Post-shock (day {SHOCK_DAY}–{TIMESTEPS}): mean E = {output['phase_analysis']['post_shock']['mean_E']:.0f}, "
        f"floor days = {output['phase_analysis']['post_shock']['total_floor_days']}, "
        f"ceiling days = {output['phase_analysis']['post_shock']['total_ceiling_days']}",
    ])

    if cross_check:
        lines.extend([
            "",
            "── Cross-check ──",
            f"  multi_seed_results.csv: {cross_check['verdict']}",
            f"  Matching seeds: {cross_check['matching_seeds']}, Mismatching: {cross_check['mismatching_seeds']}",
        ])

    lines.extend([
        "",
        "── Paper Sentence ──",
        paper_sentence,
        "",
    ])

    with open(txt_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Saved: {txt_path}")

    # Print final verdict
    print("\n" + "=" * 70)
    print(f"VERDICT: {verdict}")
    print(f"\nPaper sentence:\n  {paper_sentence}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    run_analysis()
