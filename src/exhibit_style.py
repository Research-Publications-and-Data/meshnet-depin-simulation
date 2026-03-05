#!/usr/bin/env python3
"""
House style and shared utilities for all exhibits.
Publication palette: NAVY, GOLD, CRIMSON, STEEL, SAGE.
Serif fonts, 300 DPI, grayscale-distinguishable.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from pathlib import Path

EXHIBITS_DIR = Path(__file__).resolve().parent.parent / "exhibits"
EXHIBITS_DIR.mkdir(parents=True, exist_ok=True)

# Publication palette
NAVY    = '#1f3d73'
GOLD    = '#c4a035'
CRIMSON = '#8b1a1a'
STEEL   = '#4a6fa5'
SAGE    = '#5c7a5c'

COLORS = {
    'primary':    NAVY,
    'secondary':  STEEL,
    'accent1':    NAVY,
    'accent2':    CRIMSON,
    'accent3':    GOLD,
    'accent4':    SAGE,
    'accent5':    GOLD,
    'accent6':    STEEL,
    'grid':       '#e0e0e0',
    'text':       NAVY,
    'bg':         '#ffffff',
    'light_gray': '#f5f5f5',
    'mid_gray':   '#999999',
}

SCENARIO_COLORS = {
    'bull':       SAGE,
    'bear':       CRIMSON,
    'competitor': GOLD,
    'regulatory': STEEL,
}

SCENARIO_LINESTYLES = {
    'bull':       '-',
    'bear':       '--',
    'competitor': '-.',
    'regulatory': ':',
}

# Extended palette for exhibits needing 6+ distinct colors
PALETTE_EXTENDED = [
    NAVY,           # 0
    CRIMSON,        # 1
    GOLD,           # 2
    SAGE,           # 3
    STEEL,          # 4
    '#2d5016',      # 5 dark olive
    '#6b3a3a',      # 6 muted burgundy
    '#7a6520',      # 7 dark gold
]

def setup_style():
    plt.rcParams.update({
        'figure.facecolor': COLORS['bg'],
        'axes.facecolor': COLORS['bg'],
        'axes.edgecolor': COLORS['grid'],
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': COLORS['grid'],
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'Georgia'],
        'font.size': 11,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16,
        'figure.titleweight': 'bold',
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'legend.framealpha': 0.9,
        'legend.edgecolor': COLORS['grid'],
    })

def hide_spines(ax, keep_left=True, keep_bottom=True):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if not keep_left:
        ax.spines['left'].set_visible(False)
    if not keep_bottom:
        ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_color(COLORS['grid'])
    ax.spines['bottom'].set_color(COLORS['grid'])

def save_exhibit(fig, name):
    path = EXHIBITS_DIR / name
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path.name}")

def add_source(fig, text="Source: Author's calculations."):
    fig.text(0.02, 0.01, text, fontsize=8, color=COLORS['mid_gray'],
             fontstyle='italic', transform=fig.transFigure)
