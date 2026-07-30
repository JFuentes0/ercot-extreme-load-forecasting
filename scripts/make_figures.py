"""Generate the four exploratory presentation figures.

**All four are EXPLORATORY.** They sit outside the D-016 pre-registration and
must not be presented as confirmatory. They do not touch the pre-registered
analysis or its result; they read the committed manifests, the captured
predictions, and the inventory, and draw.

Every number is derived from those artifacts — nothing is transcribed, mirroring
`report_stage4.py`. Re-running this script after a re-run of the sweep
regenerates the figures from the new data.

| Figure | Source |
| --- | --- |
| 1 reliability diagram | `runs/track_a/predictions/per_hour_predictions.csv` |
| 2 February 2021 case study | same |
| 3 coverage vs event severity | stage-5 manifests + the event inventory |
| 4 forest plot | stage-5 manifests + the D-016 analysis JSON |

Colours are the validated three-slot categorical palette (blue, orange); every
series also carries a distinct marker and linestyle, so identity never depends on
colour alone.

Usage:
    python scripts/make_figures.py
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
STAGE5 = REPO / "runs" / "track_a" / "stage5"
PREDICTIONS = REPO / "runs" / "track_a" / "predictions" / "per_hour_predictions.csv"
PROVENANCE = (
    REPO / "runs" / "track_a" / "predictions" / "per_hour_predictions_provenance.json"
)
ANALYSIS = REPO / "runs" / "track_a" / "stage5" / "analysis.json"
INVENTORY = REPO / "data" / "shared" / "event_inventory_headline.csv"
FIGURES = REPO / "docs" / "track_a" / "figures"

PRIMARY_FEATURE_SET = "temperature"
PRIMARY_CONDITION = "sampled"
NOMINAL_COVERAGE = 0.90

# Validated categorical palette (all-pairs CVD and normal-vision floors pass).
BLUE = "#2a78d6"
ORANGE = "#eb6834"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#dcdcd8"


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "axes.linewidth": 1.0,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "font.size": 12,
            "axes.titlesize": 15,
            "axes.labelsize": 12,
            "legend.frameon": False,
            "figure.dpi": 200,
        }
    )


def _exploratory(ax) -> None:
    """Stamp every figure. These are not confirmatory results."""
    ax.figure.text(
        0.995,
        0.005,
        "EXPLORATORY — outside the D-016 pre-registration",
        ha="right",
        va="bottom",
        fontsize=8,
        color=INK_MUTED,
    )


def _finish(fig, ax, path: Path) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _exploratory(ax)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {_short(path)}")


def _short(path: Path) -> str:
    """Repo-relative where possible; absolute otherwise (e.g. a scratch dir)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _titled(ax, title: str, subtitle: str | None = None) -> None:
    """Descriptive title, with any data-derived finding as a subtitle beneath it.

    Both are placed in axes coordinates. Fixed figure-fraction text collided with
    the title once the figure height changed.
    """
    ax.set_title(title, loc="left", pad=30 if subtitle else 14)
    if subtitle:
        ax.text(
            0.0,
            1.015,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10.5,
            color=INK_MUTED,
        )


def _footer(ax, text: str) -> None:
    """Provenance line below the axes.

    Offset in **points**, not axes fractions: these figures differ in height (the
    forest plot scales with the fold count), and a fractional offset that clears
    the x-label on a short figure overshoots badly on a tall one.
    """
    ax.annotate(
        text,
        xy=(0.0, 0.0),
        xycoords="axes fraction",
        xytext=(0, -54),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=8,
        color=INK_MUTED,
    )


def _manifests() -> list[dict]:
    files = sorted(STAGE5.glob("*/run_manifest_*.json"))
    if not files:
        print(f"no stage-5 manifests under {STAGE5}", file=sys.stderr)
        raise SystemExit(1)
    return [json.loads(p.read_text(encoding="utf-8")) for p in files]


