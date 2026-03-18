# MeshNet DePIN Simulation

Agent-based simulation of a five-mechanism DePIN (Decentralized Physical Infrastructure Network) token economy with PID-controlled adaptive emission and an operational risk layer calibrated to empirical failure rates across Ethereum, Helium, Geodnet, and Filecoin.

## Papers

This codebase supports two papers:

**Pub3:** Zukowski, Z. (2026). "Adaptive Tokenomics: A Systems Engineering Approach to Programmable Incentive Design." SSRN Working Paper. [Link](https://ssrn.com/abstract=6364158)

**Pub4:** Zukowski, Z. (2026). "Operational Risk in Token Economies: How Infrastructure Failures Strengthen Adaptive Controllers and Break Reputation Systems." SSRN Working Paper. [Link](https://ssrn.com/abstract=6352118)

## Key Findings

**Adaptive emission outperforms static emission under all stress scenarios.** PID-controlled emission compresses worst-case variance by 6.25x under competitor shock (Pub3), improving to 6.89x when operational risk is added (Pub4). Static emission policy deteriorates further under operational risk.

**Operational risk accidentally strengthens the adaptive controller.** The controller mistakes temporary infrastructure outages for permanent operator losses and over-compensates with higher rewards. This builds a financial buffer that protects the network when a real economic shock arrives.

**Threshold-gated reputation systems collapse under operational risk.** Any reputation system that conditions recovery on a performance threshold above the operational risk floor will converge to zero. At 0.5% daily downtime, operators have a 16% chance of qualifying for seasonal reputation recovery. Lowering the threshold from 0.99 to 0.95 restores stability.

## Architecture

### Base Model (Pub3): `src/meshnet_model.py`

Five integrated token mechanisms simulated over 1,825 timesteps (5 years):
1. **Productive staking** with slashing for fraud/downtime
2. **Burn-mint equilibrium** linking service fees to token supply
3. **PID-controlled adaptive emission** targeting network size
4. **Reputation-weighted governance** reducing concentration
5. **Conviction voting** for community proposals

Three operator types (high-commitment, casual, mercenary) make entry/exit decisions based on staking yield vs. opportunity cost. Four macro scenarios (bull, bear, competitor shock, regulatory shock) test robustness.

### Operational Risk Extension (Pub4): `src/meshnet_oprisk.py`

Extends each operator with a six-step operational risk check per epoch:
1. Correlated infrastructure event (probability 0.5%/epoch, affects infrastructure group)
2. Independent downtime (per-operator, log-normal rate)
3. Catastrophic failure (permanent exit)
4. Operational slashing (with superlinear correlation penalty)
5. Reputation update (incidents reduce reputation score)
6. Economic decision (unchanged from base model)

Seven parameters calibrated from four networks:
| Parameter | Description | Base Value |
|-----------|-------------|------------|
| p_down | Daily downtime probability | 0.5% |
| p_exit | Annual catastrophic exit | 3% |
| p_slash | Annual operational slashing | 0.05% |
| rho_corr | Correlated failure fraction | 10% |
| phi | Partial failure fraction | 20% |
| T_recover | Mean recovery time | 3 days |
| delta_rep | Reputation decay per incident | 0.25 |

## Simulation Battery

| Battery | Runs | Paper |
|---------|------|-------|
| Base model (4 scenarios x 2 models x seed 42) | 8 | Pub3 |
| 30-seed ensemble (4 scenarios x 2 models x 30 seeds) | 240 | Pub3 |
| PID sensitivity (60 gain configs x 4 scenarios) | 240 | Pub3 |
| Adversarial scenarios (wash trading, slashing, interaction) | 318 | Pub3 |
| Operational risk ensemble (30 seeds x 4 scenarios x 2 models) | 240 | Pub4 |
| Operational risk sensitivity (sweeps, profiles, interactions) | 384 | Pub4 |
| Gap-closing: P_DOWN bug fix verification | 12 | Pub4 |
| Gap-closing: Reputation threshold sweep | 30 | Pub4 |
| Gap-closing: Regulatory 30-seed ensemble | 62 | Pub4 |
| Gap-closing: Multi-seed rho sweep | 300 | Pub4 |
| Gap-closing: Multi-seed protocol profiles | 90 | Pub4 |
| **Total** | **~1,924** | |

## Quick Start

```bash
pip install -r requirements.txt
cd src/

# Run base model (Pub3)
python meshnet_model.py

# Run operational risk extension (Pub4, sequential)
python meshnet_oprisk.py

# Run operational risk extension (Pub4, parallel)
python meshnet_oprisk_parallel.py

# Generate all exhibits
python generate_exhibits.py
python generate_oprisk_exhibits.py
```

## Operational Risk Standards

The operational risk taxonomy draws on two emerging standards:
- **ValOS** (Validator Operation Standard): 74 active risk vectors, 64 testable controls. [GitHub](https://github.com/ValOS-Standard)
- **NORS** (Node Operator Risk Standard): 31 control objectives, 7 categories. [Docs](https://nors.docs)

## License

MIT License. See [LICENSE](LICENSE).

## Citation

If you use this code, please cite the associated papers:

```bibtex
@article{zukowski2026adaptive,
  title={Adaptive Tokenomics: A Systems Engineering Approach to Programmable Incentive Design},
  author={Zukowski, Zach},
  journal={SSRN Working Paper},
  year={2026},
  doi={10.2139/ssrn.6364158},
  url={https://ssrn.com/abstract=6364158}
}

@article{zukowski2026oprisk,
  title={Operational Risk in Token Economies: How Infrastructure Failures Strengthen Adaptive Controllers and Break Reputation Systems},
  author={Zukowski, Zach},
  journal={SSRN Working Paper},
  year={2026},
  doi={10.2139/ssrn.6352118},
  url={https://ssrn.com/abstract=6352118}
}
```

## Author

Zach Zukowski | [Medium](https://medium.com/@CryptoZach) | [SSRN](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=10386216)
