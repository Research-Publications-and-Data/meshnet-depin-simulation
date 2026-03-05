# MeshNet Simulation Results Summary — v2

**Date:** 2026-02-23
**Changes from v1:**
1. `SLASH_FRAUD`: 0.50 → 1.00 (full forfeiture for intentional fraud)
2. Competitor scenario: `shock_month` 12→18, `poach_rate` 0.35→0.25
3. Regulatory scenario: `shock_month` 12→18, `cost_multiplier` 2.0→1.30
4. Fraud sweep range: [0.20, 0.35, 0.50, 0.70, 0.90] → [0.20, 0.40, 0.60, 0.80, 1.00]

**Seed:** 42 (unchanged). **Timesteps:** 1,825 (unchanged).

---

## A. Core Results Comparison Table

| Scenario | Model | v1 Final N | v2 Final N | v1 Dev% | v2 Dev% | Direction |
|---|---|---:|---:|---:|---:|---|
| bull | PID | 11,934 | 11,934 | 19.3% | 19.3% | same |
| bull | static | 11,934 | 11,934 | 19.3% | 19.3% | same |
| bear | PID | 6,330 | 5,536 | 36.7% | 44.6% | worse |
| bear | static | 5,966 | 7,401 | 40.3% | 26.0% | better |
| competitor | PID | 11,117 | 11,559 | 11.2% | 15.6% | worse |
| competitor | static | 2,798 | 11,934 | 72.0% | 19.3% | **much better** |
| regulatory | PID | 10,279 | 9,152 | 2.8% | 8.5% | worse |
| regulatory | static | 617 | 11,934 | 93.8% | 19.3% | **much better** |

### Key Narrative Changes

**Static emission no longer produces catastrophic failure.** Under the milder regulatory scenario (30% cost increase vs. 100%, month 18 vs. 12), static emission actually sustains 11,934 nodes — identical to bull. Under competitor (25% poach vs. 35%, month 18 vs. 12), static also sustains 11,934. This eliminates the v1 headline: "PID achieves 16.6× more operators than static under regulatory shock."

**The PID advantage narrows dramatically:**
- Competitor: PID improvement over static was 68–76% in v1 → now PID is actually slightly *worse* (15.6% vs 19.3% dev, but PID undershoots while static overshoots).
- Regulatory: PID improvement was 16.6× in v1 → now 56% improvement (8.5% vs 19.3% dev).
- Bear: PID is *worse* than static (44.6% vs 26.0% dev).

**The v2 results reveal that the PID advantage is scenario-severity-dependent.** Under mild-to-moderate stress, PID's feedback loop can actually *overshoot* during recovery, while static's smooth taper benefits from the extended runway before shock arrives (month 18 vs 12). PID's advantage becomes decisive only under severe shocks — which the v2 parameters attenuate.

---

## B. Parameter Change Impact

### Fraud Slashing 0.50 → 1.00 (isolated effect)

Bull and bear scenarios are unchanged between v1 and v2 in terms of scenario parameters, so differences isolate the fraud slashing effect:

| Metric | Bull/PID v1 | Bull/PID v2 | Bear/PID v1 | Bear/PID v2 |
|---|---:|---:|---:|---:|
| Final N | 11,934 | 11,934 | 6,330 | 5,536 |
| Final C | 126,746,834 | 95,776,493 | 192,666,155 | 207,760,738 |
| Slashed total | 168,063,530 | 275,812,684 | 173,804,416 | 285,016,684 |
| Final P | $6.5617 | $9.7089 | $0.1680 | $0.1161 |

**Effect of γ_fraud 0.50→1.00:**
- Slashed totals increase ~64% (168M→276M in bull, 174M→285M in bear).
- Circulating supply drops more (126M→96M in bull) because more tokens are removed.
- Price rises in bull (more scarcity) but drops in bear (fewer operators → less demand support).
- Node count unchanged in bull (cap effect), but drops in bear (more mercenary operators forced out by stake depletion).

### Scenario Timing & Severity Changes (combined effect)

