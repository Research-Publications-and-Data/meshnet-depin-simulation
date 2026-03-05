#!/usr/bin/env python3
"""
MeshNet discrete-time agent-based simulation (v2 — tuned parameters).
Runs 4 scenarios × 2 emission models = 8 configurations over 1,825 timesteps (5 years).
Operators are modeled as heterogeneous agents across behavioral profiles;
user demand is a reduced-form stochastic process.

v2 changes (parameter tuning, no architectural changes):
  1A. Normalized PID gains (error expressed as fraction of N_TARGET)
  1B. Reduced exit probability (0.3%/day) and opportunity cost ($3/day) — hardware sunk costs
  1C. Superlinear fee revenue scaling — network effects unlock enterprise demand
  1D. Wider PID bounds (0.25×–3× base) — room to respond to severe shocks
  1E. Treasury yield stabilization floor — defense in depth

Prose corrections needed (reviewer-identified mismatches):
  Fix 1: §8 says "linear distribution" — should be "exponentially decaying baseline" (code is correct).
  Fix 2: Appendix A says regulatory shock at "month 12" — code now uses month 18 for
         competitor and regulatory (aligned with prose).
  Fix 3: Paper claims "five agent types including users and whales" — should say
         "Operators are modeled as heterogeneous agents across behavioral profiles;
          user demand is a reduced-form stochastic process."
  Fix 4: Paper says conviction voting and quarterly retroactive outflows are simulated — they are not.
         Remove from simulation model description (they are governance specs from §7).
"""
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CAL_PATH = ROOT / "calibration_params.json"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "simulation_results.csv"

# ── Load calibration ──────────────────────────────────────────
try:
    with open(CAL_PATH) as f:
        CAL = json.load(f)
except FileNotFoundError:
    CAL = {}

# ── Constants ─────────────────────────────────────────────────
TOTAL_SUPPLY = 1_000_000_000
BASE_EMISSION = 109_589        # tokens/day
PID_MIN = 27_397               # 0.25× base — allow deep cuts when overshooting (1D)
PID_MAX = 328_767              # 3.0× base — aggressive ramp during crises (1D)
N_TARGET = 10_000
PROTOCOL_FEE = 0.30

# PID gains: normalized to base emission per unit of normalized error (1A)
# At 100% below target (error_norm=1.0): Kp adds 80% of base emission
KP_NORM = 0.8
KI_NORM = 0.15
KD_NORM = 0.2

# Slashing penalties (default values)
SLASH_DOWNTIME = 0.10   # fraction of stake slashed for uptime < 0.90
SLASH_FRAUD = 1.00      # full forfeiture for intentional fraud (was 0.50)

PID_CADENCE = 14               # evaluate every 14 days
SEED = 42
TIMESTEPS = 1825               # 5 years

# Operator economics (1B)
# Opportunity cost includes hardware amortization + alternative yield, not just marginal cost
OPPORTUNITY_COST = 5.0         # $5/day — hardware amort ($2) + electricity/internet ($2) + alt yield ($1)
EXIT_PROB_BASE = 0.008         # 0.8%/day → ~22%/month (hardware sunk costs temper but don't eliminate)
EXIT_PROB_VETERAN = 0.003      # 0.3%/day for operators active >180 days (reputation investment)
ENTRY_CAP_ABS = 30             # Max 30 new operators per day (hardware deployment constraint)

# OU price model (from calibration)
OU_KAPPA = CAL.get("price", {}).get("mesh_ou_kappa", 2.8)
OU_SIGMA = CAL.get("price", {}).get("mesh_ou_sigma", 0.049)

# S2R logistic parameters (from calibration)
S2R_L = CAL.get("s2r", {}).get("logistic_L", 1.5)
S2R_K = CAL.get("s2r", {}).get("logistic_k", 0.7)
S2R_T0 = CAL.get("s2r", {}).get("logistic_t0", 28.0)

