#!/usr/bin/env python3
"""
PID gain sensitivity sweep (60 runs).
Sweeps Kp, Ki, Kd independently while holding others at defaults.
- Kp: [0.3, 0.5, 0.8, 1.0, 1.6] × 4 scenarios = 20
- Ki: [0.05, 0.10, 0.15, 0.25, 0.35] × 4 scenarios = 20
- Kd: [0.05, 0.10, 0.20, 0.35, 0.50] × 4 scenarios = 20
Deduplicating default values gives 56 unique runs (4 shared at defaults).
Output: results/sensitivity_results.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from meshnet_model import sensitivity_sweep

if __name__ == "__main__":
    sensitivity_sweep()