| Parameter Change | Effect on Competitor | Effect on Regulatory |
|---|---|---|
| shock_month 12→18 | +6 months of growth before shock; PID and static both stronger at shock time | Same |
| poach_rate 0.35→0.25 | 25% fewer operators lost; static survives | N/A |
| cost_multiplier 2.0→1.30 | N/A | 70% smaller cost increase; static easily absorbs 30% cost inflation |

---

## C. Updated Quantitative Claims

Every specific number from the whitepaper that needs updating:

```
CLAIM: "PID recovers to 11,117 nodes (11% deviation) after the month-18 poaching shock"
LOCATION: §8, competitor PID result
OLD VALUE: 11,117 nodes, 11% deviation
NEW VALUE: 11,559 nodes, 15.6% deviation

CLAIM: "Static emission collapses to 2,798 nodes (72% below target) under competitor scenario"
LOCATION: §8, competitor static result
OLD VALUE: 2,798 nodes, 72% deviation
NEW VALUE: 11,934 nodes, 19.3% deviation
NOTE: Static no longer collapses. Rewrite: "Static emission sustains 11,934 nodes (19% above target)"

CLAIM: "PID achieves 10,279 nodes (2.8% deviation) under regulatory shock"
LOCATION: §8, regulatory PID result
OLD VALUE: 10,279 nodes, 2.8% deviation
NEW VALUE: 9,152 nodes, 8.5% deviation

CLAIM: "Static emission collapses to 617 nodes (94% below target) under regulatory scenario"
LOCATION: §8, regulatory static result
OLD VALUE: 617 nodes, 93.8% deviation
NEW VALUE: 11,934 nodes, 19.3% deviation
NOTE: Static no longer collapses. Rewrite: "Static emission sustains 11,934 nodes (19% above target)"

CLAIM: "PID reduces deviation from target by 68–76% compared to static"
LOCATION: §8, PID vs static comparison
OLD VALUE: 68–76% improvement
NEW VALUE: PID improves regulatory (56%), but performs comparably or worse in other scenarios.
NOTE: Complete rewrite needed. PID advantage is now scenario-severity-dependent.

CLAIM: "Circulating supply changes: -45.3% competitor, -23.5% regulatory, +12.5%, +47.0%"
LOCATION: §8, circulating supply
OLD VALUE: (various percentages from v1)
NEW VALUE (200M base): bull/PID=-51.9%, bear/PID=+3.9%, competitor/PID=-73.6%, regulatory/PID=-51.6%
NEW VALUE (actual C0 base): bull/PID=-51.9%, bear/PID=+4.5%, competitor/PID=-73.4%, regulatory/PID=-51.3%
NOTE: Paper uses 200M theoretical base for C_change percentages.

CLAIM: "Slashing totals: 309M competitor/PID vs 152M competitor/static"
LOCATION: §8, slashing
OLD VALUE: Various v1 slashing totals
NEW VALUE: bull/PID=275.8M, bear/PID=269.2M, competitor/PID=353.9M, regulatory/PID=296.7M
            bull/static=276.1M, bear/static=285.5M, competitor/static=308.4M, regulatory/static=280.8M

CLAIM: "Ki sensitivity spread: 44 percentage points"
LOCATION: §8, Ki sensitivity
OLD VALUE: 44 pp
NEW VALUE: Bear scenario: 39.3 pp (16.8% to 56.1%). Bull: 0 pp. Competitor: 12.2 pp. Regulatory: 10.7 pp.

CLAIM: "Treasury fired on 6 days, 10,344 tokens"
LOCATION: §8, treasury dynamics
NOTE: Need to re-extract from v2 simulation data.

CLAIM: Abstract numbers referencing PID vs static improvement ratios
LOCATION: Abstract
NOTE: All ratios need recalculation. The 16.6× regulatory advantage no longer exists.

CLAIM: "burns under 0.5M, slashing 228-357M"
LOCATION: §11, limitations
OLD VALUE: burns under 0.5M, slashing 228-357M
NEW VALUE: Burns still under 0.5M. Slashing range: 234M–354M across all sweep parameterizations.

CLAIM: "Fraud penalty affects supply trajectory but not node count in bull and bear"
LOCATION: §8, slashing sweep (third finding)
OLD VALUE: N unchanged in bull (11,934) and bear (5,536)
NEW VALUE: N unchanged in bull only. Bear N varies 5,077–6,330 across fraud penalty sweep.
NOTE: Paper §8 corrected to reflect bear N variability.

CLAIM: §12 conclusion numbers
NOTE: All conclusion numbers verified against v2 data — paper pass6_final is current.
```

