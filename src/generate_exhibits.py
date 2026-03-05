#!/usr/bin/env python3
"""
Generate all 26 paper exhibits + 2 supplementary for the MeshNet tokenomics paper.
Reads simulation_results.csv, multi_seed_results.csv, and calibration_params.json.
"""
import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exhibit_style import (
    COLORS, SCENARIO_COLORS, SCENARIO_LINESTYLES, PALETTE_EXTENDED,
    setup_style, hide_spines, save_exhibit, add_source, EXHIBITS_DIR
)

ROOT = Path(__file__).resolve().parent.parent
SIM_PATH = ROOT / "results" / "simulation_results.csv"
CAL_PATH = ROOT / "calibration_params.json"

# Load data
def load_sim():
    return pd.read_csv(SIM_PATH)

def load_cal():
    with open(CAL_PATH) as f:
        return json.load(f)

def load_s2r():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import data_loader
    return data_loader.load_s2r_cleaned()

def load_governance():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import data_loader
    return data_loader.load_governance()


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 1: Coordination Technology Timeline
# ═══════════════════════════════════════════════════════════════
def exhibit_01():
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-1.6, 2.8)
    ax.axis('off')

    nodes = [
        (0.5, 1, "Markets", "Price signals\n& competition", "Information\nasymmetry", COLORS['accent1']),
        (1.5, 1, "Governments", "Law & taxation\n& regulation", "Regulatory\ncapture", COLORS['accent3']),
        (2.5, 1, "Corporations", "Hierarchy &\ncontracts", "Agency\ncosts", COLORS['accent1']),
        (3.5, 1, "Platforms", "APIs &\nalgorithms", "Rent\nextraction", COLORS['accent2']),
        (4.5, 1, "Protocols", "Tokens &\nconsensus", "Governance\ncapture?", COLORS['accent4']),
    ]
    for x, y, name, mechanism, failure, color in nodes:
        box = FancyBboxPatch((x-0.42, y-0.35), 0.84, 0.7, boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor='white', alpha=0.9, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=12,
                fontweight='bold', color='white')
        ax.text(x, y-0.85, mechanism, ha='center', va='top', fontsize=12,
                color=COLORS['text'], style='italic')
        ax.text(x, y+0.8, failure, ha='center', va='bottom', fontsize=10,
                color=COLORS['accent2'], alpha=0.85)
        if x < 4.5:
            ax.annotate('', xy=(x+0.52, y), xytext=(x+0.42, y),
                        arrowprops=dict(arrowstyle='->', color=COLORS['mid_gray'],
                                        lw=1.5))

    ax.text(2.5, 2.5, "Evolution of Coordination Technologies",
            ha='center', va='center', fontsize=16, fontweight='bold',
            color=COLORS['text'])
    ax.text(2.5, -1.4, "Increasing decentralization →", ha='center',
            fontsize=10, color=COLORS['mid_gray'], style='italic')
    add_source(fig, "Source: Adapted from Williamson (1985), Ostrom (1990), Lessig (2006).")
    save_exhibit(fig, "exhibit_02_coordination_timeline.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 2: Value Flow Comparison
# ═══════════════════════════════════════════════════════════════
def exhibit_02():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    def draw_flow(ax, title, nodes, edges, node_colors):
        ax.set_xlim(-2.2, 3.8)
        ax.set_ylim(-1, len(nodes))
        ax.axis('off')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
        positions = {}
        for i, (name, x) in enumerate(nodes):
            y = len(nodes) - 1 - i
            positions[name] = (x, y)
            c = node_colors.get(name, COLORS['accent1'])
            box = FancyBboxPatch((x-0.65, y-0.3), 1.3, 0.6,
                                 boxstyle="round,pad=0.05",
                                 facecolor=c, edgecolor='white', alpha=0.85, lw=1.5)
            ax.add_patch(box)
            ax.text(x, y, name, ha='center', va='center', fontsize=12,
                    fontweight='bold', color='white')
        # Draw downward edges (straight on right side) and return edge (curved on left)
        for src, dst, label in edges:
            sx, sy = positions[src]
            dx, dy = positions[dst]
            is_return = dy > sy  # return arrow goes upward
            if is_return:
                # Curved return arrow on the left side
                ax.annotate('', xy=(dx - 0.65, dy - 0.1), xytext=(sx - 0.65, sy + 0.1),
                            arrowprops=dict(arrowstyle='->', color=COLORS['mid_gray'],
                                            lw=1.2, connectionstyle='arc3,rad=-0.5'))
                # Label to the left of the curve — offset farther
                ax.text(-1.6, (sy + dy) / 2, label, fontsize=11, color=COLORS['mid_gray'],
                        ha='center', va='center', style='italic',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor=COLORS['grid'], alpha=0.9))
            else:
                # Straight downward arrow on the right side
                ax.annotate('', xy=(dx + 0.2, dy + 0.33), xytext=(sx + 0.2, sy - 0.33),
                            arrowprops=dict(arrowstyle='->', color=COLORS['mid_gray'],
                                            lw=1.2))
                # Label to the right of the arrow
                ax.text(2.3, (sy + dy) / 2, label, fontsize=11, color=COLORS['mid_gray'],
                        ha='left', va='center', style='italic')

    firm_nodes = [("Capital", 0.7), ("Labor", 0.7), ("Product", 0.7),
                  ("Profit", 0.7)]
    firm_colors = {n: COLORS['accent1'] for n, _ in firm_nodes}
    firm_colors["Capital"] = COLORS['accent3']
    firm_edges = [("Capital", "Labor", "wages"), ("Labor", "Product", "production"),
                  ("Product", "Profit", "revenue"), ("Profit", "Capital", "retained")]
    draw_flow(ax1, "Traditional Firm", firm_nodes, firm_edges, firm_colors)

    proto_nodes = [("Labor", 0.7), ("Protocol", 0.7), ("Token Dist.", 0.7),
                   ("Labor=Capital", 0.7)]
    proto_colors = {n: COLORS['accent4'] for n, _ in proto_nodes}
    proto_colors["Protocol"] = COLORS['accent2']
    proto_edges = [("Labor", "Protocol", "coverage/work"),
                   ("Protocol", "Token Dist.", "emissions"),
                   ("Token Dist.", "Labor=Capital", "ownership"),
                   ("Labor=Capital", "Labor", "governance")]
    draw_flow(ax2, "Protocol Model", proto_nodes, proto_edges, proto_colors)

    fig.tight_layout(w_pad=2)
    add_source(fig, "Source: Author's framework.")
    save_exhibit(fig, "exhibit_04_value_flow_comparison.png")  # was: exhibit_03


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 3: Historical Private Currency Issuance
# ═══════════════════════════════════════════════════════════════
def exhibit_03():
    years = [1790, 1800, 1810, 1820, 1830, 1840, 1845, 1850, 1855,
             1860, 1863, 1865, 1870]
    counts = [25, 100, 200, 300, 600, 1500, 2000, 3000, 5000,
              8000, 8000, 2000, 300]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.fill_between(years, counts, alpha=0.3, color=COLORS['accent1'])
    ax.plot(years, counts, color=COLORS['accent1'], linewidth=2.5, marker='o',
            markersize=5, zorder=5)
    ax.axvline(x=1863, color=COLORS['accent2'], linewidth=1.5, linestyle='--',
               alpha=0.7, zorder=3)
    ax.annotate("National Banking\nAct (1863)", xy=(1863, 6500),
                xytext=(1835, 5000), fontsize=9, color=COLORS['accent2'],
                fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=COLORS['accent2'], lw=1.2))
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Private Currencies")
    ax.set_title("Private Currency Issuance in the United States, 1790-1870")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    hide_spines(ax)
    add_source(fig, "Source: Gorton (1999), Rockoff (1974). Historical estimates.")
    save_exhibit(fig, "exhibit_03_private_currencies.png")  # was: exhibit_04


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 4: MeshNet System Map
# ═══════════════════════════════════════════════════════════════
def exhibit_04():
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-0.5, 13)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("MeshNet System Architecture", fontsize=16, fontweight='bold', pad=10)

    # Layout: fill the frame edge-to-edge
    # Rows: top (y=12), mid-upper (y=8.5), mid-lower (y=5), bottom (y=1.5)
    nodes = {
        "Node\nOperators":    (3.5,  12,   COLORS['accent4']),
        "Users":              (11.5, 12,   COLORS['accent6']),
        "Network":            (7.5,  8.5,  COLORS['primary']),
        "Treasury":           (2.5,  5,    COLORS['accent3']),
        "Burn\nAddress":      (2.5,  1.5,  COLORS['accent2']),
        "PID\nController":    (13,   5,    COLORS['accent5']),
        "Reputation\nSystem": (7,    1.5,  COLORS['accent1']),
        "Governance":         (11,   1.5,  COLORS['accent3']),
    }
    bw, bh = 3.0, 1.5  # box width/height — large enough to fill space
    for name, (x, y, color) in nodes.items():
        box = FancyBboxPatch((x - bw / 2, y - bh / 2), bw, bh,
                             boxstyle="round,pad=0.10", facecolor=color,
                             edgecolor='white', alpha=0.92, linewidth=2.5)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=14,
                fontweight='bold', color='white')

    # Edges: (src, dst, label, arc_rad, label_x, label_y)
    # All labels positioned along their arrow midpoints, away from any box
    edges = [
        # Node Operators → Network (coverage, down-right diagonal)
        ("Node\nOperators", "Network",           "coverage",              0.0,   4.0, 10.5),
        # Users → Network (fees, down-left diagonal)
        ("Users",           "Network",            "fees",                  0.0,  11.0, 10.5),
        # Network → Treasury (protocol fee, down-left)
        ("Network",         "Treasury",           "protocol fee (30%)",    0.0,   3.2,  7.3),
        # Treasury → Burn Address (buy-and-burn, straight down)
        ("Treasury",        "Burn\nAddress",      "buy-and-burn",          0.0,   0.2,  3.3),
        # PID Controller → Node Operators ($MESH emissions, arc up-left)
        ("PID\nController", "Node\nOperators",    "$MESH emissions",       0.3,  10.0, 10.5),
        # Node Operators → Reputation System (uptime proof, long diagonal)
        # Label at midpoint of arrow, offset right to avoid Treasury
        ("Node\nOperators", "Reputation\nSystem", "uptime proof",          0.0,   6.5,  7.3),
        # Reputation System → Governance (vote power, rightward)
        ("Reputation\nSystem","Governance",       "vote power\nmultiplier",0.0,   9.0,  0.0),
        # Governance → PID Controller (parameter adjustment, upward)
        ("Governance",      "PID\nController",    "parameter\nadjustment", 0.0,  13.8,  3.3),
    ]
    for src, dst, label, rad, lx, ly in edges:
        sx, sy = nodes[src][0], nodes[src][1]
        dx, dy = nodes[dst][0], nodes[dst][1]
        # Arrow endpoints at box edges
        if sy != dy:
            src_y = sy - bh / 2 * np.sign(sy - dy)
            dst_y = dy + bh / 2 * np.sign(sy - dy)
        else:
            src_y = sy
            dst_y = dy
        if sx != dx and sy == dy:
            src_x = sx + bw / 2 * np.sign(dx - sx)
            dst_x = dx - bw / 2 * np.sign(dx - sx)
        else:
            src_x = sx
            dst_x = dx
        ax.annotate('', xy=(dst_x, dst_y), xytext=(src_x, src_y),
                    arrowprops=dict(arrowstyle='->', color=COLORS['mid_gray'],
                                    lw=2.0, connectionstyle=f'arc3,rad={rad}'))
        ax.text(lx, ly, label, fontsize=11, color=COLORS['text'],
                ha='center', va='center', style='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=COLORS['grid'], alpha=0.95), zorder=5)

    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_05_meshnet_system_map.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 6: Voting Power Function (3D surface)
# ═══════════════════════════════════════════════════════════════
def exhibit_06():
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    tau = np.logspace(3, 5.7, 60)  # 1,000 to 500,000
    R = np.linspace(0, 5, 60)
    TAU, REP = np.meshgrid(tau, R)
    V = TAU * (1 + REP) ** 2

    surf = ax.plot_surface(np.log10(TAU), REP, V / 1e6, cmap='viridis',
                           alpha=0.75, edgecolor='none')
    ax.set_xlabel("log₁₀(Token Balance)", fontsize=12, labelpad=10)
    ax.set_ylabel("Reputation Score R(i)", fontsize=12, labelpad=10)
    ax.set_zlabel("Voting Power (millions)", fontsize=12, labelpad=10)
    ax.set_title("Voting Power: V(i) = τ(i) × (1 + R(i))²", fontsize=16,
                 fontweight='bold', pad=20)

    # Annotate key points
    whale_tau, whale_R = 100_000, 0
    whale_V = whale_tau * (1 + whale_R) ** 2
    op_tau, op_R = 10_000, 2
    op_V = op_tau * (1 + op_R) ** 2

    whale_color = '#ff4d6d'
    op_color = '#06d6a0'
    dot_edge = 'white'

    # Scatter dots in 3D space (visual anchors on the surface)
    whale_x = np.log10(whale_tau)
    whale_z = whale_V / 1e6
    op_x = np.log10(op_tau)
    op_z = op_V / 1e6

    ax.scatter([whale_x], [whale_R], [whale_z],
               color=whale_color, s=220, zorder=10,
               edgecolors=dot_edge, linewidths=2, depthshade=False)
    ax.scatter([op_x], [op_R], [op_z],
               color=op_color, s=220, zorder=10,
               edgecolors=dot_edge, linewidths=2, depthshade=False)

    ax.set_ylim(0, 5)
    ax.view_init(elev=25, azim=-50)
    fig.colorbar(surf, shrink=0.5, aspect=10, label='Voting Power (M)')

    # Finalize projection so 3D→2D coordinates are accurate
    fig.canvas.draw()

    # 2D annotations with arrows connecting labels to their 3D dots.
    # Project 3D scatter points into axes-fraction coordinates.
    from mpl_toolkits.mplot3d import proj3d

    def _project_to_axes_frac(ax, x3, y3, z3):
        x2, y2, _ = proj3d.proj_transform(x3, y3, z3, ax.get_proj())
        dot_disp = ax.transData.transform((x2, y2))
        return tuple(ax.transAxes.inverted().transform(dot_disp))

    for (x3, y3, z3, text_xy, clr, label) in [
        (whale_x, whale_R, whale_z, (0.52, 0.25), whale_color,
         f"Whale\n(100k, R=0)\nV={whale_V:,}"),
        (op_x, op_R, op_z, (0.22, 0.42), op_color,
         f"Operator\n(10k, R=2)\nV={op_V:,}"),
    ]:
        dot_xy = _project_to_axes_frac(ax, x3, y3, z3)
        ax.annotate(label, xy=dot_xy, xytext=text_xy,
                    xycoords='axes fraction', textcoords='axes fraction',
                    fontsize=8.5, ha='center', color=clr, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=clr, linewidth=1.5, alpha=0.95),
                    arrowprops=dict(arrowstyle='->', color=clr, lw=1.5))
    save_exhibit(fig, "exhibit_07_voting_power.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 7: Burn-Mint Equilibrium (with Helium S2R inset)
# ═══════════════════════════════════════════════════════════════
def exhibit_07():
    sim = load_sim()
    cal = load_cal()

    # Two-panel layout: main chart on top, Helium BME reference below
    # This avoids any inset-over-data overlap issues
    fig, (ax, ax_bme) = plt.subplots(2, 1, figsize=(11, 8),
                                      height_ratios=[3, 1],
                                      gridspec_kw={'hspace': 0.35})

    # ── Top panel: circulating supply ──
    for scen, label in [("bull", "High Adoption"), ("competitor", "Medium Adoption"),
                        ("bear", "Low Adoption")]:
        sub = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "pid")]
        months = sub["timestep"] / 30
        ax.plot(months, sub["C"] / 1e6, label=label,
                color=SCENARIO_COLORS[scen], linewidth=2)

    ax.set_xlabel("Month")
    ax.set_ylabel("Circulating Supply (millions $MESH)")
    ax.set_title("Burn-Mint Equilibrium: Circulating Supply Under Three Adoption Scenarios")
    ax.legend(loc='lower center', fontsize=10, ncol=3,
              bbox_to_anchor=(0.5, -0.02), framealpha=0.95)
    hide_spines(ax)

    # Annotate crossover for bull
    bull = sim[(sim["scenario"] == "bull") & (sim["emission_model"] == "pid")]
    crossover = bull[bull["s2r"] >= 1.0]
    if len(crossover) > 0:
        cross_month = crossover.iloc[0]["timestep"] / 30
        cross_C = crossover.iloc[0]["C"] / 1e6
        ax.axvline(x=cross_month, color=COLORS['accent2'], ls=':', alpha=0.5)
        ax.annotate(f"B(t) > E(t)\nMonth {cross_month:.0f}",
                    xy=(cross_month, cross_C), xytext=(cross_month + 5, cross_C + 20),
                    fontsize=8, color=COLORS['accent2'],
                    arrowprops=dict(arrowstyle='->', color=COLORS['accent2']))

    # ── Bottom panel: Helium Burn-Mint Equilibrium (empirical) ──
    try:
        s2r_df = load_s2r()
        months_real = np.arange(len(s2r_df))
        s2r_col = "s2r_clean" if "s2r_clean" in s2r_df.columns else "s2r"
        ax_bme.plot(months_real, s2r_df[s2r_col], color=COLORS['accent2'],
                    linewidth=1.5, marker='.', markersize=3)
        ax_bme.axhline(1.0, color=COLORS['mid_gray'], ls='--', lw=0.8)
        ax_bme.set_title("Helium Burn-Mint Equilibrium (empirical)", fontsize=12,
                         fontweight='bold')
        ax_bme.set_xlabel("Month", fontsize=12)
        ax_bme.set_ylabel("BME Ratio", fontsize=12)
        ax_bme.tick_params(labelsize=10)
        ax_bme.set_facecolor(COLORS['light_gray'])
        hide_spines(ax_bme)
    except Exception:
        ax_bme.text(0.5, 0.5, "Helium BME data not available",
                    ha='center', va='center', transform=ax_bme.transAxes, fontsize=10)
        ax_bme.axis('off')

    add_source(fig, "Source: Author's calculations; Helium on-chain data (Dune Analytics).")
    save_exhibit(fig, "exhibit_08_burn_mint_equilibrium.png")  # was: exhibit_10


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 8: Dynamic Fee Curves
# ═══════════════════════════════════════════════════════════════
def exhibit_08():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Urban congestion pricing
    congestion = np.linspace(0, 2.0, 200)
    base_fee = 0.05  # $0.05 base
    fee_floor = 0.02
    fee_ceiling = 0.50
    fee_mult = np.clip(1 + 2 * (congestion - 0.5) ** 2, 0.4, 10)
    urban_fee = np.clip(base_fee * fee_mult, fee_floor, fee_ceiling)

    ax1.plot(congestion, urban_fee, color=COLORS['accent1'], linewidth=2.5)
    ax1.axhline(fee_floor, color=COLORS['accent4'], ls='--', lw=1, label=f'Floor (${fee_floor})')
    ax1.axhline(fee_ceiling, color=COLORS['accent2'], ls='--', lw=1, label=f'Ceiling (${fee_ceiling})')
    ax1.fill_between(congestion, fee_floor, urban_fee, alpha=0.1, color=COLORS['accent1'])
    ax1.set_xlabel("Congestion Ratio (demand / capacity)")
    ax1.set_ylabel("Fee per Transaction ($)")
    ax1.set_title("Urban Zone: Congestion Pricing")
    ax1.legend()
    hide_spines(ax1)

    # Panel 2: Rural subsidy
    density = np.linspace(0, 1.0, 200)
    subsidy = np.exp(-3 * density)  # exponential decay subsidy
    rural_fee = base_fee * (1 - 0.8 * subsidy)

    ax2.plot(density, rural_fee, color=COLORS['accent4'], linewidth=2.5)
    ax2.plot(density, subsidy * base_fee, color=COLORS['accent3'], linewidth=1.5,
             ls='--', label='Subsidy amount')
    ax2.axhline(base_fee, color=COLORS['mid_gray'], ls=':', lw=1, label='Base fee')
    ax2.set_xlabel("Coverage Density (nodes / km²)")
    ax2.set_ylabel("Effective Fee ($)")
    ax2.set_title("Rural Zone: Coverage Subsidy")
    ax2.legend()
    hide_spines(ax2)

    fig.tight_layout()
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_11_dynamic_fee_curves.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 9: Token Allocation
# ═══════════════════════════════════════════════════════════════
def exhibit_09():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1.2]})

    categories = ['Node Operators', 'Retro Public Goods', 'Treasury',
                  'Team', 'Airdrop', 'Ecosystem', 'Market Makers']
    pcts = [40, 15, 15, 15, 8, 5.5, 1.5]
    colors_list = [COLORS['accent4'], COLORS['accent1'], COLORS['accent3'],
                   COLORS['accent2'], COLORS['accent5'], COLORS['accent6'],
                   COLORS['mid_gray']]

    # Horizontal bar with external labels for narrow segments
    left = 0
    bar_y = 0
    for cat, pct, c in zip(categories, pcts, colors_list):
        ax1.barh(bar_y, pct, left=left, color=c, height=0.6, edgecolor='white', lw=1)
        if pct >= 15:
            # Wide segments: label inside
            ax1.text(left + pct / 2, bar_y, f"{cat}\n{pct}%", ha='center', va='center',
                     fontsize=8, fontweight='bold', color='white')
        # Narrow segments handled below with external labels
        left += pct
    # External labels with leader lines for narrow segments (Airdrop 8%, Ecosystem 5.5%, Market Makers 1.5%)
    narrow_segments = [(4, "Airdrop", 8, colors_list[4]),
                       (5, "Ecosystem", 5.5, colors_list[5]),
                       (6, "Market Makers", 1.5, colors_list[6])]
    left_acc = sum(pcts[:4])  # left edge of Airdrop
    y_offsets = [0.7, 0.95, 1.2]  # staggered heights to avoid overlap
    for (idx, cat, pct, c), y_off in zip(narrow_segments, y_offsets):
        seg_center = left_acc + pct / 2
        ax1.annotate(f"{cat} {pct}%", xy=(seg_center, bar_y + 0.3),
                     xytext=(seg_center, y_off),
                     fontsize=8, fontweight='bold', color=c, ha='center', va='bottom',
                     arrowprops=dict(arrowstyle='->', color=c, lw=1.0, shrinkA=0, shrinkB=2))
        left_acc += pct
    ax1.set_xlim(0, 100)
    ax1.set_ylim(-0.5, 1.5)
    ax1.axis('off')
    ax1.set_title("$MESH Token Allocation (1B Total Supply)", fontsize=16, fontweight='bold')

    # Circulating supply timeline
    months = np.arange(0, 49)
    circ = np.zeros(len(months))
    # Airdrop: 25% TGE, 75% linear 12 months
    airdrop_total = 80_000_000
    circ += airdrop_total * 0.25  # TGE
    for m in range(1, 13):
        circ[m:] += airdrop_total * 0.75 / 12
    # Operator emissions: ~109k/day
    for m in months:
        circ[m] += 109_589 * 30 * m
    # Team: 1yr cliff then 3yr linear
    team_total = 150_000_000
    for m in range(12, 49):
        circ[m:] += team_total / 36 if m < 48 else 0
    # Ecosystem: linear 4yr
    eco_total = 55_000_000
    for m in months:
        circ[m] += eco_total / 48 * m
    circ = np.minimum(circ, 1_000_000_000)

    ax2.fill_between(months, circ / 1e6, alpha=0.3, color=COLORS['accent1'])
    ax2.plot(months, circ / 1e6, color=COLORS['accent1'], linewidth=2)
    ax2.axvline(12, color=COLORS['accent2'], ls=':', alpha=0.5)
    # Place "Team cliff unlocks" annotation well above the curve with a leader line
    y_max = circ.max() / 1e6
    ax2.annotate("Team cliff\nunlocks", xy=(12, circ[12] / 1e6),
                 xytext=(22, y_max * 0.92), fontsize=9,
                 color=COLORS['accent2'], fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=COLORS['accent2'], lw=1.2))
    ax2.set_xlabel("Months After TGE")
    ax2.set_ylabel("Circulating Supply (millions)")
    ax2.set_title("Projected Circulating Supply")
    hide_spines(ax2)

    fig.tight_layout()
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_12_token_allocation.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 10: Emission Schedule (PID vs fee revenue)
# ═══════════════════════════════════════════════════════════════
def exhibit_10():
    sim = load_sim()
    bull_pid = sim[(sim["scenario"] == "bull") & (sim["emission_model"] == "pid")]

    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    fig.subplots_adjust(right=0.82)  # extra right margin for endpoint labels
    months = bull_pid["timestep"] / 30

    ax1.plot(months, bull_pid["E"], color=COLORS['accent1'], linewidth=2,
             label='PID Emission Rate (tokens/day)')
    ax1.set_ylabel("Emission Rate (tokens/day)", color=COLORS['accent1'])
    ax1.set_xlabel("Month")
    ax1.tick_params(axis='y', labelcolor=COLORS['accent1'])

    ax2 = ax1.twinx()
    ax2.plot(months, bull_pid["F_daily"], color=COLORS['accent4'], linewidth=2,
             ls='--', label='Fee Revenue ($/day)')
    ax2.set_ylabel("Fee Revenue ($/day)", color=COLORS['accent4'])
    ax2.tick_params(axis='y', labelcolor=COLORS['accent4'])

    # Endpoint annotations — inside plot area to avoid clipping
    last_month = months.iloc[-1]
    last_E = bull_pid["E"].iloc[-1]
    last_F = bull_pid["F_daily"].iloc[-1]
    fee_pct = last_F / last_E * 100 if last_E > 0 else 0
    ax1.annotate(f"Emission: {last_E:,.0f} tokens/day",
                 xy=(last_month, last_E), xytext=(last_month - 15, last_E * 1.15),
                 fontsize=8, color=COLORS['accent1'], fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=COLORS['accent1'], lw=1))
    ax2.annotate(f"Fees: ${last_F:,.0f}/day ({fee_pct:.1f}% of emission)",
                 xy=(last_month, last_F), xytext=(last_month - 25, last_F * 1.12),
                 fontsize=8, color=COLORS['accent4'], fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=COLORS['accent4'], lw=1))

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')
    ax1.set_title("Emission-to-Fee Transition (Bull Scenario, PID Controller)")
    hide_spines(ax1)
    ax2.spines['top'].set_visible(False)

    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_13_emission_schedule.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 11: Airdrop Sizing Sensitivity
