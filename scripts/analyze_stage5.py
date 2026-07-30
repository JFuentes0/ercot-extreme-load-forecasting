"""The pre-registered stage-5 analysis (D-016).

**This script is committed before stage 5 runs.** Its git commit timestamp
predates the data it analyses, which is what makes the stage-5 result
confirmatory rather than exploratory. Nothing here may be changed after the
sweep without recording the change in the deviations register.

Specification — `docs/track_a/ANALYSIS_PLAN_v1.md`:

* **Primary endpoint, one test.** Per-event paired difference
  (CNP − AdaCNP) in held-out event-period Gaussian NLL under D-010, averaged
  over the three frozen seeds, in the **temperature / sampled** cell. Two-sided
  paired t-test against zero at alpha = 0.05, n = number of load-eligible events
  (derived, never a literal).
* **Everything else is descriptive.** Other cells, the calibration metric and
  the freeze §7 secondaries are reported without p-values.
* **Robustness, not extra tests.** Wilcoxon signed-rank; a sensitivity excluding
  folds with fewer than two held-out days; a leave-one-fold-out jackknife. If
  Wilcoxon disagrees with the t-test the result is reported **inconclusive** —
  the favourable one is never chosen.

Validate against stage-4 data before stage 5 exists:

    python scripts/analyze_stage5.py --runs runs/track_a/stage4 --validate
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = REPO / "runs" / "track_a" / "stage5"

#: Pre-registered primary cell: the most faithful to Hu et al. -- temperature
#: features as in their PJM inputs, sampled context as in their Alg. 1/2.
#: Chosen on fidelity, NOT on which produced the larger observed effect.
PRIMARY_FEATURE_SET = "temperature"
PRIMARY_CONDITION = "sampled"

ALPHA = 0.05
MIN_EVENT_DAYS_FOR_SENSITIVITY = 2

#: Hu et al.'s AdaCNP-over-CNP NLL margins against the CNP column (their Table 2).
PAPER_MARGIN_FRACTIONS = {"PJM": 0.034, "ISO-NE": 0.008}


@dataclass
class Paired:
    """One event's paired difference, averaged over seeds."""

    event_id: str
    delta: float
    n_seeds: int
    held_out_days: int
    per_seed: list[float] = field(default_factory=list)


def _load_manifests(runs_dir: Path) -> list[dict]:
    manifests = sorted(runs_dir.glob("*/run_manifest_*.json"))
    if not manifests:
        print(f"no manifests under {runs_dir}", file=sys.stderr)
        raise SystemExit(1)
    return [json.loads(p.read_text(encoding="utf-8")) for p in manifests]


def _pair(runs: list[dict]) -> dict[tuple[str, str], list[Paired]]:
    """Group into per-event paired differences, per cell, seeds averaged."""
    by_key: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for run in runs:
        key = (
            run["feature_set"],
            run["context_condition"],
            run["seed"],
            run["event_id"],
        )
        by_key[key][run["arm"]] = run

    per_cell_event: dict[tuple[str, str, str], list[tuple[float, int]]] = defaultdict(
        list
    )
    for (feature_set, condition, _seed, event_id), arms in by_key.items():
        if {"CNP", "AdaCNP"} - arms.keys():
            continue
        delta = (
            arms["CNP"]["primary_nll_latent_demand_normalized_units"]
            - arms["AdaCNP"]["primary_nll_latent_demand_normalized_units"]
        )
        per_cell_event[(feature_set, condition, event_id)].append(
            (delta, arms["CNP"]["held_out_episodes"])
        )

    cells: dict[tuple[str, str], list[Paired]] = defaultdict(list)
    for (feature_set, condition, event_id), entries in per_cell_event.items():
        deltas = [d for d, _ in entries]
        cells[(feature_set, condition)].append(
            Paired(
                event_id=event_id,
                delta=statistics.fmean(deltas),
                n_seeds=len(deltas),
                held_out_days=entries[0][1],
                per_seed=deltas,
            )
        )
    for values in cells.values():
        values.sort(key=lambda p: p.event_id)
    return cells


def _paired_t(values: list[float]) -> tuple[float, float, tuple[float, float]]:
    """Mean, two-sided p, and the 95% CI of the mean."""
    array = np.asarray(values, dtype=float)
    n = len(array)
    mean = float(array.mean())
    if n < 2:
        return mean, float("nan"), (float("nan"), float("nan"))
    result = stats.ttest_1samp(array, popmean=0.0, alternative="two-sided")
    se = float(array.std(ddof=1) / np.sqrt(n))
    crit = float(stats.t.ppf(1.0 - ALPHA / 2.0, df=n - 1))
    return mean, float(result.pvalue), (mean - crit * se, mean + crit * se)


def _wilcoxon(values: list[float]) -> float:
    if len(values) < 6:
        return float("nan")
    try:
        return float(stats.wilcoxon(np.asarray(values, dtype=float)).pvalue)
    except ValueError:
        return float("nan")