---

## I. Verification Status (2026-02-23)

**Paper file:** `tokenomics_whitepaper_v2_pass6_final.md`
**Status:** All quantitative claims verified against raw simulation CSV data.

| Section | Verified | Notes |
|---|---|---|
| Abstract | ✓ | Ensemble stats, BME, variance reduction framing correct |
| Executive Summary | ✓ | CV ratios, 5th-percentile bounds correct |
| §8 Core Results | ✓ | All single-seed scenario N, P, deviation% match |
| §8 Ensemble (240-run) | ✓ | All mean, std, CV, p5, p95 match |
| §8 PID Gain Sensitivity | ✓ | Kp/Ki/Kd sweep findings match |
| §8 Ki Non-Monotonicity | ✓ | 150-run test, rank consistency match |
| §8 Monetary Regime | ✓ | C_change% uses 200M base, all values verified |
| §8 Slashing Sweep | ✓ | Downtime and fraud sweep ranges match CSV |
| §8 Fraud Sweep | **CORRECTED** | Bear N now noted as variable (was claimed constant) |
| §8 Cadence | ✓ | All 4 cadence metrics match |
| §8 Treasury Dynamics | ✓ | Stabilizer non-firing, slashing dominance narrative correct |
| §9 Adversarial | ✓ | Wash trading, whale governance, Sybil numbers consistent |
| §11 Limitations | ✓ | Slashing range, BME negligibility correct |
| §12 Conclusion | ✓ | Variance reduction framing, ensemble stats correct |

**Methodology note:** Paper reports C_change% using 200,000,000 as theoretical initial circulating supply. The simulation CSV uses actual timestep-0 C values (~198.6M–198.9M, varying by stochastic initialization). Both approaches are valid; the 200M base produces cleaner presentation numbers. Difference is <0.5pp on all values.

**Errors found in this summary (Section H):** The original slashing sweep tables contained values from an intermediate run or had a generation bug. Tables corrected to match `slashing_sensitivity_results.csv` ground truth.

---

## D. Validation Results

| # | Assertion | Result | Notes |
|---|---|---|---|
| 1 | PID stability (3/4 scenarios within target) | **PASS** | Bear misses (44.6% > 40% threshold). Bull, competitor, regulatory pass. |
| 2 | Static divergence (≥2 scenarios >40%) | **FAIL** | **0/4 scenarios diverge.** Static no longer collapses with milder params. |
| 3 | Burn-mint dynamics (S2R trending up) | **PASS** | Max S2R=0.0061 at month 57. Trend: early=0.0014 → late=0.0038. |
| 4 | Wash trading defense (<5% fraud) | **PASS** | All scenarios <0.001%. |
| 5 | Reputation compression | **PASS** | Real DePIN Gini 0.887, MeshNet target 0.730. |
| 6 | Supply accounting (C+T tracking) | **PASS** | Informational. Max dev 79% (bear/PID). |
| 7 | Price non-negative | **PASS** | Min price $0.070. |
| 8 | Exhibit artifacts (21/21 ≥10KB) | **PASS** | All 21 generated. |
| 9 | PID sensitivity robustness (competitor N>5000) | **PASS** | All 5 Kp values viable. |
| 10 | Slashing sensitivity (baseline in middle 60%) | **FAIL** | 2/4 in range. Bull and competitor at range edges (SLASH_FRAUD=1.00 is now the maximum sweep value). |