# ═══════════════════════════════════════════════════════════════
def exhibit_11():
    rng = np.random.default_rng(42)
    ratios = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    price_impacts = []
    for r in ratios:
        # Mercenary sell % increases with ratio
        sell_pct = 0.3 + 0.5 * (r - 0.2) / 0.6  # 30-80% sell
        airdrop_tokens = r * 200_000_000  # fraction of initial float
        sell_pressure = airdrop_tokens * sell_pct
        order_book_depth = 50_000_000  # tokens at various prices
        impact = sell_pressure / (order_book_depth + sell_pressure) * 100
        impact += rng.normal(0, 1.5)
        price_impacts.append(max(0, impact))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar([f"{int(r*100)}%" for r in ratios], price_impacts,
                  color=[COLORS['accent4'] if r <= 0.5 else COLORS['accent2'] for r in ratios],
                  edgecolor='white', linewidth=1.5, width=0.6)
    # Annotate MeshNet target — positioned far left above bars to avoid overlap
    target_idx = ratios.index(0.40)
    ax.annotate("MeshNet\ndesign target", xy=(target_idx, price_impacts[target_idx]),
                xytext=(target_idx - 1.8, max(price_impacts) * 0.95),
                fontsize=9, fontweight='bold', color=COLORS['accent4'],
                arrowprops=dict(arrowstyle='->', color=COLORS['accent4'], lw=1.5))

    ax.set_xlabel("Airdrop-to-Float Ratio")
    ax.set_ylabel("Estimated 30-Day Price Impact (%)")
    ax.set_title("Airdrop Sizing: Price Impact Sensitivity")
    ax.axhline(15, color=COLORS['mid_gray'], ls=':', lw=1, alpha=0.5)
    ax.text(5.2, 16, "Instability zone", fontsize=9, color=COLORS['accent2'],
            fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      edgecolor=COLORS['accent2'], alpha=0.8))
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_14_airdrop_sensitivity.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 12: Conviction Accumulation Curves
# ═══════════════════════════════════════════════════════════════
def exhibit_12():
    beta = 0.05
    days = np.arange(0, 91)
    profiles = [
        ("Small holder (1k)", 1_000, 60, COLORS['accent4']),
        ("Medium holder (10k)", 10_000, 30, COLORS['accent1']),
        ("Large holder (100k)", 100_000, 7, COLORS['accent3']),
        ("Whale flash (500k)", 500_000, 1, COLORS['accent2']),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for label, tau, signal_days, color in profiles:
        conv = np.zeros(len(days))
        for t in range(1, len(days)):
            signal = tau if t <= signal_days else 0
            conv[t] = conv[t-1] * (1 - beta) + signal * beta
        ax.plot(days, conv / 1000, label=label, color=color, linewidth=2.5)

    ax.set_xlabel("Days")
    ax.set_ylabel("Conviction Weight (thousands)")
    ax.set_title("Conviction Voting: Accumulated Weight Over Time")
    ax.legend(loc='upper right')
    ax.axvline(60, color=COLORS['mid_gray'], ls=':', alpha=0.3)
    ax.text(61, ax.get_ylim()[1] * 0.9, "60-day\nhorizon", fontsize=7,
            color=COLORS['mid_gray'])
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_15_conviction_curves.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 13: Governance Decision Tree
# ═══════════════════════════════════════════════════════════════
def exhibit_13():
    fig, ax = plt.subplots(figsize=(16, 7.5))
    ax.set_xlim(-0.5, 14.0)
    ax.set_ylim(-0.5, 6.0)
    ax.axis('off')
    ax.set_title("MeshNet Governance Decision Flow", fontsize=16,
                 fontweight='bold', pad=10)

    boxes = [
        (0.5,  3, "Proposal\nSubmitted", COLORS['accent1']),
        (2.8,  3, "Conviction\nThreshold?", COLORS['accent3']),
        (5.2,  4.2, "Critical\n(66%+7d)", COLORS['accent2']),
        (5.2,  3, "Major\n(50%+5d)", COLORS['accent5']),
        (5.2,  1.8, "Minor\n(33%+3d)", COLORS['accent4']),
        (7.5,  3, "Voting\nPeriod", COLORS['accent1']),
        (9.5,  3, "Operator\nVeto?", COLORS['accent2']),
        (11.3, 3, "Timelock\n(48h)", COLORS['accent3']),
        (13.0, 3, "Execute", COLORS['accent4']),
        (9.5,  0.8, "90-day\nSuspension", COLORS['accent2']),
    ]
    # Track diamond centers for arrow offset computation
    diamond_centers = set()
    for x, y, label, color in boxes:
        if "?" in label:
            w, h = 2.0, 1.2
            diamond = plt.Polygon([(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)],
                                  facecolor=color, edgecolor='white', alpha=0.9, lw=1.5)
            ax.add_patch(diamond)
            diamond_centers.add((x, y))
            ax.text(x, y, label, ha='center', va='center', fontsize=11,
                    fontweight='bold', color='white')
        else:
            w, h = 1.5, 0.8
            box = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.05",
                                 facecolor=color, edgecolor='white', alpha=0.9, lw=1.5)
            ax.add_patch(box)
            ax.text(x, y, label, ha='center', va='center', fontsize=11,
                    fontweight='bold', color='white')

    # Arrows — compute offsets based on whether source/dest is diamond
    arrow_pairs = [
        (0.5, 3, 2.8, 3), (2.8, 3, 5.2, 4.2), (2.8, 3, 5.2, 3),
        (2.8, 3, 5.2, 1.8), (5.2, 4.2, 7.5, 3), (5.2, 3, 7.5, 3),
        (5.2, 1.8, 7.5, 3), (7.5, 3, 9.5, 3), (9.5, 3, 11.3, 3),
        (11.3, 3, 13.0, 3),
    ]
    for sx, sy, dx, dy in arrow_pairs:
        src_off = 0.85 if (sx, sy) in diamond_centers else 0.65
        dst_off = 0.85 if (dx, dy) in diamond_centers else 0.65
        ax.annotate('', xy=(dx - dst_off, dy), xytext=(sx + src_off, sy),
                    arrowprops=dict(arrowstyle='->', color=COLORS['mid_gray'], lw=1.2))
    # Veto branch — starts from diamond bottom vertex (y - h/2 = 3 - 0.6 = 2.4)
    ax.annotate('', xy=(9.5, 1.2), xytext=(9.5, 2.4),
                arrowprops=dict(arrowstyle='->', color=COLORS['accent2'], lw=1.2))
    ax.text(10.3, 2.0, ">75%\noppose", fontsize=10, color=COLORS['accent2'])

    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_16_governance_flowchart.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 14: PID Controller Block Diagram