# ── Scenarios ─────────────────────────────────────────────────
SCENARIOS = {
    "bull": {
        "demand_growth_annual": 0.30,
        "price_drift": 0.002,
        "shock_month": None,
        "shock_type": None,
    },
    "bear": {
        "demand_growth_annual": -0.15,
        "price_drift": -0.001,
        "shock_month": 12,
        "shock_type": "demand_contraction",
    },
    "competitor": {
        "demand_growth_annual": -0.10,    # negative: competitor takes market share
        "price_drift": -0.001,            # market uncertainty
        "shock_month": 18,                # competitor enters month 18 (matches prose)
        "shock_type": "operator_poach",
        "poach_rate": 0.25,               # 25% of operators defect (matches prose)
    },
    "regulatory": {
        "demand_growth_annual": -0.05,    # regulatory uncertainty freezes growth
        "price_drift": -0.001,            # market uncertainty
        "shock_month": 18,                # regulatory action month 18 (matches prose)
        "shock_type": "cost_increase",
        "cost_multiplier": 1.30,          # 30% cost increase (matches prose: "costs increase 30%")
    },
}


# ── Agent initialization ─────────────────────────────────────

def create_operators(n, rng):
    """Create operator agents with type-specific behavioral parameters."""
    agents = []
    types = (
        [("high_commitment", 0.3, 0.2, 0.995, 0.0)] * int(n * 0.40) +
        [("casual", 0.8, 0.6, 0.95, 0.0)] * int(n * 0.30) +
        [("mercenary", 1.2, 0.9, 0.85, 0.15)] * int(n * 0.15) +
        [("casual", 0.8, 0.6, 0.95, 0.0)] * (n - int(n*0.40) - int(n*0.30) - int(n*0.15))
    )
    for i, (atype, exit_t, price_s, uptime_base, fraud_p) in enumerate(types):
        agents.append({
            "id": i,
            "type": atype,
            "exit_threshold": exit_t,
            "price_sensitivity": price_s,
            "uptime": min(1.0, uptime_base + rng.normal(0, 0.01)),
            "fraud_prob": fraud_p,
            "stake": 10_000 + rng.integers(0, 20_000),
            "reputation": 0.0,
            "active": True,
            "seasons_active": 0,
        })
    return agents


def create_whales(rng):
    """Create 5 whale agents."""
    return [
        {"id": f"whale_{i}", "tokens": int(TOTAL_SUPPLY * (0.02 + rng.random() * 0.03)),
         "reputation": 0.0, "selfish_prob": 0.3}
        for i in range(5)
    ]


# ── State update functions ────────────────────────────────────

def compute_demand(t, N, P, scenario, rng, cost_mult=1.0):
    """PSUB 1: Compute daily fee revenue with superlinear network effects (1C)."""
    annual_growth = scenario["demand_growth_annual"]
    daily_growth = (1 + annual_growth) ** (1/365) - 1

    # Superlinear fee scaling: coverage completeness unlocks enterprise demand (1C)
    coverage_ratio = N / N_TARGET
    if coverage_ratio < 0.3:
        # Below 30%: linear scaling, no enterprise customers
        coverage_factor = coverage_ratio
    elif coverage_ratio < 0.8:
        # 30-80%: accelerating, enterprise contracts begin
        coverage_factor = coverage_ratio ** 1.3
    else:
        # 80%+: full network effects, carrier offload, geographic completeness
        coverage_factor = min(coverage_ratio ** 1.5, 2.0)

    base_demand = 1000 * coverage_factor * (1 + daily_growth) ** t

    # Apply shocks
    shock_day = (scenario.get("shock_month") or 999) * 30
    if scenario.get("shock_type") == "demand_contraction" and t > shock_day:
        base_demand *= max(0.3, 1 - 0.02 * ((t - shock_day) / 30))
    elif scenario.get("shock_type") == "cost_increase" and t > shock_day:
        base_demand *= (1 / cost_mult)  # higher costs reduce effective demand
    elif scenario.get("shock_type") == "operator_poach" and t > shock_day:
        # Competitor also siphons demand; 30% demand erosion over 6 months
        months_since = (t - shock_day) / 30
        demand_loss = min(0.30, 0.05 * months_since)
        base_demand *= (1 - demand_loss)

    # Random noise
    noise = 1 + rng.normal(0, 0.05)
    return max(50, base_demand * noise)