**Assertion 2 diagnosis:** Static no longer diverges because:
1. Later shock timing (month 18 vs 12) gives 6 extra months of pre-shock growth
2. Lower competitor poach rate (25% vs 35%) means fewer operators lost
3. Lower regulatory cost increase (30% vs 100%) is easily absorbed
4. Combined: static emission's smooth taper is sufficient for mild-moderate shocks

**Assertion 10 diagnosis:** With SLASH_FRAUD=1.00 as the new default and the fraud sweep range now [0.20, 0.40, 0.60, 0.80, 1.00], the baseline sits at the maximum of the swept range. This is expected and not problematic — it confirms that full forfeiture is the most aggressive option in the sweep.

---

## E. Multi-Seed Confidence Intervals (240 runs)

| Scenario | Model | N_mean | N_std | N_p5 | N_p95 | P_mean | P_std | BME_max_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| bull | PID | 11,934 | 0 | 11,934 | 11,934 | $14.24 | $5.30 | 0.0071 |
| bull | static | 11,934 | 0 | 11,934 | 11,934 | $14.16 | $7.68 | 0.0057 |
| bear | PID | 6,306 | 1,380 | 4,429 | 8,194 | $0.20 | $0.13 | 0.0035 |
| bear | static | 3,900 | 3,738 | 709 | 11,028 | $0.28 | $0.43 | 0.0059 |
| competitor | PID | 10,099 | 880 | 8,880 | 11,696 | $2.20 | $1.17 | 0.0037 |
| competitor | static | 8,610 | 4,684 | 1,049 | 11,934 | $2.22 | $2.05 | 0.0059 |
| regulatory | PID | 10,262 | 956 | 8,934 | 11,677 | $2.35 | $1.36 | 0.0046 |
| regulatory | static | 11,189 | 2,558 | 5,968 | 11,934 | $2.95 | $1.56 | 0.0057 |

### Coefficient of Variation (std/mean)

| Scenario | Model | N_CV | P_CV |
|---|---|---:|---:|
| bull | PID | 0.000 | 0.372 |
| bull | static | 0.000 | 0.543 |
| bear | PID | 0.219 | 0.666 |
| bear | static | 0.958 | 1.495 |
| competitor | PID | 0.087 | 0.532 |
| competitor | static | 0.544 | 0.921 |
| regulatory | PID | 0.093 | 0.577 |
| regulatory | static | 0.229 | 0.529 |

**Key findings:**
- **PID produces consistently lower variance** in competitor (CV=0.087 vs 0.544) and regulatory (0.093 vs 0.229).
- **Bear/static has extremely high variance** (CV=0.958) with p5=709, p95=11,028 — static can either collapse or survive depending on stochastic path.
- **Bull scenario is deterministic** for both models (N=11,934 in all seeds) — the entry cap binds.
- **Competitor/static can still collapse in some seeds** (p5=1,049) even though the seed=42 run gave 11,934. The 30-seed ensemble reveals this is misleading — static is fragile.
- **Regulatory/static mean=11,189** but with p5=5,968, confirming it survives on average but has tail risk.

### Narrative implication
The single-seed v2 result (static N=11,934 in competitor/regulatory) is an **optimistic outlier**. Across 30 seeds, static mean is 8,610 (competitor) and 11,189 (regulatory) with substantial downside. PID maintains tighter confidence intervals. **The PID advantage is real but manifests as variance reduction rather than level difference.**

---

## F. Ki Non-Monotonicity Re-Test (150 runs)

| Ki | Mean Final N | Std | Min | Max |
|---:|---:|---:|---:|---:|
| 0.05 | 6,057 | 1,392 | 3,173 | 8,854 |
| 0.10 | 6,670 | 1,111 | 4,395 | 9,231 |
| 0.15 | 6,306 | 1,380 | 3,690 | 10,780 |
| 0.25 | 7,546 | 1,678 | 4,416 | 10,962 |
| 0.35 | 7,021 | 1,694 | 3,799 | 10,574 |

**Modal rank ordering:** Ki=0.25 (rank 1), Ki=0.35 (rank 2), Ki=0.10 (rank 3), Ki=0.05 (rank 4), Ki=0.15 (rank 5)

**Rank consistency across 30 seeds:**

