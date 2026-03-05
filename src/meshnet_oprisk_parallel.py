#!/usr/bin/env python3
"""
Pub4 Operational Risk Layer — Parallel Runner.
Uses multiprocessing to run ~624 configurations efficiently.
"""
import json
import sys
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from multiprocessing import Pool, cpu_count
from functools import partial

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
EXHIBITS_DIR = ROOT / "exhibits"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
EXHIBITS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_oprisk import (
    run_simulation, SCENARIOS, N_TARGET, BASE_EMISSION,
    PARAM_SWEEPS, PROTOCOL_PROFILES, RHO_SWEEP, DELTA_REP,
    COLORS, INFRA_GROUPS,
)

N_SEEDS = 30
BASE_SEED = 1000
NCPU = max(1, cpu_count() - 1)


def _run_one(args):
    """Worker function for multiprocessing."""
    sname, scenario, use_pid, seed, op_risk, params, extra = args
    records = run_simulation(sname, scenario, use_pid, seed,
                             op_risk=op_risk, params=params)
    final = records[-1]
    final.update(extra)
    return final


def _run_one_full(args):
    """Worker returning full timeseries."""
    sname, scenario, use_pid, seed, op_risk, params, extra = args
    records = run_simulation(sname, scenario, use_pid, seed,
                             op_risk=op_risk, params=params)
    for r in records:
        r.update(extra)
    return records


def batch_ensemble(op_risk, label):
    """Run 30-seed × 4 scenarios × 2 models ensemble."""
    print(f"\n{'='*60}")
    print(f"{label} ({N_SEEDS * len(SCENARIOS) * 2} runs, {NCPU} workers)")
    print(f"{'='*60}")

    jobs = []
    for seed_offset in range(N_SEEDS):
        seed = BASE_SEED + seed_offset
        for sname, scenario in SCENARIOS.items():
            for use_pid in [True, False]:
                jobs.append((sname, scenario, use_pid, seed, op_risk, None, {}))

    t0 = time.time()
    with Pool(NCPU) as pool:
        results = pool.map(_run_one, jobs)
    elapsed = time.time() - t0
    print(f"  Completed {len(results)} runs in {elapsed:.0f}s ({elapsed/len(results):.1f}s/run)")
    return results


def batch_timeseries(op_risk, seed=42):
    """Run seed=42 full timeseries for all scenarios × models."""
    label = "oprisk" if op_risk else "baseline"
    print(f"\n  Running full timeseries (seed={seed}, {label})...")

    jobs = []
    for sname, scenario in SCENARIOS.items():
        for use_pid in [True, False]:
            jobs.append((sname, scenario, use_pid, seed, op_risk, None, {}))

    t0 = time.time()
    with Pool(NCPU) as pool:
        all_records = pool.map(_run_one_full, jobs)

    flat = [r for batch in all_records for r in batch]
    print(f"  {len(flat)} rows in {time.time()-t0:.0f}s")
    return flat


def batch_sweeps():
    """Batch 2: Per-parameter sweeps (84 runs)."""
    print(f"\n{'='*60}")
    print(f"BATCH 2: PARAMETER SWEEPS ({sum(len(v) for v in PARAM_SWEEPS.values()) * len(SCENARIOS)} runs)")
    print(f"{'='*60}")

    jobs = []
    for param_name, values in PARAM_SWEEPS.items():
        for val in values:
            for sname, scenario in SCENARIOS.items():
                extra = {'sweep_param': param_name, 'sweep_value': val}
                jobs.append((sname, scenario, True, 42, True, {param_name: val}, extra))

    t0 = time.time()
    with Pool(NCPU) as pool:
        results = pool.map(_run_one, jobs)
    print(f"  Completed {len(results)} runs in {time.time()-t0:.0f}s")
    return results