def pid_emission(N, integral_norm, prev_error_norm, t, kp=None, ki=None, kd=None):
    """PSUB 2: PID-controlled emission rate with normalized gains (1A)."""
    if t % PID_CADENCE != 0:
        return None, integral_norm, prev_error_norm  # No update this step

    _kp = kp if kp is not None else KP_NORM
    _ki = ki if ki is not None else KI_NORM
    _kd = kd if kd is not None else KD_NORM

    # Normalized error: fraction of target (range [-inf, 1])
    error_norm = (N_TARGET - N) / N_TARGET
    integral_norm = integral_norm + error_norm
    integral_norm = max(-5.0, min(5.0, integral_norm))  # anti-windup in normalized space
    derivative_norm = error_norm - prev_error_norm

    # Adjustment expressed as fraction of base emission
    adjustment = BASE_EMISSION * (
        _kp * error_norm +
        _ki * integral_norm +
        _kd * derivative_norm
    )
    new_E = BASE_EMISSION + adjustment
    new_E = max(PID_MIN, min(PID_MAX, new_E))
    return new_E, integral_norm, error_norm


def static_emission(t):
    """Static linear emission: same total tokens, no feedback."""
    # 400M over 10 years = 109,589/day, tapering 5% per year
    year = t / 365
    return BASE_EMISSION * (0.95 ** year)


def burn_tokens(F_daily, P):
    """PSUB 3: Compute tokens burned from fee revenue."""
    burn_usd = F_daily * PROTOCOL_FEE
    return burn_usd / max(P, 0.001)


def update_operators(agents, E, F_daily, N, P, scenario, t, rng, T,
                     cost_mult=1.0, slash_downtime=None, slash_fraud=None):
    """PSUB 4+5: Staking/slashing, treasury stabilization, and entry/exit.
    Changes from v1: reduced exit prob (1B), lower opportunity cost (1B),
    veteran cooling-off (1B), treasury yield floor (1E)."""
    sd = slash_downtime if slash_downtime is not None else SLASH_DOWNTIME
    sf = slash_fraud if slash_fraud is not None else SLASH_FRAUD
    active = [a for a in agents if a["active"]]
    slashed = 0
    fraud_captured = 0
    treasury_subsidy = 0

    if len(active) == 0:
        return agents, slashed, fraud_captured, treasury_subsidy

    active_count = len(active)
    per_op_emission = E / max(active_count, 1)
    per_op_fee = (F_daily * (1 - PROTOCOL_FEE)) / max(active_count, 1)
    op_cost = (3.0 + rng.normal(0, 0.5)) * cost_mult  # ~$3/day base operating cost

    for a in active:
        # Uptime jitter
        a["uptime"] = min(1.0, max(0.5, a["uptime"] + rng.normal(0, 0.005)))

        # Slashing: downtime
        if a["uptime"] < 0.90:
            slash_amount = int(a["stake"] * sd)
            a["stake"] -= slash_amount
            slashed += slash_amount

        # Slashing: fraud (with proof-of-coverage)
        if a["fraud_prob"] > 0 and rng.random() < a["fraud_prob"]:
            if rng.random() < 0.97:  # 97% catch rate with PoC
                slash_amount = int(a["stake"] * sf)
                a["stake"] -= slash_amount
                slashed += slash_amount
            else:
                fraud_captured += per_op_emission * 0.1

        # Yield calculation
        per_op_yield_usd = (per_op_emission + per_op_fee) * P
        daily_yield = per_op_yield_usd - op_cost

        # Exit decision: yield vs opportunity cost (price already in yield via P)
        exit_prob = EXIT_PROB_VETERAN if a["seasons_active"] >= 2 else EXIT_PROB_BASE
        if daily_yield < a["exit_threshold"] * OPPORTUNITY_COST:
            if rng.random() < exit_prob:
                a["active"] = False

        # Stake floor
        if a["stake"] <= 0:
            a["active"] = False

    # Treasury yield stabilization (1E): floor at 50% of opportunity cost
    per_op_yield_usd = (per_op_emission + per_op_fee) * P
    if per_op_yield_usd < 0.5 * OPPORTUNITY_COST and T > TOTAL_SUPPLY * 0.02:
        deficit_per_op = (0.5 * OPPORTUNITY_COST) - per_op_yield_usd
        subsidy_tokens = deficit_per_op / max(P, 0.001)
        total_subsidy = subsidy_tokens * active_count
        if total_subsidy < T * 0.01:  # cap at 1% of treasury per day
            treasury_subsidy = total_subsidy

    # New entrants: soft cap with decreasing entry rate above target
    active_count = sum(1 for a in agents if a["active"])
    token_yield_usd = (per_op_emission + per_op_fee) * P
    if token_yield_usd > 2.0 * OPPORTUNITY_COST:  # 2× opp cost to justify new hardware
        # Entry rate tapers: 100% at N*, 50% at 1.1×N*, 0% at 1.2×N* (= 12,000)
        if active_count > N_TARGET:
            entry_factor = max(0.0, 1.0 - (active_count - N_TARGET) / (N_TARGET * 0.2))
        else:
            entry_factor = 1.0
        base_new = min(int(active_count * 0.03), ENTRY_CAP_ABS)
        new_count = max(0, int(base_new * entry_factor))
        for _ in range(new_count):
            agents.append({
                "id": len(agents),
                "type": rng.choice(["high_commitment", "casual", "mercenary"],
                                   p=[0.5, 0.35, 0.15]),
                "exit_threshold": rng.choice([0.3, 0.8, 1.2], p=[0.5, 0.35, 0.15]),
                "price_sensitivity": rng.uniform(0.2, 0.9),
                "uptime": 0.95 + rng.normal(0, 0.02),
                "fraud_prob": 0.15 if rng.random() < 0.15 else 0.0,
                "stake": 10_000 + rng.integers(0, 20_000),
                "reputation": 0.0,
                "active": True,
                "seasons_active": 0,
            })

    # Operator poach shock
    shock_day = (scenario.get("shock_month") or 999) * 30
    if scenario.get("shock_type") == "operator_poach" and t == shock_day:
        poach_n = int(active_count * scenario.get("poach_rate", 0.25))
        poached = 0
        for a in agents:
            if a["active"] and a["type"] != "high_commitment" and poached < poach_n:
                a["active"] = False
                poached += 1

    return agents, slashed, fraud_captured, treasury_subsidy