# ═══════════════════════════════════════════════════════════════
def exhibit_14():
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set_xlim(-1, 12)
    ax.set_ylim(-0.5, 3.8)
    ax.axis('off')
    ax.set_title("PID Emission Controller Block Diagram", fontsize=16,
                 fontweight='bold', pad=10)

    blocks = [
        (0.5, 2, "Setpoint\nN*=10,000", COLORS['accent4'], 1.8, 0.9),
        (2.5, 2, "Σ", COLORS['primary'], 0.7, 0.7),
        (4.5, 2, "PID\nController", COLORS['accent1'], 2.0, 0.9),
        (7, 2, "Emission\nE(t)", COLORS['accent3'], 1.8, 0.9),
        (9.5, 2, "MeshNet\nEconomy", COLORS['accent2'], 2.0, 0.9),
        (9.5, 0.2, "Node Count\nN(t)", COLORS['accent5'], 1.8, 0.7),
    ]
    for x, y, label, color, w, h in blocks:
        box = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor='white', alpha=0.9, lw=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=11,
                fontweight='bold', color='white')

    # Forward path arrows
    for sx, dx in [(1.4, 2.15), (2.85, 3.5), (5.5, 6.1), (7.9, 8.5)]:
        ax.annotate('', xy=(dx, 2), xytext=(sx, 2),
                    arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=1.8))

    # Feedback path — lowered to y=-0.1 for clear separation from Node Count box
    ax.annotate('', xy=(9.5, 1.55), xytext=(9.5, 0.55),
                arrowprops=dict(arrowstyle='<-', color=COLORS['text'], lw=1.5))
    ax.plot([9.5, 9.5], [-0.15, -0.1], color=COLORS['text'], lw=1.5)
    ax.plot([2.5, 2.5, 9.5], [-0.1, -0.1, -0.1], color=COLORS['text'], lw=1.5)
    ax.annotate('', xy=(2.5, 1.65), xytext=(2.5, -0.1),
                arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=1.5))

    # Labels on arrows — shifted to avoid overlapping Σ box and connector lines
    ax.text(3.5, 2.6, "error e(t)", fontsize=11, style='italic', color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor=COLORS['grid'], alpha=0.9), zorder=5)
    ax.text(6.6, 2.6, "E(t)", fontsize=11, style='italic', color=COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor=COLORS['grid'], alpha=0.9), zorder=5)

    # Disturbance
    ax.annotate('', xy=(9.5, 2.45), xytext=(9.5, 3.3),
                arrowprops=dict(arrowstyle='->', color=COLORS['accent2'], lw=1.5))
    ax.text(9.5, 3.5, "Disturbance\n(demand shocks)", ha='center', fontsize=10,
            color=COLORS['accent2'], fontweight='bold')
    ax.text(5.5, -0.7, "Feedback: N(t) → error → PID adjustment → E(t+1)",
            fontsize=10, style='italic', color=COLORS['mid_gray'], ha='center')

    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_17_pid_block_diagram.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 15: Emission Rate PID vs Static