# --------------------------------------------------------------------------- 1
def figure_reliability(predictions: pd.DataFrame, meta: dict) -> None:
    """Predicted probability against observed frequency, by regime.

    For a Gaussian forecast the reliability curve is read off the predictive
    CDF: for each nominal level p, the model's p-quantile is mu + z_p·sigma, and
    the observed frequency is the share of outcomes at or below it. A perfectly
    calibrated forecast traces the 45° line.
    """
    levels = np.linspace(0.02, 0.98, 49)
    z = stats.norm.ppf(levels)

    fig, ax = plt.subplots(figsize=(9.0, 7.0))
    ax.plot(
        [0, 1],
        [0, 1],
        linestyle=(0, (4, 3)),
        color=INK_MUTED,
        linewidth=1.4,
        label="perfect calibration",
        zorder=1,
    )

    styles = {
        "extreme": (BLUE, "o", "-", "Held-out extreme events"),
        "normal": (ORANGE, "s", "--", "Normal (non-event) periods"),
    }
    summary = {}
    for regime, (colour, marker, dash, label) in styles.items():
        subset = predictions[predictions["regime"] == regime]
        if subset.empty:
            continue
        y = subset["y_norm"].to_numpy()
        mu = subset["mean_norm"].to_numpy()
        sigma = subset["scale_norm"].to_numpy()
        observed = [float(np.mean(y <= mu + zi * sigma)) for zi in z]
        ax.plot(
            levels,
            observed,
            color=colour,
            marker=marker,
            linestyle=dash,
            linewidth=2.0,
            markersize=5,
            markevery=6,
            label=f"{label}  (n={len(y):,} h)",
            zorder=3,
        )
        # central 90% coverage, the freeze §7 calibration metric
        half = stats.norm.ppf(0.95) * sigma
        summary[regime] = float(np.mean((y >= mu - half) & (y <= mu + half)))

    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    # Title is DESCRIPTIVE. The finding is carried by the subtitle, computed from
    # the data -- so the figure cannot assert a conclusion the data does not
    # support. An earlier draft hard-coded the conclusion before the data existed.
    note = " · ".join(
        f"{styles[r][3].split(' (')[0]}: 90% interval covers {v:.0%}"
        for r, v in summary.items()
    )
    _titled(
        ax,
        "Reliability: predicted probability vs observed frequency",
        note + f"   (nominal {NOMINAL_COVERAGE:.0%})",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.55)
    ax.legend(loc="lower right", fontsize=10)
    run = meta["runs"][0] if meta.get("runs") else {}
    _footer(
        ax,
        f"{meta['cell']['feature_set']}/{meta['cell']['context_condition']}, "
        f"{meta['arm']}, seed {meta['seed']}, all folds pooled"
        + (f", context {run.get('context_size', '?')}" if run else ""),
    )
    _finish(fig, ax, FIGURES / "fig1_reliability.png")
    return summary