def _two_sided_power(effect: float, sd: float, n: int) -> float:
    """Power of the two-sided one-sample t-test at ``effect``.

    ``scipy.stats.nct.cdf`` returns **NaN** for large non-centrality (ncp above
    roughly 8-10). Left unguarded that is silently destructive here: NaN fails
    every ``>=`` comparison, so a bisection reads "cannot evaluate" as "not
    enough power" and walks the answer upward. It reported an MDE of 2.36 where
    the true value is 0.49 — a five-fold overstatement, in a number that appears
    in the headline verdict.

    Where the exact form is unavailable the normal approximation is used
    instead. It is accurate precisely in the large-ncp regime where `nct` fails,
    and there power is indistinguishable from 1 anyway.
    """
    se = sd / np.sqrt(n)
    ncp = effect / se
    crit = stats.t.ppf(1.0 - ALPHA / 2.0, df=n - 1)
    exact = (
        1.0
        - stats.nct.cdf(crit, df=n - 1, nc=ncp)
        + stats.nct.cdf(-crit, df=n - 1, nc=ncp)
    )
    if np.isfinite(exact):
        return float(exact)
    return float(stats.norm.cdf(ncp - crit) + stats.norm.cdf(-ncp - crit))


def _mde(values: list[float], n: int) -> float:
    """Minimum detectable effect at 80% power, from the observed spread.

    Bisects on :func:`_two_sided_power`, which is monotone increasing in the
    effect, so the bracket is guaranteed to contain the crossing.
    """
    if len(values) < 2:
        return float("nan")
    sd = float(np.std(values, ddof=1))
    if sd == 0.0:
        return 0.0

    lo, hi = 0.0, 10.0 * sd
    if _two_sided_power(hi, sd, n) < 0.80:  # pragma: no cover - defensive
        return float("nan")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if _two_sided_power(mid, sd, n) >= 0.80:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def _verdict(mean: float, p: float, p_wilcoxon: float, mde: float) -> list[str]:
    """The pre-registered decision rule. No branch is chosen after the fact."""
    out: list[str] = []
    disagree = not np.isnan(p_wilcoxon) and (p < ALPHA) != (p_wilcoxon < ALPHA)
    if disagree:
        out.append(
            "INCONCLUSIVE — the t-test and Wilcoxon disagree at alpha=0.05. "
            "Both are reported; neither is preferred. The pre-registration "
            "forbids selecting the favourable one."
        )
        return out

    if p < ALPHA and mean > 0:
        out.append("AdaCNP ADVANTAGE DETECTED on held-out ERCOT extreme events.")
    elif p < ALPHA and mean < 0:
        out.append("CNP ADVANTAGE DETECTED on held-out ERCOT extreme events.")
    else:
        out.append("NO DETECTABLE DIFFERENCE between the arms.")
        out.append(
            f"The minimum detectable effect at this n is {mde:.4f}. Hu et al.'s "
            "margin, converted to these units, is 0.02-0.12 — below the MDE. "
            "This result therefore NEITHER CONFIRMS NOR REFUTES Hu et al., and "
            "must not be reported as a failure to replicate."
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument(
        "--validate",
        action="store_true",
        help="dry-run against another stage's manifests to prove the script works",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    runs = _load_manifests(args.runs)
    cells = _pair(runs)
    fold_counts = {r["derived_fold_count"] for r in runs}
    derived_folds = fold_counts.pop() if len(fold_counts) == 1 else None

    print("=== STAGE-5 PRE-REGISTERED ANALYSIS (D-016) ===")
    if args.validate:
        print("  *** VALIDATION RUN — not the stage-5 result ***")
    print(f"  manifests            {len(runs)}  from {args.runs}")
    print(f"  derived fold count   {derived_folds}  (from the manifests)")
    print(f"  primary cell         {PRIMARY_FEATURE_SET} / {PRIMARY_CONDITION}")
    print(f"  test                 two-sided paired t, alpha = {ALPHA}")
    print("  unit of analysis     per-event paired difference, seeds averaged")

    key = (PRIMARY_FEATURE_SET, PRIMARY_CONDITION)
    if key not in cells:
        print(
            f"\nFAIL: the pre-registered primary cell {key} is absent from these runs.",
            file=sys.stderr,
        )
        return 1

    primary = cells[key]
    deltas = [p.delta for p in primary]
    n = len(deltas)
    mean, p_value, (ci_lo, ci_hi) = _paired_t(deltas)
    p_w = _wilcoxon(deltas)
    mde = _mde(deltas, n)

    print(f"\n{'=' * 74}\n=== PRIMARY RESULT ===")
    print(f"  n (events)                  {n}")
    print(f"  seeds per event             {primary[0].n_seeds}")
    print(f"  mean paired difference      {mean:+.4f}   (positive = AdaCNP better)")
    print(f"  95% CI                      [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"  two-sided paired t p-value  {p_value:.4f}")
    print(f"  Wilcoxon p-value            {p_w:.4f}   (robustness, not a second test)")
    print(
        f"  minimum detectable effect   {mde:.4f}   at 80% power, from observed spread"
    )

    print("\n=== VERDICT (pre-registered decision rule) ===")
    for line in _verdict(mean, p_value, p_w, mde):
        print(f"  {line}")

    print("\n=== ROBUSTNESS (predeclared; not additional tests) ===")
    kept = [
        p.delta for p in primary if p.held_out_days >= MIN_EVENT_DAYS_FOR_SENSITIVITY
    ]
    dropped = [
        p.event_id for p in primary if p.held_out_days < MIN_EVENT_DAYS_FOR_SENSITIVITY
    ]
    if dropped:
        m2, p2, _ = _paired_t(kept)
        print(
            f"  excluding folds with <{MIN_EVENT_DAYS_FOR_SENSITIVITY} held-out days "
            f"({', '.join(dropped)}): n={len(kept)}, mean {m2:+.4f}, p {p2:.4f}"
        )
    else:
        print(
            f"  no fold has fewer than {MIN_EVENT_DAYS_FOR_SENSITIVITY} held-out days"
        )

    if n > 2:
        jack = [_paired_t(deltas[:i] + deltas[i + 1 :])[0] for i in range(n)]
        worst = max(range(n), key=lambda i: abs(jack[i] - mean))
        print(
            f"  jackknife mean range        [{min(jack):+.4f}, {max(jack):+.4f}]; "
            f"most influential fold {primary[worst].event_id}"
        )
        signs = {np.sign(j) for j in jack}
        print(f"  sign stable under jackknife {'YES' if len(signs) == 1 else 'NO'}")

    print(f"\n{'=' * 74}\n=== DESCRIPTIVE — all cells (no p-values, freeze §7) ===")
    header = f"{'feature set':<13}{'context':<10}{'n':>4}{'mean delta':>13}{'sd':>10}{'AdaCNP wins':>13}"
    print(header)
    print("-" * len(header))
    for (feature_set, condition), values in sorted(cells.items()):
        d = [v.delta for v in values]
        sd = statistics.stdev(d) if len(d) > 1 else float("nan")
        wins = sum(1 for x in d if x > 0)
        marker = "  <- PRIMARY" if (feature_set, condition) == key else ""
        print(
            f"{feature_set:<13}{condition:<10}{len(d):>4}{statistics.fmean(d):>13.4f}"
            f"{sd:>10.4f}{wins:>8}/{len(d):<4}{marker}"
        )

    print("\n=== PER-EVENT, PRIMARY CELL ===")
    print(f"{'event':<16}{'mean delta':>12}{'held-out days':>15}{'per-seed':>32}")
    print("-" * 75)
    for entry in primary:
        seeds = ", ".join(f"{s:+.3f}" for s in entry.per_seed)
        print(
            f"{entry.event_id:<16}{entry.delta:>12.4f}{entry.held_out_days:>15}"
            f"{seeds:>32}"
        )

    _descriptive_secondaries(runs, key)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "primary_cell": {"feature_set": key[0], "condition": key[1]},
                    "n_events": n,
                    "mean_paired_difference": mean,
                    "ci95": [ci_lo, ci_hi],
                    "p_two_sided_paired_t": p_value,
                    "p_wilcoxon": p_w,
                    "minimum_detectable_effect": mde,
                    "verdict": _verdict(mean, p_value, p_w, mde),
                    "per_event": [
                        {
                            "event_id": e.event_id,
                            "delta": e.delta,
                            "per_seed": e.per_seed,
                            "held_out_days": e.held_out_days,
                        }
                        for e in primary
                    ],
                    "all_cells": {
                        f"{f}/{c}": {
                            "n": len(v),
                            "mean": statistics.fmean([x.delta for x in v]),
                            "sd": statistics.stdev([x.delta for x in v])
                            if len(v) > 1
                            else None,
                            "adacnp_wins": sum(1 for x in v if x.delta > 0),
                        }
                        for (f, c), v in sorted(cells.items())
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"\n  machine-readable result written to {args.json_out}")

    return 0


def _descriptive_secondaries(runs: list[dict], key: tuple[str, str]) -> None:
    """Freeze §7 secondaries for the primary cell, by arm. Descriptive only."""
    rows = [
        r
        for r in runs
        if (r["feature_set"], r["context_condition"]) == key
        and r.get("secondary_metrics")
    ]
    if not rows:
        print("\n=== FREEZE §7 SECONDARY METRICS: not present in these manifests ===")
        return

    print("\n=== FREEZE §7 SECONDARY METRICS — primary cell, by arm ===")
    print("  Descriptive. Freeze §7: these do not adjudicate the comparison.\n")
    keys = list(rows[0]["secondary_metrics"].keys())
    header = f"{'metric':<38}{'CNP':>14}{'AdaCNP':>14}"
    print(header)
    print("-" * len(header))
    for metric in keys:
        cells_by_arm = {}
        for arm in ("CNP", "AdaCNP"):
            values = [
                r["secondary_metrics"][metric]
                for r in rows
                if r["arm"] == arm and r["secondary_metrics"].get(metric) is not None
            ]
            cells_by_arm[arm] = statistics.fmean(values) if values else None
        fmt = lambda v: "n/a" if v is None else f"{v:.6f}"
        print(
            f"{metric:<38}{fmt(cells_by_arm['CNP']):>14}{fmt(cells_by_arm['AdaCNP']):>14}"
        )


if __name__ == "__main__":
    sys.exit(main())