# ═══════════════════════════════════════════════════════════════
def exhibit_15():
    sim = load_sim()
    fig, ax = plt.subplots(figsize=(10, 5.5))

    # Bull scenario primary
    bull_pid = sim[(sim["scenario"] == "bull") & (sim["emission_model"] == "pid")]
    bull_sta = sim[(sim["scenario"] == "bull") & (sim["emission_model"] == "static")]
    months = bull_pid["timestep"].values / 30

    ax.plot(months, bull_pid["E"], color=COLORS['accent1'], linewidth=2.5,
            label='PID (bull)', zorder=5)
    ax.plot(months, bull_sta["E"], color=COLORS['accent1'], linewidth=2,
            ls='--', alpha=0.6, label='Static (bull)')

    # Shade range across all 4 scenarios for PID
    all_pid_E = []
    for scen in SCENARIO_COLORS:
        sub = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "pid")]
        if len(sub) == len(months):
            all_pid_E.append(sub["E"].values)
    if all_pid_E:
        lo = np.min(all_pid_E, axis=0)
        hi = np.max(all_pid_E, axis=0)
        ax.fill_between(months, lo, hi, alpha=0.15, color=COLORS['accent1'],
                        label='PID range (all scenarios)')

    ax.set_xlabel("Month")
    ax.set_ylabel("Emission Rate (tokens/day)")
    ax.set_title("Emission Rate: PID Controller vs. Static Schedule")
    ax.legend(loc='upper right')
    hide_spines(ax)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_18_emission_pid_vs_static.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 16: Node Count Stability PID vs Static