# --------------------------------------------------------------------------- 2
def figure_case_study(predictions: pd.DataFrame, meta: dict) -> dict | None:
    """One day of February 2021: forecast, interval, and what actually happened."""
    event = predictions[
        (predictions["event_id"] == "E14_20210212")
        & (predictions["regime"] == "extreme")
    ].copy()
    if event.empty:
        print("  fig2 skipped: no E14 predictions captured", file=sys.stderr)
        return None

    event["ts"] = pd.to_datetime(event["ts_utc"], utc=True)
    event["day"] = event["ts"].dt.tz_convert("America/Chicago").dt.date

    # Representative day: the one with the most hours outside the 90% interval --
    # the day the forecast was most confidently wrong. Chosen by a stated rule,
    # not by eye.
    z = stats.norm.ppf(0.95)
    event["outside"] = (event["y_mw"] < event["mean_mw"] - z * event["scale_mw"]) | (
        event["y_mw"] > event["mean_mw"] + z * event["scale_mw"]
    )
    counts = event.groupby("day")["outside"].sum().sort_values(ascending=False)
    chosen_day = counts.index[0]
    day = event[event["day"] == chosen_day].sort_values("ts")

    hours = np.arange(len(day))
    mean = day["mean_mw"].to_numpy()
    half = z * day["scale_mw"].to_numpy()
    actual = day["y_mw"].to_numpy()
    outside = day["outside"].to_numpy()

    fig, ax = plt.subplots(figsize=(11.0, 6.4))
    ax.fill_between(
        hours,
        mean - half,
        mean + half,
        color=BLUE,
        alpha=0.16,
        linewidth=0,
        label="90% prediction interval",
        zorder=1,
    )
    ax.plot(
        hours,
        mean,
        color=BLUE,
        linewidth=2.0,
        linestyle="-",
        label="Forecast mean",
        zorder=3,
    )
    ax.plot(
        hours,
        actual,
        color=INK,
        linewidth=2.0,
        linestyle="-",
        marker="o",
        markersize=4.5,
        label="Actual load",
        zorder=4,
    )
    if outside.any():
        ax.plot(
            hours[outside],
            actual[outside],
            linestyle="none",
            marker="o",
            markersize=11,
            markerfacecolor="none",
            markeredgecolor=ORANGE,
            markeredgewidth=2.2,
            label=f"Outside the interval ({int(outside.sum())} of {len(hours)} h)",
            zorder=5,
        )

    ax.set_xlabel(f"Hour of {chosen_day} (America/Chicago)")
    ax.set_ylabel("ERCOT load (MW)")
    _titled(
        ax,
        f"February 2021 — forecast, 90% interval, and actual load ({chosen_day})",
        f"{int(outside.sum())} of {len(hours)} hours fell outside the 90% "
        "prediction interval on this day",
    )
    ax.set_xticks(hours[::3])
    ax.set_xticklabels([f"{h:02d}" for h in hours[::3]])
    ax.grid(True, axis="y", alpha=0.55)
    ax.legend(loc="best", fontsize=10)
    shed = int(day["verified_shed"].sum())
    _footer(
        ax,
        f"E14_20210212 · {meta['cell']['feature_set']}/"
        f"{meta['cell']['context_condition']} · {meta['arm']} · seed {meta['seed']}"
        " · day chosen as the most hours outside the interval"
        + (
            f" · {shed} verified_shed hour(s) this day, excluded from the "
            "primary metric"
            if shed
            else ""
        ),
    )
    _finish(fig, ax, FIGURES / "fig2_february_2021.png")
    return {
        "day": str(chosen_day),
        "hours_outside": int(outside.sum()),
        "hours": len(hours),
        "verified_shed_hours": shed,
    }