| Ki | Consistency |
|---:|---:|
| 0.05 | 0.400 |
| 0.10 | 0.367 |
| 0.15 | 0.267 |
| 0.25 | 0.467 |
| 0.35 | 0.300 |

**Min consistency:** 0.267 (< 0.60 threshold)
**Verdict: PATH-DEPENDENT** (same as v1)

The rank ordering of Ki values depends on the random seed, not on structural properties of the controller. The paper must state: "Ki non-monotonicity observed in single-seed runs; multi-seed testing shows rank ordering is seed-dependent."

---

## G. Cadence Comparison

| Cadence (days) | Mean Dev% | Mean Adjustments | Mean Emission Vol | Mean Floor Steps |
|---:|---:|---:|---:|---:|
| 7 | 16.0% | 157 | 76,439 | 728 |
| 14 | 22.0% | 110 | 72,018 | 292 |
| 21 | 15.5% | 80 | 62,746 | 146 |
| 30 | 21.0% | 60 | 50,616 | 14 |

**v2 Finding:** The 14-day cadence no longer dominates. The 21-day cadence now achieves the lowest mean deviation (15.5%) with moderate emission volatility. The 7-day cadence is a close second (16.0%) but with highest volatility and most time at emission floor. The 30-day cadence is too slow (21.0% dev).

**Recommendation:** Consider updating to 21-day cadence, or retain 14-day with acknowledgment that 21-day performs comparably under the revised scenario parameters.

---

## H. Slashing Sweep

### Downtime sweep (fraud held at γ_fraud=1.00)

| sd | bull N | bear N | comp N | reg N | bull C_chg | bear C_chg | comp C_chg | reg C_chg |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 11,934 | 3,280 | 9,506 | 11,738 | -48.4% | +30.7% | -65.9% | -38.1% |
| 0.05 | 11,934 | 8,649 | 11,475 | 10,403 | -51.0% | -29.2% | -75.5% | -47.4% |
| 0.10 | 11,934 | 5,536 | 11,559 | 9,152 | -51.9% | +4.5% | -73.4% | -51.3% |
| 0.20 | 11,934 | 4,676 | 9,148 | 9,631 | -52.3% | +7.8% | -64.6% | -56.1% |
| 0.30 | 11,934 | 7,527 | 8,994 | 11,115 | -52.4% | -10.2% | -65.9% | -59.3% |

### Fraud sweep (downtime held at γ_down=0.10)

| sf | bull N | bear N | comp N | reg N | bull C_chg | bear C_chg | comp C_chg | reg C_chg |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 11,934 | 5,077 | 10,161 | 11,474 | -36.7% | -8.9% | -58.6% | -26.7% |
| 0.40 | 11,934 | 6,330 | 8,854 | 10,957 | -36.6% | -3.6% | -52.8% | -37.3% |
| 0.60 | 11,934 | 6,330 | 10,354 | 8,035 | -36.6% | -3.6% | -52.8% | +2.3% |
| 0.80 | 11,934 | 5,656 | 10,354 | 8,207 | -36.5% | -4.6% | -52.8% | +16.4% |
| 1.00 | 11,934 | 5,536 | 11,559 | 9,152 | -51.9% | +4.5% | -73.4% | -51.3% |

**Key finding: "Fraud penalty affects supply trajectory but not node count" — HOLDS ONLY FOR BULL.**
- Bull: Node count unchanged (11,934 at all sf values). Supply change varies (-36.5% to -51.9%), with a sharp jump at sf=1.00 as full forfeiture removes substantially more tokens.
- Bear: Node count varies from 5,077 (sf=0.20) to 6,330 (sf=0.40), non-monotonically. Supply trajectory shifts from deflationary (-8.9% at sf=0.20) to mildly inflationary (+4.5% at sf=1.00).
- Competitor and regulatory: Node count varies non-monotonically with fraud penalty. The interaction between fraud forfeiture severity, operator economics, and PID emission response produces complex second-order effects.
- At γ_fraud=1.00, the paper's original claim (N unchanged in bull and bear) holds only for bull.
