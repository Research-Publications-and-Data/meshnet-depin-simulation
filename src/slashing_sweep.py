#!/usr/bin/env python3
"""
Slashing parameter sweep (40 runs).
Sweeps slash_downtime and slash_fraud independently across 4 scenarios (PID only).
- Downtime: [0.02, 0.05, 0.10, 0.20, 0.30] × 4 scenarios = 20
- Fraud:    [0.20, 0.40, 0.60, 0.80, 1.00] × 4 scenarios = 20
Output: results/slashing_sensitivity_results.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from meshnet_model import slashing_sensitivity_sweep

if __name__ == "__main__":
    slashing_sensitivity_sweep()