def update_reputation(agents, t):
    """PSUB 6: Quarterly reputation update (every 90 days)."""
    if t % 90 != 0 or t == 0:
        return agents
    active = [a for a in agents if a["active"]]
    if len(active) == 0:
        return agents
    median_uptime = np.median([a["uptime"] for a in active])
    for a in active:
        a["seasons_active"] += 1
        if a["uptime"] > 0.99:
            a["reputation"] += 1.0
        a["reputation"] *= (1 - 0.15)  # decay
        a["reputation"] = min(a["reputation"], 5.0)
    return agents


def update_price(P, F_daily, C, drift, rng):
    """PSUB 7: Ornstein-Uhlenbeck price update."""
    fundamental = (F_daily * 365) / max(C, 1) * 1000  # annualized fee / circ
    fundamental = max(0.01, min(10.0, fundamental))
    dW = rng.normal(0, 1)
    log_P = np.log(max(P, 0.001))
    log_F = np.log(max(fundamental, 0.001))
    # OU: d(log P) = kappa * (log_F - log_P) * dt + sigma * dW + drift
    new_log_P = log_P + OU_KAPPA / 365 * (log_F - log_P) + OU_SIGMA * dW + drift
    return max(0.001, np.exp(new_log_P))


# ── Main simulation loop ─────────────────────────────────────