# --------------------------------------------------------------------------- 3
def figure_coverage_vs_severity(runs: list[dict]) -> dict | None:
    """Does calibration degrade as events get more severe?"""
    inventory = pd.read_csv(INVENTORY, parse_dates=["onset"])
    margin_by_date = {
        row["onset"].strftime("%Y%m%d"): float(row["margin_C"])
        for _, row in inventory.iterrows()
    }

    per_event: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for run in runs:
        if (run["feature_set"], run["context_condition"]) != (
            PRIMARY_FEATURE_SET,
            PRIMARY_CONDITION,
        ):
            continue
        sec = run.get("secondary_metrics") or {}
        cov = sec.get("empirical_coverage_90")
        if cov is None:
            continue
        per_event[run["event_id"]][run["arm"]].append(float(cov))

    if not per_event:
        print("  fig3 skipped: no coverage in manifests", file=sys.stderr)
        return None

    fig, ax = plt.subplots(figsize=(10.0, 6.4))
    ax.axhline(
        NOMINAL_COVERAGE,
        color=INK_MUTED,
        linestyle=(0, (4, 3)),
        linewidth=1.4,
        label=f"nominal {NOMINAL_COVERAGE:.0%}",
        zorder=1,
    )

    fitted = {}
    for arm, colour, marker in (("CNP", BLUE, "o"), ("AdaCNP", ORANGE, "s")):
        xs, ys = [], []
        for event_id, by_arm in per_event.items():
            if arm not in by_arm:
                continue
            suffix = event_id.split("_")[-1]
            if suffix not in margin_by_date:
                continue
            xs.append(margin_by_date[suffix])
            ys.append(statistics.fmean(by_arm[arm]))
        if not xs:
            continue
        order = np.argsort(xs)
        xs, ys = np.asarray(xs)[order], np.asarray(ys)[order]
        ax.plot(
            xs,
            ys,
            linestyle="none",
            marker=marker,
            markersize=9,
            markerfacecolor=colour,
            markeredgecolor=SURFACE,
            markeredgewidth=1.6,
            label=f"{arm} (n={len(xs)} events)",
            zorder=3,
        )
        if len(xs) > 2:
            slope, intercept, r, p, _se = stats.linregress(xs, ys)
            grid = np.linspace(xs.min(), xs.max(), 50)
            ax.plot(
                grid,
                intercept + slope * grid,
                color=colour,
                linewidth=1.6,
                linestyle="--",
                alpha=0.75,
                zorder=2,
            )
            fitted[arm] = {"slope": slope, "r": r, "p": p, "n": len(xs)}

    ax.set_xlabel("Event severity — cold margin (°C, larger = more extreme)")
    ax.set_ylabel("Empirical 90% interval coverage")
    _titled(ax, "Interval coverage against event severity")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.55)
    ax.legend(loc="best", fontsize=10)
    if fitted:
        note = " · ".join(
            f"{arm}: slope {v['slope']:+.3f}/°C, r={v['r']:+.2f}, p={v['p']:.2f}"
            for arm, v in fitted.items()
        )
        _footer(ax, note + "   — trend lines are descriptive, not a test")
    _finish(fig, ax, FIGURES / "fig3_coverage_vs_severity.png")
    return fitted


