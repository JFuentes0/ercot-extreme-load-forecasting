# ERCOT Extreme-Load Forecasting

Probabilistic day-ahead load forecasting on ERCOT during extreme cold, comparing Adaptive Conditional Neural Processes (AdaCNP) to a Conditional Neural Process baseline.

DOE SULI internship at NETL, Summer 2026. Mentor: John Brewer.

Project page: [jfuentes0.github.io](https://jfuentes0.github.io/#suli-forecasting)

Views are my own and do not necessarily reflect those of the U.S. Department of Energy or NETL.

## What this repo contains

Python 3.11 source for the AdaCNP / CNP comparison: configs, training and evaluation scripts, tests, and audit docs. Hourly ERCOT load artifacts are **not** in git (see `.gitignore`). Reproducibility of imported files is recorded in `docs/audit/`.

| Path | Contents |
|------|----------|
| `src/ercot_forecasting/` | Shared utilities plus Track A (neural processes) and Track B code |
| `configs/` | YAML run configs |
| `scripts/` | Import, training, and aggregation entry points |
| `tests/` | Pytest suite (shared, leakage, reproducibility, track tests) |
| `docs/` | Audit notes and study documentation |

## Results (short)

Leave-one-event-out across 17 extreme cold events, with a 9:00 a.m. CT issuance cutoff. AdaCNP improved Gaussian negative log likelihood versus CNP (mean paired difference 0.459, 95% CI [0.108, 0.811], p = 0.014). Calibration did not hold in the cold: a nominal 90% interval covered 96% of normal-period hours but only 63% of held-out extreme-event hours.

## Setup

Requires Python 3.11. From a clone:

```bash
uv sync --group track-a --group track-b --group dev
make check
```

Training and evaluation need the imported load artifacts under `data/` (not shipped). Smoke tests that use synthetic data do not.

```bash
make track-a-smoke
```

## License

Source in this repository is research code from a DOE SULI internship. Please contact the author before reuse outside personal or academic inspection.