def batch_profiles():
    """Batch 3: Protocol profiles (12 runs)."""
    print(f"\n{'='*60}")
    print(f"BATCH 3: PROTOCOL PROFILES (12 runs)")
    print(f"{'='*60}")

    jobs = []
    for profile_name, profile_params in PROTOCOL_PROFILES.items():
        for sname, scenario in SCENARIOS.items():
            extra = {'profile': profile_name}
            jobs.append((sname, scenario, True, 42, True, profile_params, extra))

    t0 = time.time()
    with Pool(NCPU) as pool:
        results = pool.map(_run_one, jobs)
    print(f"  Completed {len(results)} runs in {time.time()-t0:.0f}s")
    return results


def batch_rho_sweep():
    """Batch 4: Correlated shock sweep (40 runs)."""
    print(f"\n{'='*60}")
    print(f"BATCH 4: CORRELATED SHOCK SWEEP (40 runs)")
    print(f"{'='*60}")

    jobs = []
    for rho in RHO_SWEEP:
        for sname, scenario in SCENARIOS.items():
            extra = {'rho_corr': rho}
            jobs.append((sname, scenario, True, 42, True, {'RHO_CORR': rho}, extra))

    t0 = time.time()
    with Pool(NCPU) as pool:
        results = pool.map(_run_one, jobs)
    print(f"  Completed {len(results)} runs in {time.time()-t0:.0f}s")
    return results


def batch_interaction():
    """Batch 5: Interaction tests (8 runs)."""
    print(f"\n{'='*60}")
    print(f"BATCH 5: INTERACTION TESTS (8 runs)")
    print(f"{'='*60}")

    jobs = []
    for delta_rep, label in [(0.0, "no_rep_penalty"), (DELTA_REP, "base")]:
        for sname, scenario in SCENARIOS.items():
            extra = {'interaction_label': label}
            jobs.append((sname, scenario, True, 42, True, {'DELTA_REP': delta_rep}, extra))

    t0 = time.time()
    with Pool(NCPU) as pool:
        results = pool.map(_run_one, jobs)
    print(f"  Completed {len(results)} runs in {time.time()-t0:.0f}s")
    return results


def gate_check(batch0_finals):
    """Verify Pub3 baseline reproduction."""
    print(f"\n{'='*60}")
    print("GATE CHECK: Pub3 Baseline Reproduction")
    print(f"{'='*60}")

    df = pd.DataFrame(batch0_finals)
    passed = True

    comp_pid = df[(df['scenario'] == 'competitor') & (df['emission_model'] == 'pid')]
    comp_sta = df[(df['scenario'] == 'competitor') & (df['emission_model'] == 'static')]

    if len(comp_pid) > 0:
        mean_n = comp_pid['N'].mean()
        std_n = comp_pid['N'].std()
        cv = std_n / max(mean_n, 1)
        p5 = comp_pid['N'].quantile(0.05)
        print(f"  Competitor PID: mean={mean_n:.0f}, std={std_n:.0f}, CV={cv:.3f}, 5pct={p5:.0f}")

    if len(comp_sta) > 0:
        mean_n = comp_sta['N'].mean()
        cv = comp_sta['N'].std() / max(mean_n, 1)
        p5 = comp_sta['N'].quantile(0.05)
        print(f"  Competitor Static: mean={mean_n:.0f}, CV={cv:.3f}, 5pct={p5:.0f}")

    for sname in SCENARIOS:
        pid_sub = df[(df['scenario'] == sname) & (df['emission_model'] == 'pid')]
        sta_sub = df[(df['scenario'] == sname) & (df['emission_model'] == 'static')]
        if len(pid_sub) > 0 and len(sta_sub) > 0:
            ratio = pid_sub['N'].mean() / max(sta_sub['N'].mean(), 1)
            status = "OK" if ratio >= 0.8 else "WARN"
            print(f"  {sname}: PID={pid_sub['N'].mean():.0f}, Static={sta_sub['N'].mean():.0f}, ratio={ratio:.2f} [{status}]")

    min_n = df['N'].min()
    print(f"  Node range: [{min_n}, {df['N'].max()}]")
    if min_n < 0:
        passed = False

    print(f"\n  GATE CHECK: {'PASSED' if passed else 'FAILED'}")
    return passed


def setup_chart_style():
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif'],
        'font.size': 11,
        'axes.titlesize': 13,
        'figure.figsize': (10, 6),
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'axes.grid': True,
        'grid.alpha': 0.3,
    })