# --------------------------------------------------------------------------- 4
def figure_forest(runs: list[dict], analysis: dict | None) -> dict | None:
    """Per-event paired differences, the pooled mean, and the MDE band."""
    per_event: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for run in runs:
        if (run["feature_set"], run["context_condition"]) != (
            PRIMARY_FEATURE_SET,
            PRIMARY_CONDITION,
        ):
            continue
        per_event[run["event_id"]][run["arm"]].append(
            float(run["primary_nll_latent_demand_normalized_units"])
        )

    rows = []
    for event_id, by_arm in per_event.items():
        if {"CNP", "AdaCNP"} - by_arm.keys():
            continue
        pairs = [c - a for c, a in zip(by_arm["CNP"], by_arm["AdaCNP"], strict=False)]
        if not pairs:
            continue
        mean = statistics.fmean(pairs)
        if len(pairs) > 1:
            se = statistics.stdev(pairs) / np.sqrt(len(pairs))
            crit = stats.t.ppf(0.975, df=len(pairs) - 1)
            lo, hi = mean - crit * se, mean + crit * se
        else:
            lo = hi = mean
        rows.append((event_id, mean, lo, hi, len(pairs)))

    if not rows:
        print("  fig4 skipped: no paired runs in the primary cell", file=sys.stderr)
        return None

    rows.sort(key=lambda r: r[1])
    labels = [r[0] for r in rows]
    means = np.array([r[1] for r in rows])
    los = np.array([r[2] for r in rows])
    his = np.array([r[3] for r in rows])
    y = np.arange(len(rows))

    pooled = (
        analysis.get("mean_paired_difference") if analysis else statistics.fmean(means)
    )
    pooled_ci = analysis.get("ci95") if analysis else None
    mde = analysis.get("minimum_detectable_effect") if analysis else None

    fig, ax = plt.subplots(figsize=(10.0, max(4.5, 0.42 * len(rows) + 2.6)))
    if mde:
        ax.axvspan(
            -mde,
            mde,
            color=INK_MUTED,
            alpha=0.10,
            linewidth=0,
            zorder=0,
            label=f"below the minimum detectable effect (±{mde:.2f})",
        )
    ax.axvline(0.0, color=INK_MUTED, linewidth=1.4, zorder=1)

    ax.hlines(y, los, his, color=BLUE, linewidth=2.0, zorder=3)
    ax.plot(
        means,
        y,
        linestyle="none",
        marker="o",
        markersize=8,
        markerfacecolor=BLUE,
        markeredgecolor=SURFACE,
        markeredgewidth=1.6,
        label="per-event difference (95% CI over 3 seeds)",
        zorder=4,
    )

    ax.plot(
        [pooled],
        [len(rows) + 0.6],
        linestyle="none",
        marker="D",
        markersize=12,
        markerfacecolor=ORANGE,
        markeredgecolor=SURFACE,
        markeredgewidth=1.6,
        label="pooled mean",
        zorder=5,
    )
    if pooled_ci:
        ax.hlines(
            [len(rows) + 0.6],
            pooled_ci[0],
            pooled_ci[1],
            color=ORANGE,
            linewidth=2.6,
            zorder=4,
        )

    ax.set_yticks(list(y) + [len(rows) + 0.6])
    ax.set_yticklabels(labels + ["POOLED"], fontsize=10)
    ax.set_xlabel("Paired CNP − AdaCNP primary NLL   (right of zero = AdaCNP better)")
    subtitle = None
    if mde is not None and pooled is not None:
        subtitle = (
            f"Pooled {pooled:+.3f}; minimum detectable effect \u00b1{mde:.3f} \u2014 "
            + (
                "the pooled effect lies inside the band this design can resolve"
                if abs(pooled) < mde
                else "the pooled effect exceeds the band this design can resolve"
            )
        )
    _titled(ax, "Per-event paired difference, CNP \u2212 AdaCNP", subtitle)
    ax.grid(True, axis="x", alpha=0.55)
    # Headroom on the right so the legend has genuinely empty space to sit in.
    # Without it the legend box overlapped the widest bottom-row interval.
    span = float(max(his.max(), abs(los.min())))
    ax.set_xlim(los.min() - 0.08 * span, his.max() + 0.42 * span)
    ax.legend(loc="lower right", fontsize=9.5)
    _footer(
        ax,
        f"{PRIMARY_FEATURE_SET}/{PRIMARY_CONDITION}, 3 seeds per event. Per-event CIs "
        "use 2 degrees of freedom and are correspondingly wide.",
    )
    _finish(fig, ax, FIGURES / "fig4_forest.png")
    return {"n_events": len(rows), "pooled": pooled, "mde": mde}


def main() -> int:
    _style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    print("=== EXPLORATORY PRESENTATION FIGURES ===")
    print("  All four are outside the D-016 pre-registration.\n")

    runs = _manifests()
    analysis = (
        json.loads(ANALYSIS.read_text(encoding="utf-8")) if ANALYSIS.is_file() else None
    )

    facts: dict = {"manifests": len(runs)}
    if PREDICTIONS.is_file():
        predictions = pd.read_csv(PREDICTIONS)
        meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        facts["reliability"] = figure_reliability(predictions, meta)
        facts["case_study"] = figure_case_study(predictions, meta)
        facts["prediction_provenance"] = {
            "cell": meta["cell"],
            "arm": meta["arm"],
            "seed": meta["seed"],
            "rows": meta["rows"],
        }
    else:
        print(
            f"  figs 1-2 skipped: run scripts/capture_predictions.py first "
            f"({_short(PREDICTIONS)} absent)",
            file=sys.stderr,
        )

    facts["coverage_vs_severity"] = figure_coverage_vs_severity(runs)
    facts["forest"] = figure_forest(runs, analysis)

    (FIGURES / "figure_facts.json").write_text(
        json.dumps(facts, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(f"\n  facts written to {_short(FIGURES / 'figure_facts.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
