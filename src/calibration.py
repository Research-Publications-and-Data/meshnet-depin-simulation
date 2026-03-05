#!/usr/bin/env python3
"""
Calibration: Derive MeshNet simulation parameters from real Helium data.
Outputs calibration_params.json used by meshnet_model.py and generate_exhibits.py.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

import data_loader

OUT = Path(__file__).resolve().parent.parent / "calibration_params.json"


def calibrate_s2r(s2r_df: pd.DataFrame) -> dict:
    """Derive burn-mint trajectory parameters from Helium S2R."""
    s2r = s2r_df["s2r_clean"].values
    months = np.arange(len(s2r))

    # Key empirical milestones
    milestones = {
        "month_1_s2r": round(float(s2r[0]), 4),
        "month_6_s2r": round(float(s2r[min(5, len(s2r)-1)]), 4),
        "month_12_s2r": round(float(s2r[min(11, len(s2r)-1)]), 4),
        "month_24_s2r": round(float(s2r[min(23, len(s2r)-1)]), 4),
        "month_34_s2r": round(float(s2r[-1]), 4),
    }

    # Find first month where S2R >= 1.0
    parity_idx = np.where(s2r >= 1.0)[0]
    milestones["first_parity_month"] = int(parity_idx[0]) + 1 if len(parity_idx) > 0 else None

    # Fit logistic growth: S2R(t) = L / (1 + exp(-k*(t - t0)))
    # Use median monthly S2R to reduce spike sensitivity
    s2r_smooth = s2r_df["s2r_3m_rolling"].dropna().values
    months_smooth = months[:len(s2r_smooth)]
    if len(s2r_smooth) > 5:
        from scipy.optimize import curve_fit
        def logistic(t, L, k, t0):
            return L / (1 + np.exp(-k * (t - t0)))
        try:
            popt, _ = curve_fit(logistic, months_smooth, s2r_smooth,
                                p0=[2.0, 0.15, 25], maxfev=5000,
                                bounds=([0.5, 0.01, 10], [5.0, 1.0, 50]))
            milestones["logistic_L"] = round(float(popt[0]), 4)
            milestones["logistic_k"] = round(float(popt[1]), 4)
            milestones["logistic_t0"] = round(float(popt[2]), 2)
        except Exception:
            milestones["logistic_L"] = 2.0
            milestones["logistic_k"] = 0.15
            milestones["logistic_t0"] = 28.0

    return milestones


def calibrate_emission(issuance_df: pd.DataFrame, current: dict) -> dict:
    """Derive emission schedule parameters from Helium issuance."""
    weekly_issued = issuance_df["hnt_issued"].values
    total_supply = current.get("total_supply", 223_000_000)
    circulating = current.get("circulating_supply", 186_000_000)

    # Weekly stats
    mean_weekly = float(np.mean(weekly_issued))
    std_weekly = float(np.std(weekly_issued))
    mean_daily = mean_weekly / 7

    # Detect halving: compare first half vs second half
    mid = len(weekly_issued) // 2
    ratio = float(np.mean(weekly_issued[mid:]) / max(np.mean(weekly_issued[:mid]), 1))

    return {
        "helium_total_supply": total_supply,
        "helium_circulating": circulating,
        "helium_pct_issued": round(circulating / total_supply, 4),
        "helium_mean_daily_issuance": round(mean_daily, 0),
        "helium_issuance_std_weekly": round(std_weekly, 0),
        "helium_half2_vs_half1_ratio": round(ratio, 3),
        # MeshNet mapped parameters
        "mesh_total_supply": 1_000_000_000,
        "mesh_operator_pool": 400_000_000,
        "mesh_base_emission_daily": 109_589,
        "mesh_pid_min_daily": 54_795,
        "mesh_pid_max_daily": 219_178,
    }


def calibrate_price(price_df: pd.DataFrame) -> dict:
    """Derive Ornstein-Uhlenbeck parameters from HNT price data."""
    prices = price_df["hnt_price_usd"].values
    log_prices = np.log(prices[prices > 0])
    log_returns = np.diff(log_prices)

    # Annualized volatility
    daily_vol = float(np.std(log_returns))
    annual_vol = daily_vol * np.sqrt(365)

    # Autocorrelation (lag-1) — negative = mean-reverting
    autocorr = float(np.corrcoef(log_returns[:-1], log_returns[1:])[0, 1])

    # OU mean-reversion speed: κ ≈ -ln(autocorr) per day
    kappa = -np.log(max(abs(autocorr), 0.01))

    return {
        "hnt_mean_price": round(float(np.mean(prices)), 4),
        "hnt_daily_vol": round(daily_vol, 6),
        "hnt_annual_vol": round(annual_vol, 4),
        "hnt_autocorr_lag1": round(autocorr, 4),
        "ou_kappa": round(float(kappa), 4),
        "ou_sigma": round(daily_vol, 6),
        # MeshNet mapped
        "mesh_initial_price": 0.10,
        "mesh_ou_kappa": round(float(kappa) * 0.8, 4),  # slightly slower reversion
        "mesh_ou_sigma": round(daily_vol * 0.9, 6),  # slightly lower vol
    }


def calibrate_governance(gov_df: pd.DataFrame) -> dict:
    """Derive governance concentration benchmarks (DeFi + DePIN)."""
    hhi_vals = gov_df["hhi"].dropna().values
    gini_vals = gov_df["gini"].dropna().values

    benchmarks = {
        "real_hhi_min": round(float(np.min(hhi_vals)), 4),
        "real_hhi_max": round(float(np.max(hhi_vals)), 4),
        "real_hhi_mean": round(float(np.mean(hhi_vals)), 4),
        "real_gini_min": round(float(np.min(gini_vals)), 4),
        "real_gini_max": round(float(np.max(gini_vals)), 4),
        "real_gini_mean": round(float(np.mean(gini_vals)), 4),
        "protocols": [],
    }
    for _, row in gov_df.iterrows():
        entry = {
            "name": row["protocol"],
            "hhi": round(float(row["hhi"]), 4),
            "gini": round(float(row["gini"]), 4),
            "top1": round(float(row["top1_share"]), 4) if pd.notna(row.get("top1_share")) else None,
        }
        if "category" in row and pd.notna(row.get("category")):
            entry["category"] = row["category"]
        benchmarks["protocols"].append(entry)

    # Category-level summaries
    if "category" in gov_df.columns:
        for cat in ["defi", "depin"]:
            sub = gov_df[gov_df["category"] == cat]
            if len(sub) > 0:
                sub_hhi = sub["hhi"].dropna()
                sub_gini = sub["gini"].dropna()
                benchmarks[f"{cat}_n"] = len(sub_hhi)
                benchmarks[f"{cat}_hhi_min"] = round(float(sub_hhi.min()), 4)
                benchmarks[f"{cat}_hhi_max"] = round(float(sub_hhi.max()), 4)
                benchmarks[f"{cat}_hhi_mean"] = round(float(sub_hhi.mean()), 4)
                benchmarks[f"{cat}_gini_mean"] = round(float(sub_gini.mean()), 4)

    # MeshNet target: reputation-weighted governance should compress
    # Use DeFi min as baseline (DeFi represents mature governance)
    defi_hhi = gov_df[gov_df.get("category", "defi") == "defi"]["hhi"].dropna() if "category" in gov_df.columns else gov_df["hhi"].dropna()
    defi_gini = gov_df[gov_df.get("category", "defi") == "defi"]["gini"].dropna() if "category" in gov_df.columns else gov_df["gini"].dropna()
    if len(defi_hhi) > 0:
        benchmarks["mesh_target_gini"] = round(float(defi_gini.min()) * 0.85, 4)
        benchmarks["mesh_target_hhi"] = round(float(defi_hhi.min()) * 0.6, 4)
    else:
        benchmarks["mesh_target_gini"] = round(float(np.min(gini_vals)) * 0.85, 4)
        benchmarks["mesh_target_hhi"] = round(float(np.min(hhi_vals)) * 0.6, 4)

    return benchmarks


def main():
    print("=" * 60)
    print("MESHNET CALIBRATION FROM HELIUM DATA")
    print("=" * 60)

    data = data_loader.load_all()

    params = {}

    # 1. S2R calibration
    print("\n1. Burn-Mint Ratio (S2R):")
    if data["s2r_cleaned"] is not None:
        params["s2r"] = calibrate_s2r(data["s2r_cleaned"])
        for k, v in params["s2r"].items():
            print(f"   {k}: {v}")
    else:
        params["s2r"] = {"logistic_L": 2.0, "logistic_k": 0.15, "logistic_t0": 28.0}
        print("   Using fallback parameters")

    # 2. Emission calibration
    print("\n2. Emission Rate:")
    if data["weekly_issuance"] is not None and data["hnt_current"] is not None:
        params["emission"] = calibrate_emission(data["weekly_issuance"], data["hnt_current"])
        for k, v in params["emission"].items():
            print(f"   {k}: {v}")

    # 3. Price dynamics
    print("\n3. Price Dynamics:")
    if data["hnt_price"] is not None:
        params["price"] = calibrate_price(data["hnt_price"])
        for k, v in params["price"].items():
            print(f"   {k}: {v}")

    # 4. Governance benchmarks
    print("\n4. Governance Concentration:")
    if data["governance"] is not None:
        params["governance"] = calibrate_governance(data["governance"])
        g = params["governance"]
        print(f"   Overall HHI range: {g['real_hhi_min']:.4f} – {g['real_hhi_max']:.4f}")
        print(f"   Overall Gini range: {g['real_gini_min']:.4f} – {g['real_gini_max']:.4f}")
        if "defi_n" in g:
            print(f"   DeFi  (N={g['defi_n']}):  HHI {g['defi_hhi_min']:.4f}–{g['defi_hhi_max']:.4f} (mean {g['defi_hhi_mean']:.4f})")
        if "depin_n" in g:
            print(f"   DePIN (N={g['depin_n']}): HHI {g['depin_hhi_min']:.4f}–{g['depin_hhi_max']:.4f} (mean {g['depin_hhi_mean']:.4f})")
        print(f"   MeshNet target Gini: {g['mesh_target_gini']:.4f}")

    # Save
    with open(OUT, "w") as f:
        json.dump(params, f, indent=2, default=str)
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