def generate_exhibit_1(batch0_finals, batch1_finals):
    """PID Variance Compression With vs. Without Operational Risk."""
    setup_chart_style()
    df0 = pd.DataFrame(batch0_finals)
    df1 = pd.DataFrame(batch1_finals)

    groups = {
        'PID\n(econ only)': df0[(df0['scenario'] == 'competitor') & (df0['emission_model'] == 'pid')]['N'],
        'PID\n(+op risk)': df1[(df1['scenario'] == 'competitor') & (df1['emission_model'] == 'pid')]['N'],
        'Static\n(econ only)': df0[(df0['scenario'] == 'competitor') & (df0['emission_model'] == 'static')]['N'],
        'Static\n(+op risk)': df1[(df1['scenario'] == 'competitor') & (df1['emission_model'] == 'static')]['N'],
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [2, 1]})
    colors = [COLORS['pid_econ'], COLORS['pid_oprisk'], COLORS['static_econ'], COLORS['static_oprisk']]

    bp = ax1.boxplot([groups[k].values for k in groups], labels=list(groups.keys()),
                     patch_artist=True, widths=0.6)
    for patch, c in zip(bp['boxes'], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
    ax1.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5, label=f'Target ({N_TARGET:,})')
    ax1.set_ylabel('Final Node Count (Year 5)')
    ax1.set_title('Panel A: Node Count Distribution Under Competitor Shock')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

    cvs = {}
    cv_vals = []
    for label, series in groups.items():
        cv = series.std() / max(series.mean(), 1)
        cvs[label] = cv
        cv_vals.append(cv)

    bars = ax2.bar(range(len(cvs)), cv_vals, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax2.set_xticks(range(len(cvs)))
    ax2.set_xticklabels([k.replace('\n', ' ') for k in cvs], fontsize=8, rotation=15, ha='right')
    ax2.set_ylabel('Coefficient of Variation')
    ax2.set_title('Panel B: Variance Compression')
    for bar, cv in zip(bars, cv_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f'{cv:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    fig.suptitle('Exhibit 1: PID Variance Compression With vs. Without Operational Risk',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.text(0.01, -0.02, "Author's calculation. 30-seed ensemble, competitor shock scenario.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_1_variance_compression.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")
    return cvs


def generate_exhibit_2(ts_oprisk):
    """Correlated Failure Event Impact."""
    setup_chart_style()
    df = pd.DataFrame(ts_oprisk)
    comp = df[(df['scenario'] == 'competitor') & (df['emission_model'] == 'pid')]
    if len(comp) == 0:
        print("  WARNING: No data for Exhibit 2")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    t = comp['timestep'].values
    n = comp['N'].values

    ax.plot(t / 365, n, color=COLORS['pid_oprisk'], linewidth=1.5, label='PID + Op Risk')
    ax.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5, label=f'Target ({N_TARGET:,})')

    n_series = pd.Series(n)
    pct_change = n_series.pct_change()
    event_days = pct_change[pct_change < -0.02].index.tolist()
    clusters = []
    for d in event_days:
        if not clusters or d - clusters[-1][-1] > 14:
            clusters.append([d])
        else:
            clusters[-1].append(d)
    for cluster in clusters[:10]:
        start = cluster[0] / 365
        end = (cluster[-1] + 7) / 365
        ax.axvspan(start, end, alpha=0.15, color=COLORS['event_shade'], zorder=0)

    ax.set_xlabel('Year')
    ax.set_ylabel('Active Node Count')
    ax.set_title('Exhibit 2: Correlated Failure Event Impact on Network Size')
    ax.legend(loc='lower right')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    fig.text(0.01, -0.02, "Author's calculation. Competitor shock, seed=42. "
             "Red shading: epochs with >2% single-day drop.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_2_correlated_event.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


def generate_exhibit_3(ts_baseline, ts_oprisk):
    """Integral Over-Accumulation comparison."""
    setup_chart_style()
    df_base = pd.DataFrame(ts_baseline)
    df_op = pd.DataFrame(ts_oprisk)

    base = df_base[(df_base['scenario'] == 'competitor') & (df_base['emission_model'] == 'pid')]
    oprisk = df_op[(df_op['scenario'] == 'competitor') & (df_op['emission_model'] == 'pid')]
    if len(base) == 0 or len(oprisk) == 0:
        print("  WARNING: Missing data for Exhibit 3")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(base['timestep'].values / 365, base['pid_integral'].values,
             color=COLORS['pid_econ'], linewidth=1.5, label='Economic only')
    ax1.plot(oprisk['timestep'].values / 365, oprisk['pid_integral'].values,
             color=COLORS['pid_oprisk'], linewidth=1.5, label='+ Operational risk')
    ax1.axhline(0, color='black', linewidth=0.5)
    ax1.set_ylabel('PID Integral (normalized)')
    ax1.set_title('Panel A: Integral Accumulation')
    ax1.legend()

    ax2.plot(base['timestep'].values / 365, base['pid_emission_rate'].values,
             color=COLORS['pid_econ'], linewidth=1.5, label='Economic only')
    ax2.plot(oprisk['timestep'].values / 365, oprisk['pid_emission_rate'].values,
             color=COLORS['pid_oprisk'], linewidth=1.5, label='+ Operational risk')
    ax2.axhline(1.0, color='black', linestyle='--', linewidth=0.8, alpha=0.5, label='Base rate (1.0x)')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Emission Rate (multiple of base)')
    ax2.set_title('Panel B: Emission Rate Multiplier')
    ax2.legend()

    fig.suptitle('Exhibit 3: PID Integral Over-Accumulation Under Operational Risk',
                 fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.text(0.01, -0.02, "Author's calculation. Competitor shock, seed=42.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_3_integral_accumulation.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


def generate_exhibit_4(batch4_records):
    """Correlated Shock Sensitivity."""
    setup_chart_style()
    df = pd.DataFrame(batch4_records)
    comp = df[df['scenario'] == 'competitor']
    if len(comp) == 0:
        print("  WARNING: No data for Exhibit 4")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    rho_vals = sorted(comp['rho_corr'].unique())
    n_vals = [comp[comp['rho_corr'] == r]['N'].values[0] for r in rho_vals]

    ax.plot(np.array(rho_vals) * 100, n_vals, color=COLORS['pid_oprisk'],
            marker='o', linewidth=2, markersize=6, label='PID + Op Risk')
    ax.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5,
               label=f'Target ({N_TARGET:,})')
    ax.set_xlabel('RHO_CORR (%)')
    ax.set_ylabel('Final Node Count (Year 5)')
    ax.set_title('Exhibit 4: Correlated Shock Sensitivity (Competitor Scenario)')
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    fig.text(0.01, -0.02, "Author's calculation. Competitor shock, PID only, seed=42. "
             "Single-seed: directional sensitivity only.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_4_rho_sensitivity.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


def generate_exhibit_5(batch3_records):
    """Protocol-Specific Comparison."""
    setup_chart_style()
    df = pd.DataFrame(batch3_records)
    comp = df[df['scenario'] == 'competitor']
    if len(comp) == 0:
        print("  WARNING: No data for Exhibit 5")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    profiles = comp['profile'].unique()
    n_vals = [comp[comp['profile'] == p]['N'].values[0] for p in profiles]
    colors_bar = ['#2196F3', '#FF9800', '#4CAF50']

    bars = ax.bar(range(len(profiles)), n_vals, color=colors_bar[:len(profiles)],
                  alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5,
               label=f'Target ({N_TARGET:,})')
    ax.set_xticks(range(len(profiles)))
    ax.set_xticklabels([p.replace('_', ' ').title() for p in profiles], fontsize=10)
    ax.set_ylabel('Final Node Count (Year 5)')
    ax.set_title('Exhibit 5: Protocol-Specific Risk Profiles (Competitor Scenario)')
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    for bar, n in zip(bars, n_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{n:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    fig.text(0.01, -0.02, "Author's calculation. Competitor shock, PID only, seed=42.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_5_protocol_profiles.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


def build_results_summary(batch0_finals, batch1_finals, batch4_records, ts_oprisk):
    """Build results_summary.json."""
    df0 = pd.DataFrame(batch0_finals)
    df1 = pd.DataFrame(batch1_finals)
    summary = {"baseline": {}, "oprisk": {}, "hypotheses": {}}

    for label, df in [("baseline", df0), ("oprisk", df1)]:
        comp_pid = df[(df['scenario'] == 'competitor') & (df['emission_model'] == 'pid')]
        comp_sta = df[(df['scenario'] == 'competitor') & (df['emission_model'] == 'static')]
        pid_cv = sta_cv = 0
        if len(comp_pid) > 0:
            pid_cv = comp_pid['N'].std() / max(comp_pid['N'].mean(), 1)
            summary[label]["competitor_pid_mean"] = round(float(comp_pid['N'].mean()), 0)
            summary[label]["competitor_pid_cv"] = round(float(pid_cv), 4)
            summary[label]["competitor_pid_5pct"] = round(float(comp_pid['N'].quantile(0.05)), 0)
        if len(comp_sta) > 0:
            sta_cv = comp_sta['N'].std() / max(comp_sta['N'].mean(), 1)
            summary[label]["competitor_static_mean"] = round(float(comp_sta['N'].mean()), 0)
            summary[label]["competitor_static_cv"] = round(float(sta_cv), 4)
            summary[label]["competitor_static_5pct"] = round(float(comp_sta['N'].quantile(0.05)), 0)
        if pid_cv > 0 and sta_cv > 0:
            summary[label]["variance_compression_ratio"] = round(float(sta_cv / pid_cv), 2)

    base_ratio = summary["baseline"].get("variance_compression_ratio", 1)
    op_ratio = summary["oprisk"].get("variance_compression_ratio", 1)
    if op_ratio > 0:
        summary["hypotheses"]["h1_degradation_ratio"] = round(float(base_ratio / op_ratio), 2)

    if ts_oprisk:
        df_ts = pd.DataFrame(ts_oprisk)
        comp_ts = df_ts[(df_ts['scenario'] == 'competitor') & (df_ts['emission_model'] == 'pid')]
        if len(comp_ts) > 0:
            n_series = comp_ts['N'].values
            max_drop = 0
            for i in range(1, len(n_series)):
                drop = (n_series[i-1] - n_series[i]) / max(n_series[i-1], 1)
                max_drop = max(max_drop, drop)
            summary["hypotheses"]["h2_flash_crash_max_drop_pct"] = round(float(max_drop * 100), 2)

    op_comp = df1[(df1['scenario'] == 'competitor') & (df1['emission_model'] == 'pid')]
    if len(op_comp) > 0 and 'avg_reputation' in op_comp.columns:
        summary["hypotheses"]["h3_avg_reputation_oprisk"] = round(float(op_comp['avg_reputation'].mean()), 4)

    base_gap = summary["baseline"].get("competitor_pid_mean", 0) - summary["baseline"].get("competitor_static_mean", 0)
    op_gap = summary["oprisk"].get("competitor_pid_mean", 0) - summary["oprisk"].get("competitor_static_mean", 0)
    summary["hypotheses"]["h4_static_gap_widened"] = bool(op_gap > base_gap)

    return summary


def build_ensemble_comparison(batch0_finals, batch1_finals):
    """Build ensemble_comparison.csv."""
    df0 = pd.DataFrame(batch0_finals)
    df0['op_risk'] = False
    df1 = pd.DataFrame(batch1_finals)
    df1['op_risk'] = True
    combined = pd.concat([df0, df1], ignore_index=True)

    summary = combined.groupby(['scenario', 'emission_model', 'op_risk']).agg(
        N_mean=('N', 'mean'),
        N_std=('N', 'std'),
        N_p5=('N', lambda x: x.quantile(0.05)),
        N_p25=('N', lambda x: x.quantile(0.25)),
        N_median=('N', 'median'),
        N_p75=('N', lambda x: x.quantile(0.75)),
        N_p95=('N', lambda x: x.quantile(0.95)),
        P_mean=('P', 'mean'),
        n_runs=('N', 'count'),
    ).round(4)
    summary['N_cv'] = (summary['N_std'] / summary['N_mean'].clip(lower=1)).round(4)
    return summary


def main():
    t_start = time.time()
    print("=" * 70)
    print("PUB4: OPERATIONAL RISK LAYER — PARALLEL RUNNER")
    print(f"CPUs: {NCPU}, Seeds: {N_SEEDS}, Planned: ~624 configurations")
    print("=" * 70)

    # Batch 0: Baseline
    batch0_finals = batch_ensemble(op_risk=False, label="BATCH 0: BASELINE (240 runs)")
    gate_check(batch0_finals)
    ts_baseline = batch_timeseries(op_risk=False, seed=42)

    # Batch 1: Oprisk ensemble
    batch1_finals = batch_ensemble(op_risk=True, label="BATCH 1: OPRISK ENSEMBLE (240 runs)")
    ts_oprisk = batch_timeseries(op_risk=True, seed=42)

    # Batches 2-5
    batch2 = batch_sweeps()
    batch3 = batch_profiles()
    batch4 = batch_rho_sweep()
    batch5 = batch_interaction()

    # Save results
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")

    df_ts_base = pd.DataFrame(ts_baseline)
    df_ts_base.to_csv(RESULTS_DIR / "simulation_results_baseline.csv", index=False)
    print(f"  simulation_results_baseline.csv: {len(df_ts_base)} rows")

    oprisk_all = ts_oprisk + batch2 + batch3 + batch4 + batch5
    df_oprisk = pd.DataFrame(oprisk_all)
    df_oprisk.to_csv(RESULTS_DIR / "simulation_results_oprisk.csv", index=False)
    print(f"  simulation_results_oprisk.csv: {len(df_oprisk)} rows")

    ensemble = build_ensemble_comparison(batch0_finals, batch1_finals)
    ensemble.to_csv(RESULTS_DIR / "ensemble_comparison.csv")
    print(f"  ensemble_comparison.csv: {len(ensemble)} rows")
    print("\n" + ensemble.to_string())

    # Exhibits
    print(f"\n{'='*60}")
    print("GENERATING EXHIBITS")
    print(f"{'='*60}")

    cvs = generate_exhibit_1(batch0_finals, batch1_finals)
    generate_exhibit_2(ts_oprisk)
    generate_exhibit_3(ts_baseline, ts_oprisk)
    generate_exhibit_4(batch4)
    generate_exhibit_5(batch3)

    # Results summary
    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")

    summary = build_results_summary(batch0_finals, batch1_finals, batch4, ts_oprisk)
    summary_path = RESULTS_DIR / "results_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  Saved: {summary_path}")
    print(json.dumps(summary, indent=2, default=str))

    # Verification
    print(f"\n{'='*60}")
    print("VERIFICATION")
    print(f"{'='*60}")

    df0 = pd.DataFrame(batch0_finals)
    df1 = pd.DataFrame(batch1_finals)

    if 'avg_reputation' in df0.columns and 'avg_reputation' in df1.columns:
        b_rep = df0['avg_reputation'].mean()
        o_rep = df1['avg_reputation'].mean()
        print(f"  Reputation (base={b_rep:.3f}, oprisk={o_rep:.3f}): {'PASS' if o_rep < b_rep else 'WARN'}")

    all_n = pd.concat([df0['N'], df1['N']])
    print(f"  Node count non-negative (min={all_n.min()}): {'PASS' if all_n.min() >= 0 else 'FAIL'}")

    op_exits = df1.get('op_exited_total', pd.Series([0]))
    print(f"  Operational exits (total={op_exits.sum()}): {'PASS' if op_exits.sum() > 0 else 'WARN'}")

    total_runs = len(batch0_finals) + len(batch1_finals) + len(batch2) + len(batch3) + len(batch4) + len(batch5)
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"DONE — {total_runs} configs, {len(ts_baseline)+len(ts_oprisk)} timeseries rows")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
