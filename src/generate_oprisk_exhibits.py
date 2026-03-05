#!/usr/bin/env python3
"""Regenerate Pub4 exhibits and results_summary from saved simulation data."""
import json
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
EXHIBITS_DIR = ROOT / "exhibits"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from meshnet_oprisk import N_TARGET, BASE_EMISSION, COLORS

COLORS = {
    'pid_econ': '#1f4e79',
    'pid_oprisk': '#c00000',
    'static_econ': '#666666',
    'static_oprisk': '#d4a017',
    'event_shade': '#ffe0e0',
}


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


def main():
    print("Loading ensemble comparison data...")
    ensemble = pd.read_csv(RESULTS_DIR / "ensemble_comparison.csv")
    print(ensemble.to_string())

    print("\nLoading timeseries data...")
    ts_base = pd.read_csv(RESULTS_DIR / "simulation_results_baseline.csv")
    ts_oprisk_full = pd.read_csv(RESULTS_DIR / "simulation_results_oprisk.csv")
    # Timeseries portion: rows with consecutive timesteps (not final-only batch records)
    ts_oprisk = ts_oprisk_full[ts_oprisk_full['timestep'].notna()]

    setup_chart_style()

    # ── Exhibit 1: Variance Compression ──────────────────────
    print("\nGenerating Exhibit 1...")
    # We need ensemble finals. Reconstruct from ensemble_comparison.csv stats
    # Actually we need raw finals. Let's use the ensemble CSV stats directly.

    # For box plots, we need the raw data. Let me use the timeseries final timesteps
    # from batch 0/1. We have 8 configs × 1825 timesteps in each ts file.
    # But batch 0/1 had 30 seeds each — only seed=42 is in ts files.
    # We'll use the ensemble stats for Panel B (CV bars) and skip box plots.

    fig, ax = plt.subplots(figsize=(10, 6))
    # Extract CV values from ensemble
    labels = []
    cvs = []
    colors_list = []

    for _, row in ensemble.iterrows():
        scenario = row.get('scenario', '')
        model = row.get('emission_model', '')
        oprisk = row.get('op_risk', '')
        cv = row.get('N_cv', 0)
        if scenario == 'competitor':
            if model == 'pid' and str(oprisk) == 'False':
                labels.append('PID (econ)')
                cvs.append(cv)
                colors_list.append(COLORS['pid_econ'])
            elif model == 'pid' and str(oprisk) == 'True':
                labels.append('PID (+oprisk)')
                cvs.append(cv)
                colors_list.append(COLORS['pid_oprisk'])
            elif model == 'static' and str(oprisk) == 'False':
                labels.append('Static (econ)')
                cvs.append(cv)
                colors_list.append(COLORS['static_econ'])
            elif model == 'static' and str(oprisk) == 'True':
                labels.append('Static (+oprisk)')
                cvs.append(cv)
                colors_list.append(COLORS['static_oprisk'])

    bars = ax.bar(range(len(labels)), cvs, color=colors_list, alpha=0.8,
                  edgecolor='black', linewidth=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('Coefficient of Variation (std/mean)')
    ax.set_title('Exhibit 1: PID Variance Compression With vs. Without Operational Risk\n'
                 '(Competitor Shock, 30-Seed Ensemble)')
    for bar, cv in zip(bars, cvs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f'{cv:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    fig.text(0.01, -0.03, "Author's calculation. 30-seed ensemble, competitor shock scenario. "
             "PID feedback controller reduces outcome variance even with operational risk layer.",
             fontsize=8, fontstyle='italic', color='#666666')
    path = EXHIBITS_DIR / "exhibit_1_variance_compression.png"
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")

    # ── Exhibit 2: Correlated Failure Event Impact ───────────
    print("Generating Exhibit 2...")
    comp_oprisk = ts_oprisk[(ts_oprisk['scenario'] == 'competitor') &
                            (ts_oprisk['emission_model'] == 'pid') &
                            (ts_oprisk['op_risk'] == True)]
    if len(comp_oprisk) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        t = comp_oprisk['timestep'].values
        n = comp_oprisk['N'].values
        ax.plot(t / 365, n, color=COLORS['pid_oprisk'], linewidth=1.5, label='PID + Op Risk')
        ax.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5,
                   label=f'Target ({N_TARGET:,})')

        # Shade large drops
        n_s = pd.Series(n)
        pct_change = n_s.pct_change()
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
        fig.text(0.01, -0.03, "Author's calculation. Competitor shock, seed=42. "
                 "Red shading: epochs with >2% single-day drop.",
                 fontsize=8, fontstyle='italic', color='#666666')
        path = EXHIBITS_DIR / "exhibit_2_correlated_event.png"
        fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        print(f"  Saved: {path}")
    else:
        print("  WARNING: No oprisk competitor/PID timeseries data")

    # ── Exhibit 3: Integral Over-Accumulation ────────────────
    print("Generating Exhibit 3...")
    base_comp = ts_base[(ts_base['scenario'] == 'competitor') & (ts_base['emission_model'] == 'pid')]
    oprisk_comp = ts_oprisk[(ts_oprisk['scenario'] == 'competitor') &
                            (ts_oprisk['emission_model'] == 'pid') &
                            (ts_oprisk['op_risk'] == True)]

    if len(base_comp) > 0 and len(oprisk_comp) > 0:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        ax1.plot(base_comp['timestep'].values / 365, base_comp['pid_integral'].values,
                 color=COLORS['pid_econ'], linewidth=1.5, label='Economic only')
        ax1.plot(oprisk_comp['timestep'].values / 365, oprisk_comp['pid_integral'].values,
                 color=COLORS['pid_oprisk'], linewidth=1.5, label='+ Operational risk')
        ax1.axhline(0, color='black', linewidth=0.5)
        ax1.set_ylabel('PID Integral (normalized)')
        ax1.set_title('Panel A: Integral Accumulation')
        ax1.legend()

        ax2.plot(base_comp['timestep'].values / 365, base_comp['pid_emission_rate'].values,
                 color=COLORS['pid_econ'], linewidth=1.5, label='Economic only')
        ax2.plot(oprisk_comp['timestep'].values / 365, oprisk_comp['pid_emission_rate'].values,
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

    # ── Exhibit 4: RHO Sensitivity ───────────────────────────
    print("Generating Exhibit 4...")
    # Batch 4 records are in oprisk file — they have rho_corr column
    if 'rho_corr' in ts_oprisk_full.columns:
        rho_data = ts_oprisk_full[ts_oprisk_full['rho_corr'].notna() &
                                   (ts_oprisk_full['scenario'] == 'competitor')]
        if len(rho_data) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            rho_vals = sorted(rho_data['rho_corr'].unique())
            n_vals = [rho_data[rho_data['rho_corr'] == r]['N'].values[0] for r in rho_vals]

            ax.plot(np.array(rho_vals) * 100, n_vals, color=COLORS['pid_oprisk'],
                    marker='o', linewidth=2, markersize=6, label='PID + Op Risk')
            ax.axhline(N_TARGET, color='black', linestyle='--', linewidth=0.8, alpha=0.5,
                       label=f'Target ({N_TARGET:,})')
            ax.set_xlabel('RHO_CORR (%)')
            ax.set_ylabel('Final Node Count (Year 5)')
            ax.set_title('Exhibit 4: Correlated Shock Sensitivity (Competitor Scenario)')
            ax.legend()
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
            fig.text(0.01, -0.03, "Author's calculation. Competitor shock, PID only, seed=42.",
                     fontsize=8, fontstyle='italic', color='#666666')
            path = EXHIBITS_DIR / "exhibit_4_rho_sensitivity.png"
            fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            print(f"  Saved: {path}")
        else:
            print("  WARNING: No rho_corr data for competitor scenario")
    else:
        print("  WARNING: No rho_corr column in oprisk data")

    # ── Exhibit 5: Protocol Profiles ─────────────────────────
    print("Generating Exhibit 5...")
    if 'profile' in ts_oprisk_full.columns:
        profile_data = ts_oprisk_full[ts_oprisk_full['profile'].notna() &
                                       (ts_oprisk_full['scenario'] == 'competitor')]
        if len(profile_data) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            profiles = profile_data['profile'].unique()
            n_vals = [profile_data[profile_data['profile'] == p]['N'].values[0] for p in profiles]
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
            fig.text(0.01, -0.03, "Author's calculation. Competitor shock, PID only, seed=42.",
                     fontsize=8, fontstyle='italic', color='#666666')
            path = EXHIBITS_DIR / "exhibit_5_protocol_profiles.png"
            fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            print(f"  Saved: {path}")
        else:
            print("  WARNING: No profile data for competitor")
    else:
        print("  WARNING: No profile column in oprisk data")

    # ── Results Summary ──────────────────────────────────────
    print("\nBuilding results_summary.json...")
    summary = {"baseline": {}, "oprisk": {}, "hypotheses": {}}

    for _, row in ensemble.iterrows():
        scenario = row.get('scenario', '')
        model = row.get('emission_model', '')
        oprisk = str(row.get('op_risk', ''))

        if scenario != 'competitor':
            continue

        label = "baseline" if oprisk == 'False' else "oprisk"
        if model == 'pid':
            summary[label]["competitor_pid_mean"] = round(float(row['N_mean']), 0)
            summary[label]["competitor_pid_cv"] = round(float(row['N_cv']), 4)
            summary[label]["competitor_pid_5pct"] = round(float(row['N_p5']), 0)
        elif model == 'static':
            summary[label]["competitor_static_mean"] = round(float(row['N_mean']), 0)
            summary[label]["competitor_static_cv"] = round(float(row['N_cv']), 4)
            summary[label]["competitor_static_5pct"] = round(float(row['N_p5']), 0)

    for label in ["baseline", "oprisk"]:
        pid_cv = summary[label].get("competitor_pid_cv", 0)
        sta_cv = summary[label].get("competitor_static_cv", 0)
        if pid_cv > 0:
            summary[label]["variance_compression_ratio"] = round(sta_cv / pid_cv, 2)

    base_ratio = summary["baseline"].get("variance_compression_ratio", 1)
    op_ratio = summary["oprisk"].get("variance_compression_ratio", 1)
    if op_ratio > 0:
        summary["hypotheses"]["h1_degradation_ratio"] = round(base_ratio / op_ratio, 2)

    # H2: max flash crash drop from oprisk timeseries
    if len(oprisk_comp) > 0:
        n_series = oprisk_comp['N'].values
        max_drop = 0
        for i in range(1, len(n_series)):
            drop = (n_series[i-1] - n_series[i]) / max(n_series[i-1], 1)
            max_drop = max(max_drop, drop)
        summary["hypotheses"]["h2_flash_crash_max_drop_pct"] = round(float(max_drop * 100), 2)

    # H3: avg reputation under oprisk
    if 'avg_reputation' in oprisk_comp.columns:
        final_rep = oprisk_comp.iloc[-1].get('avg_reputation', None)
        if final_rep is not None:
            summary["hypotheses"]["h3_avg_reputation_oprisk_final"] = round(float(final_rep), 4)

    # H4: Static gap widened
    base_gap = summary["baseline"].get("competitor_pid_mean", 0) - summary["baseline"].get("competitor_static_mean", 0)
    op_gap = summary["oprisk"].get("competitor_pid_mean", 0) - summary["oprisk"].get("competitor_static_mean", 0)
    summary["hypotheses"]["h4_static_gap_widened"] = bool(op_gap > base_gap)

    summary_path = RESULTS_DIR / "results_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  Saved: {summary_path}")
    print(json.dumps(summary, indent=2, default=str))

    print("\nDone!")


if __name__ == "__main__":
    main()