# ═══════════════════════════════════════════════════════════════
def exhibit_16():
    sim = load_sim()
    fig, ax = plt.subplots(figsize=(10, 5.5))

    N_TARGET = 10_000
    band_lo = N_TARGET * 0.85
    band_hi = N_TARGET * 1.15

    ax.axhspan(band_lo, band_hi, alpha=0.1, color=COLORS['accent4'],
               label='±15% target band')
    ax.axhline(N_TARGET, color=COLORS['mid_gray'], ls=':', lw=1)

    for scen, color in SCENARIO_COLORS.items():
        pid = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "pid")]
        sta = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "static")]
        months = pid["timestep"].values / 30
        ax.plot(months, pid["N"], color=color, linewidth=2, label=f'{scen} (PID)')
        ax.plot(months, sta["N"], color=color, linewidth=1.2, ls='--', alpha=0.5)

    ax.set_xlabel("Month")
    ax.set_ylabel("Active Node Count")
    ax.set_title("Node Count Stability: PID vs. Static (dashed) Across Scenarios")
    ax.legend(loc='upper right', fontsize=10, ncol=2)
    ax.set_ylim(0, max(15000, ax.get_ylim()[1]))
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_19_node_count_stability.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 18: Token Price Trajectories
# ═══════════════════════════════════════════════════════════════
def exhibit_18():
    sim = load_sim()
    fig, ax = plt.subplots(figsize=(10, 5.5))

    for scen, color in SCENARIO_COLORS.items():
        pid = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "pid")]
        sta = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "static")]
        months = pid["timestep"].values / 30
        ax.plot(months, pid["P"], color=color, linewidth=2, label=f'{scen} (PID)')
        ax.plot(months, sta["P"], color=color, linewidth=1.2, ls='--', alpha=0.5)

    ax.set_xlabel("Month")
    ax.set_ylabel("Token Price ($)")
    ax.set_title("$MESH Price Trajectories: PID (solid) vs. Static (dashed)")
    ax.set_yscale('log')
    ax.legend(loc='best', fontsize=10, ncol=2)
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations; HNT price data (CoinGecko).")
    save_exhibit(fig, "exhibit_20_price_trajectories.png")  # was: exhibit_21


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 22: Wash Trading Impact
# ═══════════════════════════════════════════════════════════════
def exhibit_22():
    wt = pd.read_csv(ROOT / "results" / "wash_trading_results.csv")

    without_poc = wt[wt['poc'] == False]['fraud_rate_pct'].values
    with_poc = wt[wt['poc'] == True]['fraud_rate_pct'].values

    fig, ax = plt.subplots(figsize=(8, 5.5))
    positions = [0, 1]
    bp = ax.boxplot([without_poc, with_poc], positions=positions, widths=0.4,
                    patch_artist=True, showfliers=True,
                    flierprops=dict(marker='o', markersize=3, alpha=0.3))
    bp['boxes'][0].set_facecolor(COLORS['accent2'])
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor(COLORS['accent4'])
    bp['boxes'][1].set_alpha(0.7)
    for median in bp['medians']:
        median.set_color('white')
        median.set_linewidth(2)

    ax.set_xticks(positions)
    ax.set_xticklabels(["Without\nProof-of-Coverage", "With\nProof-of-Coverage"], fontsize=11)
    ax.set_ylabel("Emissions Captured by Fraudulent Nodes (%)")
    ax.set_title("Wash Trading Defense: Impact of Proof-of-Coverage")
    ax.axhline(5, color=COLORS['mid_gray'], ls=':', lw=1)
    ax.text(1.4, 5.5, "5% threshold", fontsize=8, color=COLORS['mid_gray'])
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_26_wash_trading_impact.png")  # was: exhibit_25


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 5: Whale Governance Power (with real protocol benchmarks)
# ═══════════════════════════════════════════════════════════════
def exhibit_05():
    fig, ax = plt.subplots(figsize=(10, 6))

    percentiles = [50, 75, 90, 95, 99]

    # Token-weighted model (Zipf-like distribution)
    rng = np.random.default_rng(42)
    n_holders = 10_000
    balances = rng.pareto(1.5, n_holders) * 1000
    balances = np.sort(balances)[::-1]
    total = balances.sum()
    cum_share = np.cumsum(balances) / total * 100

    token_power = []
    for p in percentiles:
        idx = int(n_holders * (1 - p / 100))
        token_power.append(cum_share[idx])

    # Reputation-weighted model
    reputations = np.zeros(n_holders)
    # Top 20% by balance get R=0-1, operators get R=2-5
    n_operators = int(n_holders * 0.4)
    reputations[:n_operators] = rng.uniform(1, 4, n_operators)
    # Whales (top 1%) get R=0
    reputations[:int(n_holders * 0.01)] = 0

    rep_power_raw = balances * (1 + reputations) ** 2
    rep_total = rep_power_raw.sum()
    rep_cum = np.cumsum(rep_power_raw) / rep_total * 100
    rep_power = []
    for p in percentiles:
        idx = int(n_holders * (1 - p / 100))
        rep_power.append(rep_cum[idx])

    x = np.arange(len(percentiles))
    width = 0.3
    bars1 = ax.bar(x - width/2, token_power, width, label='Token-Weighted',
                   color=COLORS['accent2'], alpha=0.8, edgecolor='white')
    bars2 = ax.bar(x + width/2, rep_power, width, label='Reputation-Weighted (MeshNet)',
                   color=COLORS['accent4'], alpha=0.8, edgecolor='white')

    # Real protocol Gini benchmarks as horizontal reference lines
    try:
        gov_df = load_governance()
        for _, row in gov_df.iterrows():
            if pd.notna(row.get("top1_share")):
                ax.axhline(row["top1_share"] * 100, color=COLORS['mid_gray'],
                           ls=':', lw=0.6, alpha=0.4)
        # Label a couple
        ax.text(len(percentiles) - 0.5, gov_df["top1_share"].max() * 100 + 1,
                f"Curve top-1: {gov_df['top1_share'].max():.0%}",
                fontsize=8, color=COLORS['mid_gray'])
        ax.text(len(percentiles) - 0.5, gov_df["top1_share"].min() * 100 + 1,
                f"Compound top-1: {gov_df['top1_share'].min():.0%}",
                fontsize=8, color=COLORS['mid_gray'])
    except Exception:
        pass

    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}th" for p in percentiles])
    ax.set_xlabel("Token Holding Percentile")
    ax.set_ylabel("Effective Governance Power (%)")
    ax.set_title("Governance Concentration: Token-Weighted vs. Reputation-Weighted")
    ax.legend(fontsize=10)
    hide_spines(ax)
    add_source(fig, "Source: Author's calculations; DeFi protocol data (Dune Analytics).")
    save_exhibit(fig, "exhibit_S1_whale_governance.png")  # supplementary


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 23: Token Design Discipline Map
# ═══════════════════════════════════════════════════════════════
def exhibit_23():
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-8.0, 8.0)
    ax.set_ylim(-8.0, 8.0)
    ax.axis('off')
    ax.set_aspect('equal')

    # Center
    center = FancyBboxPatch((-1.4, -0.6), 2.8, 1.2, boxstyle="round,pad=0.1",
                            facecolor=COLORS['primary'], edgecolor='white', lw=2)
    ax.add_patch(center)
    ax.text(0, 0, "Token\nDesign", ha='center', va='center', fontsize=16,
            fontweight='bold', color='white')

    disciplines = [
        ("Control\nTheory", "PID controllers\nFeedback loops\nStability analysis", COLORS['accent1']),
        ("Game\nTheory", "Minimax\nMechanism design\nNash equilibria", COLORS['accent2']),
        ("Political\nPhilosophy", "Categorical imperative\nLegitimacy\nSocial contract", COLORS['accent3']),
        ("Monetary\nEconomics", "Burn-mint equilibrium\nDynamic fees\nInflation targeting", COLORS['accent4']),
        ("Mechanism\nDesign", "Productive staking\nConviction voting\nRetroactive rewards", COLORS['accent5']),
        ("Behavioral\nPsychology", "Governance fatigue\nMercenary behavior\nExit thresholds", COLORS['accent6']),
        ("Distributed\nSystems", "Proof-of-coverage\nOn-chain verification\nSybil resistance", '#4895ef'),
        ("Constitutional\nDesign", "Tiered quorum\nVeto rights\nCommittee delegation", '#e07c24'),
    ]

    n = len(disciplines)
    radius = 4.8
    for i, (name, concepts, color) in enumerate(disciplines):
        angle = 2 * np.pi * i / n - np.pi / 2
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)

        # Spoke line — draw behind everything (low zorder)
        ax.plot([0, x * 0.7], [0, y * 0.7], color=COLORS['grid'], lw=1.5, zorder=0)

        # Node
        node_r = 1.1
        circle = plt.Circle((x, y), node_r, facecolor=color, edgecolor='white',
                             lw=2, alpha=0.9, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontsize=10,
                fontweight='bold', color='white', zorder=4)

        # Concept labels — pushed farther out with higher zorder
        # Increase distance for near-horizontal positions (3/9 o'clock) where
        # multi-line text boxes are wider and would overlap circles
        base_concept_r = radius + 2.2
        cos_val = abs(np.cos(angle))
        extra = 0.8 * cos_val  # extra push for horizontal positions
        concept_r = base_concept_r + extra
        cx = concept_r * np.cos(angle)
        cy = concept_r * np.sin(angle)
        ax.text(cx, cy, concepts, ha='center', va='center', fontsize=10,
                color=COLORS['text'], style='italic', zorder=5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=COLORS['grid'], alpha=0.95))

    ax.set_title("Interdisciplinary Foundations of Token Design", fontsize=16,
                 fontweight='bold', y=0.98)
    add_source(fig, "Source: Author's synthesis (Section 2).")
    save_exhibit(fig, "exhibit_01_discipline_map.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 20: PID Gain Sensitivity
# ═══════════════════════════════════════════════════════════════
def exhibit_20():
    """PID Gain Sensitivity: final deviation from N* across gain values."""
    sens_path = Path(__file__).resolve().parent.parent / "results" / "sensitivity_results.csv"
    df = pd.read_csv(sens_path)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

    for ax, param in zip(axes, ["Kp", "Ki", "Kd"]):
        sub = df[df["sweep_param"] == param]
        for scen, color in SCENARIO_COLORS.items():
            scen_data = sub[sub["scenario"] == scen].sort_values("param_value")
            ax.plot(scen_data["param_value"], scen_data["dev_from_target"] * 100,
                    color=color, marker='o', linewidth=2, markersize=6, label=scen)

        # Shade the "acceptable" zone (< 30% deviation)
        ax.axhspan(0, 30, alpha=0.08, color=COLORS['accent4'])
        ax.axhline(30, color=COLORS['mid_gray'], ls=':', lw=1, alpha=0.5)

        # Mark the chosen gain value
        chosen = {"Kp": 0.8, "Ki": 0.15, "Kd": 0.2}[param]
        ax.axvline(chosen, color=COLORS['accent2'], ls='--', lw=1.5, alpha=0.7)
        y_top = ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 50
        y_offset = 5.5 if param == "Kp" else 0  # shift Kp label up ~1 cm
        ax.text(chosen, y_top + y_offset,
                f' chosen={chosen}',
                fontsize=8, color=COLORS['accent2'], va='top')

        ax.set_xlabel(param)
        ax.set_title(f'{param} Sensitivity')
        hide_spines(ax)

    axes[0].set_ylabel('Deviation from N* at Year 5 (%)')
    axes[2].legend(loc='upper right', fontsize=9, bbox_to_anchor=(1.28, 1.0))

    fig.suptitle('PID Gain Sensitivity: Robustness Across Parameterizations',
                 fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    add_source(fig, "Source: Author's calculations. Each point = 1,825-day run. Other gains held at defaults.")
    save_exhibit(fig, "exhibit_24_pid_sensitivity.png")  # was: exhibit_23


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 21: Slashing Parameter Sensitivity
# ═══════════════════════════════════════════════════════════════
def exhibit_21():
    """Slashing parameter sensitivity: supply impact across scenarios."""
    slash_path = ROOT / "results" / "slashing_sensitivity_results.csv"
    df = pd.read_csv(slash_path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    # Left panel: downtime penalty
    dt_sub = df[df["sweep_param"] == "slash_downtime"]
    for scen, color in SCENARIO_COLORS.items():
        scen_data = dt_sub[dt_sub["scenario"] == scen].sort_values("param_value")
        ax1.plot(scen_data["param_value"], scen_data["C_change_pct"],
                 color=color, marker='o', linewidth=2, markersize=6, label=scen)

    # Healthy zone shading
    ax1.axhspan(-50, 10, alpha=0.06, color=COLORS['accent4'])
    ax1.axvline(0.10, color=COLORS['accent2'], ls='--', lw=1.5, alpha=0.7)
    ax1.text(0.10, ax1.get_ylim()[1] * 0.95 if ax1.get_ylim()[1] > 0 else 5,
             ' chosen=0.10', fontsize=8, color=COLORS['accent2'], va='top')
    ax1.set_xlabel("Downtime Penalty (fraction of stake)")
    ax1.set_ylabel("Circulating Supply Change (%)")
    ax1.set_title("Downtime Penalty Sensitivity")
    hide_spines(ax1)

    # Right panel: fraud penalty
    fr_sub = df[df["sweep_param"] == "slash_fraud"]
    for scen, color in SCENARIO_COLORS.items():
        scen_data = fr_sub[fr_sub["scenario"] == scen].sort_values("param_value")
        ax2.plot(scen_data["param_value"], scen_data["C_change_pct"],
                 color=color, marker='s', linewidth=2, markersize=6, label=scen)

    ax2.axhspan(-50, 10, alpha=0.06, color=COLORS['accent4'])
    ax2.axvline(1.00, color=COLORS['accent2'], ls='--', lw=1.5, alpha=0.7)
    ax2.text(1.00, ax2.get_ylim()[1] * 0.95 if ax2.get_ylim()[1] > 0 else 5,
             ' chosen=1.00', fontsize=8, color=COLORS['accent2'], va='top')
    ax2.set_xlabel("Fraud Penalty (fraction of stake)")
    ax2.set_title("Fraud Penalty Sensitivity")
    ax2.legend(loc='best', fontsize=10)
    hide_spines(ax2)

    fig.suptitle("Slashing Parameter Sensitivity: Supply Impact Across Scenarios",
                 fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    add_source(fig, "Source: Author's calculations. Each point = 1,825-day run. Other params at defaults.")
    save_exhibit(fig, "exhibit_25_slashing_sensitivity.png")  # was: exhibit_24


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# EXHIBIT 17: Ensemble Node Count Distributions (240-run)
# ═══════════════════════════════════════════════════════════════
def exhibit_17():
    ms = pd.read_csv(ROOT / "results" / "multi_seed_results.csv")
    scenarios = ['bull', 'competitor', 'regulatory', 'bear']
    titles = {'bull': 'Bull', 'competitor': 'Competitor Entry',
              'regulatory': 'Regulatory Shock', 'bear': 'Bear Market'}

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Ensemble Node Count Distributions (30 Seeds per Configuration)",
                 fontsize=16, fontweight='bold', y=0.97)

    for idx, scen in enumerate(scenarios):
        ax = axes[idx // 2][idx % 2]
        pid = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'pid')]['final_N']
        static = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'static')]['final_N']

        positions = [0, 1]
        bp = ax.boxplot([pid.values, static.values], positions=positions, widths=0.5,
                        patch_artist=True, showfliers=True,
                        flierprops=dict(marker='o', markersize=4, alpha=0.4),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5))
        for i, box in enumerate(bp['boxes']):
            box.set_facecolor(COLORS['accent6'] if i == 0 else COLORS['mid_gray'])
            box.set_alpha(0.7 if i == 0 else 0.5)
            box.set_linewidth(1)
            box.set_zorder(2)
        for whisker in bp['whiskers']:
            whisker.set_color('black')
            whisker.set_linewidth(1.5)
            whisker.set_zorder(3)
        for median in bp['medians']:
            median.set_color('white')
            median.set_linewidth(4)
            median.set_zorder(5)
        for cap in bp['caps']:
            cap.set_color('black')
            cap.set_linewidth(1.5)
            cap.set_zorder(6)

        # When median==Q3, the white median hides the box top border.
        # Redraw box top edge on top of everything.
        box_width = 0.5
        for i, data in enumerate([pid.values, static.values]):
            q3 = np.percentile(data, 75)
            med = np.median(data)
            pos = positions[i]
            half_bw = box_width / 2
            if med == q3:
                ax.plot([pos - half_bw, pos + half_bw], [q3, q3],
                        color='black', linewidth=1, zorder=7, solid_capstyle='butt')

        # Target line
        ax.axhline(10000, color=COLORS['accent2'], ls='--', lw=1, alpha=0.5)
        ax.text(-0.32, 10000, '10,000\ntarget', fontsize=7,
                color=COLORS['accent2'], va='center', ha='right')

        # Annotate CV and p5 below x-axis labels
        pid_cv = pid.std() / pid.mean() if pid.mean() > 0 else 0
        static_cv = static.std() / static.mean() if static.mean() > 0 else 0
        pid_p5 = pid.quantile(0.05)
        static_p5 = static.quantile(0.05)

        ax.set_xticks(positions)
        ax.set_xticklabels([f"PID\nCV={pid_cv:.3f}, p5={pid_p5:,.0f}",
                            f"Static\nCV={static_cv:.3f}, p5={static_p5:,.0f}"],
                           fontsize=10)
        ax.set_title(titles[scen], fontsize=12, fontweight='bold',
                     color=SCENARIO_COLORS[scen])
        ax.set_ylabel("Final Node Count" if idx % 2 == 0 else "")

        if scen == 'bull':
            ax.annotate(
                'All 30 seeds -> 11,934\n(growth cap: <1 new operator/day, int(30 x 0.033) = 0)',
                xy=(0.5, 11934), xycoords=('axes fraction', 'data'),
                fontsize=8, color=COLORS['mid_gray'], ha='center', va='top',
                xytext=(0, -8), textcoords='offset points',
            )

        hide_spines(ax)

    # Uniform y-axis across all panels
    all_N = ms['final_N']
    y_lo = max(0, all_N.min() - 500)
    y_hi = all_N.max() + 500
    for row in axes:
        for ax in row:
            ax.set_ylim(y_lo, y_hi)

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    add_source(fig, "Source: Author's calculations. 240-run ensemble (30 seeds x 8 configurations). "
               "Target: 10,000 nodes (dashed red).")
    save_exhibit(fig, "exhibit_22_ensemble_node_distributions.png")  # was: exhibit_20


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 19: Ensemble Price Distributions (240-run)
# ═══════════════════════════════════════════════════════════════
def exhibit_19():
    ms = pd.read_csv(ROOT / "results" / "multi_seed_results.csv")
    scenarios = ['bull', 'competitor', 'regulatory', 'bear']
    titles = {'bull': 'Bull', 'competitor': 'Competitor Entry',
              'regulatory': 'Regulatory Shock', 'bear': 'Bear Market'}

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Ensemble Price Distributions (30 Seeds per Configuration)",
                 fontsize=16, fontweight='bold', y=0.97)

    for idx, scen in enumerate(scenarios):
        ax = axes[idx // 2][idx % 2]
        pid = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'pid')]['final_P']
        static = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'static')]['final_P']

        positions = [0, 1]
        bp = ax.boxplot([pid.values, static.values], positions=positions, widths=0.5,
                        patch_artist=True, showfliers=True,
                        flierprops=dict(marker='o', markersize=4, alpha=0.4),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5))
        bp['boxes'][0].set_facecolor(COLORS['accent6'])
        bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_facecolor(COLORS['mid_gray'])
        bp['boxes'][1].set_alpha(0.5)
        for median in bp['medians']:
            median.set_color('white')
            median.set_linewidth(2)

        # Log scale for price
        ax.set_yscale('log')

        # Annotate CV and p5
        pid_cv = pid.std() / pid.mean() if pid.mean() > 0 else 0
        static_cv = static.std() / static.mean() if static.mean() > 0 else 0
        pid_p5 = pid.quantile(0.05)
        static_p5 = static.quantile(0.05)

        ax.set_xticks(positions)
        ax.set_xticklabels([f"PID\nCV={pid_cv:.3f}, p5=${pid_p5:.2f}",
                            f"Static\nCV={static_cv:.3f}, p5=${static_p5:.2f}"],
                           fontsize=10)
        ax.set_title(titles[scen], fontsize=12, fontweight='bold',
                     color=SCENARIO_COLORS[scen])
        ax.set_ylabel("Final $MESH Price (log)" if idx % 2 == 0 else "")
        hide_spines(ax)

    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    add_source(fig, "Source: Author's calculations. 240-run ensemble (30 seeds x 8 configurations). Log scale.")
    save_exhibit(fig, "exhibit_23_ensemble_price_distributions.png")  # was: exhibit_22


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 6 (Paper): Governance Concentration Across DePIN Protocols
# ═══════════════════════════════════════════════════════════════
def exhibit_06_gov():
    """Grouped bar chart: Gini and HHI across 12 DePIN protocols."""
    gov_path = ROOT / "data" / "raw" / "depin_governance.csv"
    df = pd.read_csv(gov_path)
    cal = load_cal()
    mesh_gini = cal["governance"]["mesh_target_gini"]
    mesh_hhi = cal["governance"]["mesh_target_hhi"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), gridspec_kw={'height_ratios': [1, 1]})

    x = np.arange(len(df))
    width = 0.55

    # Top panel: Gini coefficients
    bars1 = ax1.bar(x, df["gini"], width, color=COLORS['primary'], alpha=0.85,
                    edgecolor='white', linewidth=0.8, label='Token-Weighted Gini')
    ax1.axhline(mesh_gini, color=COLORS['accent2'], ls='--', lw=2,
                label=f'MeshNet target ({mesh_gini:.4f})')
    ax1.set_ylabel("Gini Coefficient")
    ax1.set_title("Token-Weighted Governance Concentration Across DePIN Protocols",
                  fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["protocol"], rotation=45, ha='right', fontsize=9)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.set_ylim(0, 1.1)
    hide_spines(ax1)

    # Bottom panel: HHI
    bars2 = ax2.bar(x, df["hhi"], width, color=COLORS['accent3'], alpha=0.85,
                    edgecolor='white', linewidth=0.8, label='HHI (Top-20 Delegate)')
    ax2.axhline(mesh_hhi, color=COLORS['accent2'], ls='--', lw=2,
                label=f'MeshNet target ({mesh_hhi:.4f})')
    ax2.set_ylabel("Herfindahl-Hirschman Index")
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["protocol"], rotation=45, ha='right', fontsize=9)
    ax2.legend(loc='upper right', fontsize=9)
    hide_spines(ax2)

    fig.tight_layout()
    add_source(fig, "Source: Author's calculations; on-chain governance data.")
    save_exhibit(fig, "exhibit_06_governance_concentration.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 9 (Paper): BME Trailing 12-Month Decomposition
# ═══════════════════════════════════════════════════════════════
def exhibit_09_bme():
    """Regenerate BME trailing 12-month from logistic fit parameters."""
    cal = load_cal()
    L = cal["s2r"]["logistic_L"]
    k = cal["s2r"]["logistic_k"]
    t0 = cal["s2r"]["logistic_t0"]

    # 34 months (May 2023 = month 1 to Feb 2026 = month 34)
    months = np.arange(1, 35)
    dates = pd.date_range("2023-05-01", periods=34, freq="MS")
    s2r = L / (1 + np.exp(-k * (months - t0)))

    # Synthetic monthly burn and emission from BME data
    bme_data = pd.read_csv(ROOT / "data" / "raw" / "helium_bme_monthly.csv")
    burn = bme_data["burn_hnt"].values
    emission = bme_data["emission_hnt"].values

    # Trailing 12-month BME ratio
    trailing_12 = np.full(len(months), np.nan)
    for i in range(11, len(months)):
        b12 = burn[i-11:i+1].sum()
        e12 = emission[i-11:i+1].sum()
        if e12 > 0:
            trailing_12[i] = b12 / e12

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), gridspec_kw={'height_ratios': [1, 1, 1.2]})

    # Panel 1: Monthly burn
    ax1 = axes[0]
    ax1.bar(dates, burn / 1e6, width=25, color=COLORS['accent2'], alpha=0.8,
            edgecolor='white', linewidth=0.5)
    ax1.set_ylabel("Monthly Burn (M HNT)")
    ax1.set_title("Helium Burn-Mint Equilibrium: Trailing 12-Month Decomposition",
                  fontsize=14, fontweight='bold')
    hide_spines(ax1)

    # Panel 2: Monthly emission
    ax2 = axes[1]
    ax2.bar(dates, emission / 1e6, width=25, color=COLORS['accent4'], alpha=0.8,
            edgecolor='white', linewidth=0.5)
    ax2.set_ylabel("Monthly Emission (M HNT)")
    hide_spines(ax2)

    # Panel 3: Trailing 12-month BME ratio + logistic fit
    ax3 = axes[2]
    valid = ~np.isnan(trailing_12)
    ax3.plot(dates[valid], trailing_12[valid], color=COLORS['accent1'], linewidth=2.5,
             marker='o', markersize=4, label='Trailing 12-month BME')
    ax3.plot(dates, s2r, color=COLORS['accent3'], linewidth=1.5, ls='--',
             label=f'Logistic fit (L={L:.2f}, k={k:.2f})')
    ax3.axhline(1.0, color=COLORS['mid_gray'], ls=':', lw=1, alpha=0.7)
    ax3.text(dates[-1], 1.02, "Parity", fontsize=8, color=COLORS['mid_gray'],
             ha='right', va='bottom')
    ax3.set_ylabel("BME Ratio (Burn / Emission)")
    ax3.set_xlabel("Date")
    ax3.legend(loc='upper left', fontsize=9)
    hide_spines(ax3)

    fig.tight_layout()
    add_source(fig, "Source: Author's calculations; Helium on-chain data (Dune Analytics).")
    save_exhibit(fig, "exhibit_09_bme_trailing_12month.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 10 (Paper): BME Under Three Adoption Scenarios
# ═══════════════════════════════════════════════════════════════
def exhibit_10_bme_scenarios():
    """BME trajectories for bull, bear, competitor scenarios (PID model)."""
    sim = load_sim()

    fig, ax = plt.subplots(figsize=(10, 5.5))

    for scen, label in [("bull", "High Adoption"), ("bear", "Low Adoption"),
                        ("competitor", "Competitor Entry")]:
        sub = sim[(sim["scenario"] == scen) & (sim["emission_model"] == "pid")]
        months = sub["timestep"] / 30
        ax.plot(months, sub["s2r"], label=label,
                color=SCENARIO_COLORS[scen],
                linestyle=SCENARIO_LINESTYLES[scen],
                linewidth=2.5)

    ax.axhline(1.0, color=COLORS['mid_gray'], ls=':', lw=1, alpha=0.7)
    ax.text(58, 1.03, "Parity", fontsize=9, color=COLORS['mid_gray'],
            ha='right', va='bottom')

    ax.set_xlabel("Month")
    ax.set_ylabel("Burn-Mint Equilibrium Ratio (B/E)")
    ax.set_title("Burn-Mint Equilibrium Under Three Adoption Scenarios (PID Controller)")
    ax.legend(loc='upper left', fontsize=10)
    hide_spines(ax)

    add_source(fig, "Source: Author's calculations.")
    save_exhibit(fig, "exhibit_10_bme_three_scenarios.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT 21 (Paper): Ensemble Competitor Scenario (Node Distributions)
# ═══════════════════════════════════════════════════════════════
def exhibit_21_competitor():
    """Single-panel boxplot: PID vs static node counts for competitor scenario."""
    ms = pd.read_csv(ROOT / "results" / "multi_seed_results.csv")
    scen = 'competitor'

    pid = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'pid')]['final_N']
    static = ms[(ms['scenario'] == scen) & (ms['emission_model'] == 'static')]['final_N']

    fig, ax = plt.subplots(figsize=(7, 6))

    positions = [0, 1]
    bp = ax.boxplot([pid.values, static.values], positions=positions, widths=0.5,
                    patch_artist=True, showfliers=True,
                    flierprops=dict(marker='o', markersize=4, alpha=0.4),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    bp['boxes'][0].set_facecolor(COLORS['accent6'])
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor(COLORS['mid_gray'])
    bp['boxes'][1].set_alpha(0.5)
    for median in bp['medians']:
        median.set_color('white')
        median.set_linewidth(3)

    # Target line
    ax.axhline(10000, color=COLORS['accent2'], ls='--', lw=1.5, alpha=0.6)
    ax.text(1.35, 10000, '10,000 target', fontsize=9,
            color=COLORS['accent2'], va='center')

    # Annotate statistics
    pid_cv = pid.std() / pid.mean() if pid.mean() > 0 else 0
    static_cv = static.std() / static.mean() if static.mean() > 0 else 0
    pid_p5 = pid.quantile(0.05)
    static_p5 = static.quantile(0.05)

    ax.set_xticks(positions)
    ax.set_xticklabels([f"PID\nCV={pid_cv:.3f}, p5={pid_p5:,.0f}",
                        f"Static\nCV={static_cv:.3f}, p5={static_p5:,.0f}"],
                       fontsize=10)
    ax.set_ylabel("Final Node Count")
    ax.set_title("Competitor Entry Scenario: Node Count Distributions (30 Seeds)",
                 fontsize=13, fontweight='bold', color=SCENARIO_COLORS['competitor'])
    hide_spines(ax)

    add_source(fig, "Source: Author's calculations. 30-seed ensemble per emission model.")
    save_exhibit(fig, "exhibit_21_ensemble_competitor.png")


# ═══════════════════════════════════════════════════════════════
# EXHIBIT S2 (Supplementary): S2R Timeline
# ═══════════════════════════════════════════════════════════════
def exhibit_S2_s2r():
    """Regenerate S2R timeline as supplementary exhibit."""
    try:
        s2r_df = load_s2r()
    except Exception:
        print("  S2R data not available, skipping exhibit S2")
        return
    cal = load_cal()
    L = cal["s2r"]["logistic_L"]
    k = cal["s2r"]["logistic_k"]
    t0 = cal["s2r"]["logistic_t0"]

    fig, ax = plt.subplots(figsize=(10, 5.5))

    if "period" in s2r_df.columns:
        dates = s2r_df["period"]
    elif "date" in s2r_df.columns:
        dates = pd.to_datetime(s2r_df["date"])
    else:
        dates = np.arange(len(s2r_df))

    s2r_col = "s2r" if "s2r" in s2r_df.columns else "s2r_clean"
    ax.plot(dates, s2r_df[s2r_col], color=COLORS['accent1'], linewidth=2,
            marker='o', markersize=4, label='Observed S2R')

    # Logistic fit overlay
    months = np.arange(1, len(s2r_df) + 1)
    s2r_fit = L / (1 + np.exp(-k * (months - t0)))
    ax.plot(dates, s2r_fit, color=COLORS['accent3'], linewidth=1.5, ls='--',
            label=f'Logistic fit (L={L:.2f})')

    ax.axhline(1.0, color=COLORS['mid_gray'], ls=':', lw=1)
    ax.set_xlabel("Date")
    ax.set_ylabel("Spend-to-Receive Ratio")
    ax.set_title("Helium Spend-to-Receive Ratio: Monthly Timeline")
    ax.legend(loc='upper left', fontsize=10)
    hide_spines(ax)

    add_source(fig, "Source: Author's calculations; Helium on-chain data (Dune Analytics).")
    save_exhibit(fig, "exhibit_S2_s2r_timeline.png")


# ═══════════════════════════════════════════════════════════════
# ALL EXHIBITS (Paper 1-26 + Supplementary S1-S2)
# ═══════════════════════════════════════════════════════════════
ALL_EXHIBITS = [
    ("Paper 1: Discipline Map", exhibit_23),
    ("Paper 2: Coordination Timeline", exhibit_01),
    ("Paper 3: Private Currencies", exhibit_03),
    ("Paper 4: Value Flow Comparison", exhibit_02),
    ("Paper 5: System Map", exhibit_04),
    ("Paper 6: Governance Concentration", exhibit_06_gov),
    ("Paper 7: Voting Power", exhibit_06),
    ("Paper 8: Burn-Mint Equilibrium", exhibit_07),
    ("Paper 9: BME Trailing 12-Month", exhibit_09_bme),
    ("Paper 10: BME Three Scenarios", exhibit_10_bme_scenarios),
    ("Paper 11: Dynamic Fee Curves", exhibit_08),
    ("Paper 12: Token Allocation", exhibit_09),
    ("Paper 13: Emission Schedule", exhibit_10),
    ("Paper 14: Airdrop Sensitivity", exhibit_11),
    ("Paper 15: Conviction Curves", exhibit_12),
    ("Paper 16: Governance Flowchart", exhibit_13),
    ("Paper 17: PID Block Diagram", exhibit_14),
    ("Paper 18: Emission PID vs Static", exhibit_15),
    ("Paper 19: Node Count Stability", exhibit_16),
    ("Paper 20: Price Trajectories", exhibit_18),
    ("Paper 21: Ensemble Competitor", exhibit_21_competitor),
    ("Paper 22: Ensemble Node Distributions", exhibit_17),
    ("Paper 23: Ensemble Price Distributions", exhibit_19),
    ("Paper 24: PID Gain Sensitivity", exhibit_20),
    ("Paper 25: Slashing Sensitivity", exhibit_21),
    ("Paper 26: Wash Trading Impact", exhibit_22),
    ("Supplementary S1: Whale Governance", exhibit_05),
    ("Supplementary S2: S2R Timeline", exhibit_S2_s2r),
]


def main():
    setup_style()
    print("=" * 60)
    print(f"GENERATING {len(ALL_EXHIBITS)} EXHIBITS (26 paper + 2 supplementary)")
    print("=" * 60)

    success = 0
    for name, func in ALL_EXHIBITS:
        try:
            print(f"\n{name}...")
            func()
            success += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Generated {success}/{len(ALL_EXHIBITS)} exhibits in {EXHIBITS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