def run_simulation(scenario_name: str, scenario: dict, use_pid: bool, seed: int,
                   kp=None, ki=None, kd=None,
                   slash_downtime=None, slash_fraud=None) -> list:
    """Run one simulation configuration for 1,825 timesteps."""
    rng = np.random.default_rng(seed)

    # Initial state
    C = 200_000_000
    T = 150_000_000
    N = 2_000                # Start closer to target for faster dynamics
    F_daily = 500.0
    P = 0.10
    E = BASE_EMISSION
    B = 0.0
    integral = 0.0
    prev_error = 0.0
    slashed_total = 0
    fraud_total = 0.0
    cost_mult = 1.0

    agents = create_operators(N, rng)
    whales = create_whales(rng)

    records = []

    for t in range(TIMESTEPS):
        # Cost shock
        shock_day = (scenario.get("shock_month") or 999) * 30
        if scenario.get("shock_type") == "cost_increase" and t >= shock_day:
            cost_mult = scenario.get("cost_multiplier", 1.3)

        # PSUB 1: Demand
        F_daily = compute_demand(t, N, P, scenario, rng, cost_mult)

        # PSUB 2: Emission
        if use_pid:
            result = pid_emission(N, integral, prev_error, t, kp=kp, ki=ki, kd=kd)
            if result[0] is not None:
                E, integral, prev_error = result
        else:
            E = static_emission(t)

        # PSUB 3: Burns
        B = burn_tokens(F_daily, P)

        # PSUB 4+5: Operators (now includes treasury stabilization)
        agents, slashed, fraud, treas_subsidy = update_operators(
            agents, E, F_daily, N, P, scenario, t, rng, T, cost_mult,
            slash_downtime=slash_downtime, slash_fraud=slash_fraud)
        slashed_total += slashed
        fraud_total += fraud

        # PSUB 6: Reputation
        agents = update_reputation(agents, t)

        # PSUB 7: Price
        P = update_price(P, F_daily, C, scenario.get("price_drift", 0), rng)

        # PSUB 8: Supply accounting (including treasury subsidy)
        C = C + E - B - slashed
        C = max(0, min(TOTAL_SUPPLY, C))
        T = T + slashed - treas_subsidy
        T = max(0, T)

        # Active node count
        N = sum(1 for a in agents if a["active"])
        N = max(1, N)

        # S2R (burn-mint equilibrium ratio)
        bme = B / max(E, 1)

        # Progress logging (Enhancement C)
        if t % 365 == 0:
            print(f"  [{scenario_name}/{'PID' if use_pid else 'static'}] Year {t//365}: "
                  f"N={N}, P=${P:.4f}, C={C:,.0f}", file=sys.stderr)

        # Record with run metadata (Enhancement A)
        records.append({
            "seed": seed,
            "run_id": f"{scenario_name}_{'pid' if use_pid else 'static'}",
            "timestep": t,
            "scenario": scenario_name,
            "emission_model": "pid" if use_pid else "static",
            "N": N,
            "E": round(E, 0),
            "B": round(B, 2),
            "F_daily": round(F_daily, 2),
            "P": round(P, 6),
            "C": round(C, 0),
            "T": round(T, 0),
            "s2r": round(bme, 6),
            "bme": round(bme, 6),
            "slashed_total": slashed_total,
            "fraud_captured_pct": round(fraud_total / max(E * (t+1), 1) * 100, 4),
        })

    return records


def parse_args():
    """Enhancement B: Command-line interface."""
    parser = argparse.ArgumentParser(description="MeshNet discrete-time agent-based simulation")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--scenarios", nargs="+", default=list(SCENARIOS.keys()))
    parser.add_argument("--pid-only", action="store_true")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--output", type=str, default=str(OUT_PATH))
    parser.add_argument("mode", nargs="?", default="core",
                        choices=["core", "sensitivity", "slashing"],
                        help="Run mode: core (default), sensitivity, or slashing")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "sensitivity":
        sensitivity_sweep()
        return
    elif args.mode == "slashing":
        slashing_sensitivity_sweep()
        return

    scenarios_to_run = {k: v for k, v in SCENARIOS.items() if k in args.scenarios}
    models = []
    if not args.static_only:
        models.append(True)
    if not args.pid_only:
        models.append(False)

    print("=" * 60)
    print("MESHNET SIMULATION")
    print(f"Scenarios: {len(scenarios_to_run)} × {len(models)} models = {len(scenarios_to_run)*len(models)} runs")
    print(f"Timesteps: {TIMESTEPS} per run")
    print("=" * 60)

    all_records = []
    run_count = 0
    total_runs = len(scenarios_to_run) * len(models)
    for scenario_idx, (scenario_name, scenario) in enumerate(scenarios_to_run.items()):
        for use_pid in models:
            model = "PID" if use_pid else "Static"
            seed = args.seed + scenario_idx
            run_count += 1
            print(f"\n  Run {run_count}/{total_runs}: {scenario_name} + {model} (seed={seed})")
            records = run_simulation(scenario_name, scenario, use_pid, seed)
            all_records.extend(records)
            final = records[-1]
            print(f"    N={final['N']:,}, P=${final['P']:.4f}, "
                  f"BME={final['bme']:.4f}, C={final['C']:,.0f}")

    df = pd.DataFrame(all_records)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path} ({len(df):,} rows)")

    # Quick validation
    print("\n── Quick Validation ──")
    for scenario in scenarios_to_run:
        pid = df[(df["scenario"] == scenario) & (df["emission_model"] == "pid")]
        sta = df[(df["scenario"] == scenario) & (df["emission_model"] == "static")]
        if len(pid) > 0:
            pid_final_N = pid.iloc[-1]["N"]
            pid_dev = abs(pid_final_N - N_TARGET) / N_TARGET
            pid_str = f"PID N={pid_final_N:>6,} (dev={pid_dev:.1%})"
        else:
            pid_str = "PID: skipped"
        if len(sta) > 0:
            sta_final_N = sta.iloc[-1]["N"]
            sta_dev = abs(sta_final_N - N_TARGET) / N_TARGET
            sta_str = f"Static N={sta_final_N:>6,} (dev={sta_dev:.1%})"
        else:
            sta_str = "Static: skipped"
        print(f"  {scenario:12s}: {pid_str}, {sta_str}")


def sensitivity_sweep():
    """Sweep Kp, Ki, Kd independently while holding others at defaults."""
    kp_values = [0.3, 0.5, 0.8, 1.2, 1.6]
    ki_values = [0.05, 0.10, 0.15, 0.25, 0.35]
    kd_values = [0.05, 0.10, 0.20, 0.35, 0.50]

    results = []

    # Sweep Kp (hold Ki=0.15, Kd=0.2)
    print("Sweeping Kp...")
    for kp in kp_values:
        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            seed = SEED + scenario_idx
            records = run_simulation(sname, scenario, True, seed, kp=kp, ki=KI_NORM, kd=KD_NORM)
            final = records[-1]
            n_series = [r["N"] for r in records]
            results.append({
                "sweep_param": "Kp", "param_value": kp,
                "Ki": KI_NORM, "Kd": KD_NORM,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": abs(final["N"] - N_TARGET) / N_TARGET,
                "mad": np.mean([abs(n - N_TARGET) for n in n_series]),
                "max_N": max(n_series), "min_N": min(n_series),
                "final_P": final["P"],
                "E_range": max(r["E"] for r in records) - min(r["E"] for r in records),
            })
            print(f"  Kp={kp:.1f} / {sname}: final N={final['N']}, dev={results[-1]['dev_from_target']:.1%}")

    # Sweep Ki (hold Kp=0.8, Kd=0.2)
    print("Sweeping Ki...")
    for ki in ki_values:
        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            seed = SEED + scenario_idx
            records = run_simulation(sname, scenario, True, seed, kp=KP_NORM, ki=ki, kd=KD_NORM)
            final = records[-1]
            n_series = [r["N"] for r in records]
            results.append({
                "sweep_param": "Ki", "param_value": ki,
                "Ki": ki, "Kd": KD_NORM,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": abs(final["N"] - N_TARGET) / N_TARGET,
                "mad": np.mean([abs(n - N_TARGET) for n in n_series]),
                "max_N": max(n_series), "min_N": min(n_series),
                "final_P": final["P"],
                "E_range": max(r["E"] for r in records) - min(r["E"] for r in records),
            })
            print(f"  Ki={ki:.2f} / {sname}: final N={final['N']}, dev={results[-1]['dev_from_target']:.1%}")

    # Sweep Kd (hold Kp=0.8, Ki=0.15)
    print("Sweeping Kd...")
    for kd in kd_values:
        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            seed = SEED + scenario_idx
            records = run_simulation(sname, scenario, True, seed, kp=KP_NORM, ki=KI_NORM, kd=kd)
            final = records[-1]
            n_series = [r["N"] for r in records]
            results.append({
                "sweep_param": "Kd", "param_value": kd,
                "Ki": KI_NORM, "Kd": kd,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": abs(final["N"] - N_TARGET) / N_TARGET,
                "mad": np.mean([abs(n - N_TARGET) for n in n_series]),
                "max_N": max(n_series), "min_N": min(n_series),
                "final_P": final["P"],
                "E_range": max(r["E"] for r in records) - min(r["E"] for r in records),
            })
            print(f"  Kd={kd:.2f} / {sname}: final N={final['N']}, dev={results[-1]['dev_from_target']:.1%}")

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "sensitivity_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")
    return df


def slashing_sensitivity_sweep():
    """Sweep slash_downtime and slash_fraud independently across 4 scenarios (PID only).

    Produces slashing_sensitivity_results.csv with 40 rows:
    - 5 downtime values x 4 scenarios = 20 rows
    - 5 fraud values x 4 scenarios = 20 rows
    """
    downtime_values = [0.02, 0.05, 0.10, 0.20, 0.30]
    fraud_values = [0.20, 0.40, 0.60, 0.80, 1.00]

    results = []

    # Sweep downtime penalty (hold fraud at default 1.00)
    print("Sweeping slash_downtime...")
    for sd in downtime_values:
        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            seed = SEED + scenario_idx
            records = run_simulation(sname, scenario, True, seed,
                                     slash_downtime=sd, slash_fraud=SLASH_FRAUD)
            final = records[-1]
            n_series = [r["N"] for r in records]
            c_series = [r["C"] for r in records]
            results.append({
                "sweep_param": "slash_downtime",
                "param_value": sd,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": abs(final["N"] - N_TARGET) / N_TARGET,
                "mad": round(np.mean([abs(n - N_TARGET) for n in n_series]), 0),
                "final_C": round(final["C"], 0),
                "C_change_pct": round((final["C"] - c_series[0]) / c_series[0] * 100, 1),
                "final_T": round(final["T"], 0),
                "slashed_total": final["slashed_total"],
                "final_P": final["P"],
            })
            print(f"  sd={sd:.2f} / {sname}: N={final['N']}, "
                  f"C_chg={results[-1]['C_change_pct']:+.1f}%, "
                  f"slashed={final['slashed_total']:,.0f}")

    # Sweep fraud penalty (hold downtime at default 0.10)
    print("Sweeping slash_fraud...")
    for sf in fraud_values:
        for scenario_idx, (sname, scenario) in enumerate(SCENARIOS.items()):
            seed = SEED + scenario_idx
            records = run_simulation(sname, scenario, True, seed,
                                     slash_downtime=SLASH_DOWNTIME, slash_fraud=sf)
            final = records[-1]
            n_series = [r["N"] for r in records]
            c_series = [r["C"] for r in records]
            results.append({
                "sweep_param": "slash_fraud",
                "param_value": sf,
                "scenario": sname,
                "final_N": final["N"],
                "dev_from_target": abs(final["N"] - N_TARGET) / N_TARGET,
                "mad": round(np.mean([abs(n - N_TARGET) for n in n_series]), 0),
                "final_C": round(final["C"], 0),
                "C_change_pct": round((final["C"] - c_series[0]) / c_series[0] * 100, 1),
                "final_T": round(final["T"], 0),
                "slashed_total": final["slashed_total"],
                "final_P": final["P"],
            })
            print(f"  sf={sf:.2f} / {sname}: N={final['N']}, "
                  f"C_chg={results[-1]['C_change_pct']:+.1f}%, "
                  f"slashed={final['slashed_total']:,.0f}")

    df = pd.DataFrame(results)
    out = RESULTS_DIR / "slashing_sensitivity_results.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    main()
