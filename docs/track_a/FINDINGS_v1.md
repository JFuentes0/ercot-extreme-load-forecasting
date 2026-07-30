# Track A — Findings

**ERCOT extreme-load forecasting with Conditional Neural Processes**
Replication of Hu et al., *Resilient Load Forecasting under Climate Change* (arXiv:2602.04609), on ERCOT data
**Date:** 2026-07-30 · **Stage:** freeze execution stage 5 complete (408 runs, 17 folds, 3 seeds)

---

## 1. The finding that matters most for grid operations

**These forecasts are confidently wrong precisely when the grid is under stress.**

The models were asked for a 90% prediction interval — a range that should contain the
actual load nine times in ten. Measured across all 17 held-out extreme cold events:

| Regime | 90% interval actually contains the load |
| --- | --- |
| Normal (non-event) days | **96%** |
| **Held-out extreme cold events** | **63%** |

In ordinary conditions the forecast is honest, even slightly cautious. In the conditions
that matter — the events that have historically forced ERCOT toward emergency action — the
interval that claims 90% confidence is wrong more than a third of the time.

**And it fails in the dangerous direction.** The reliability curve for extreme events sits
below the diagonal along its whole length: actual load is *systematically higher* than the
forecast distribution implies. This is not symmetric noise. The model under-forecasts
demand during extreme cold, and reports high confidence while doing so.

**It gets worse as the event gets worse.** Coverage declines measurably with event severity
— roughly 3.5 percentage points per °C of cold margin (CNP r = −0.55, AdaCNP r = −0.51).
The mildest events approach nominal coverage; the most severe event in the record,
February 2021, falls to 44–56%.

**A concrete example.** On 18 February 2021, **all 24 hours** of the day fell outside the
90% interval, with actual load running about 10 GW above the forecast mean. That day
carries no verified load-shed hours, so this is a forecasting failure, not an artifact of
demand being curtailed.

### Why this matters more than the model comparison

For a balancing authority the operational question is not "which architecture scores
better" but "can I trust the uncertainty band when I decide whether to commit generation
early." On this evidence, the answer for these models is: **in normal conditions yes, in
extreme conditions no — and the band gives no warning that it has stopped being
trustworthy.** A forecast that is uncertain and says so is manageable. A forecast that is
wrong and confident is the failure mode that leads to under-commitment.

This finding held across every configuration tested and both model arms. It is not a
property of one architecture; it is a property of these models trained this way on this
data.

---

## 2. The pre-registered result: AdaCNP versus CNP

The analysis plan, the primary endpoint, the test, and the decision rule were all
**committed before any stage-5 run executed** (`ANALYSIS_PLAN_v1.md`, decision D-016,
commit `11d3613`). The primary cell was chosen for fidelity to Hu et al., not for the size
of the effect it showed.

> **AdaCNP advantage detected on held-out ERCOT extreme events.**

| | |
| --- | --- |
| Unit of analysis | Per-event paired difference (CNP − AdaCNP), seeds averaged |
| n | 17 events × 3 seeds |
| Mean paired difference | **+0.4593** (positive = AdaCNP better) |
| 95% CI | **[+0.1075, +0.8111]** |
| Two-sided paired *t* | **p = 0.0137** |
| Wilcoxon signed-rank | p = 0.0202 — agrees |
| Minimum detectable effect | 0.4953 |

Robustness checks, all predeclared: excluding the one fold with a single held-out day gives
+0.4855 (p = 0.0139); the leave-one-fold-out jackknife ranges [+0.343, +0.501] with the
sign stable across all 17 refits. 11 of 17 events favour AdaCNP.

Secondary metrics point the same way — CRPS 0.469 vs 0.486, RMSE 0.756 vs 0.773, MAE 0.612
vs 0.630, calibration error 0.247 vs 0.272, all favouring AdaCNP. Freeze §7 reserves
adjudication to the primary metric; these are reported for interpretation only.

### Three things that must be said alongside that result

**The effect sits just below what the design could reliably detect.** The observed +0.459
is marginally under the MDE of 0.495, so this study had roughly 77% power at the effect it
found — under the 80% target. The result is real by the pre-registered rule, but it is
near the edge of resolvable and **wants independent replication rather than treatment as
settled.**

**Only the pre-registered cell shows it.** Of the four configurations run,
`temperature/sampled` gave +0.459; `temperature/nearest` gave **−0.240**, and
`base/sampled` +0.016. Had the cell been chosen after seeing the results, almost any
conclusion could have been supported. The pre-registration is what makes this claim
legitimate, and that dependence should be stated plainly rather than buried.

**It does not replicate the paper's effect size — it cannot.** Hu et al. report an
AdaCNP-over-CNP NLL margin of 0.8–3.4%; in these units that is 0.02–0.12, an order of
magnitude below this design's MDE. This study had 5–9% power to detect a margin that size,
and would need roughly 400–800 events to do so reliably. ERCOT's history supplies 17. What
was detected here is a *larger* effect than the paper reports, in a *harder* evaluation
regime; it is consistent with the paper's direction but is not a measurement of the same
quantity.

---

## 3. The mechanism does not behave as the paper describes

AdaCNP's claimed advantage comes from concentrating attention on relevant historical
analogues — during extreme cold, on similarly cold days. Freeze §7 asks for exactly this
measurement, and it became computable only once temperature features were added (D-012).

| Quantity | CNP | AdaCNP |
| --- | --- | --- |
| Weight on cold context days | 0.105 | **0.079** |
| Effective context count (of 64) | 64.0 | 57.5 |
| Weight entropy (nats) | 4.159 = log 64 | 4.041 |

CNP's uniform weighting puts 10.5% of its weight on cold days, which is simply the cold
share of its context set. **AdaCNP puts less — 7.9%.** It systematically *de-emphasizes*
cold analogues, and its weighting is only mildly non-uniform (57.5 effective contexts out
of 64).

So AdaCNP does score better on held-out extreme events, but **not by doing the thing the
paper says it does.** Whatever produces the gain here, it is not concentration on cold
analogue days. That is a genuine open question and, for a research contribution, arguably
more interesting than the score difference itself.

---

## 4. What would actually help an operator

Ranked by expected operational value, not by novelty:

1. **Fix the calibration before changing the architecture.** The arm difference (+0.46 NLL)
   is small next to the calibration failure (90% nominal delivering 63% actual). Variance
   inflation conditioned on forecast temperature, or a conformal wrapper calibrated on cold
   days specifically, would likely buy more than any architecture change.
2. **Report a regime-conditional coverage diagnostic operationally.** Coverage degrades
   predictably with cold margin — which means it is forecastable. A model that flags "my
   interval is unreliable today" is directly actionable for early-commitment decisions.
3. **Acquire day-ahead weather forecasts with issuance timestamps.** The single largest gap
   between this work and the source paper. Every temperature feature here is *past-observed*;
   Hu et al. also use next-day forecast temperature. No such archived product exists in this
   corpus.
4. **Broaden the event definition.** All 17 events are cold-season. Including summer peaks
   would roughly double n, which the power analysis identifies as the binding constraint.

---

## 5. Limitations

- **n = 17 events**, fixed by ERCOT's history and by the internship brief's extreme-weather
  framing. The power analysis (`POWER_ANALYSIS_v1.md`) puts the detectable effect at
  0.49–0.62 depending on cell.
- **Censoring.** 1,139 of 1,584 scored held-out hours per seed are `unresolved` — their
  load-shed status is unknown and, per D-010, is not resolved in either direction. If some
  were in fact shed, the primary metric is contaminated by an unknown amount. 80
  `verified_shed` hours are excluded from the primary metric.
- **No forecast weather**, as above.
- **Censored values enter the inputs.** A held-out day's lag features are observed served
  load, which for later event days may include shed hours. D-010 removes those from the
  *metric*, not from the *inputs*.
- **Two folds lose held-out days** under the temperature feature set (E05 3→1, E07 4→3);
  the predeclared sensitivity excluding sub-2-day folds leaves the result unchanged.
- **Three seeds.** Initialisation noise dominates the measurement; more seeds is the
  cheapest available improvement and would need a freeze §8 amendment.
- **Not confirmatory beyond the pre-registered endpoint.** Everything in §1 and §3 is
  descriptive or exploratory. Only §2's primary test is confirmatory.

---

## 6. Provenance

| Artifact | |
| --- | --- |
| Pre-registration | `ANALYSIS_PLAN_v1.md`, D-016, committed `11d3613` before any stage-5 run |
| Execution gate | D-015 |
| Censoring treatment | D-010 |
| Feature set / context / stopping | D-012 / D-013 / D-014 |
| Runs | 408, zero failures; skip register empty |
| Fold count | 17, derived from the inventory at run time, never a literal |
| Full results | `STAGE5_RESULTS_v1.md` · Figures: `FIGURES_v1.md` · Power: `POWER_ANALYSIS_v1.md` |
| Fidelity to source | `REPLICATION_FIDELITY_v1.md` |

**One correction of record.** The minimum detectable effect was initially computed as 2.36
by a routine that mishandled `scipy.stats.nct.cdf` returning NaN at large non-centrality;
the true value is 0.495, a 4.8× overstatement. It was caught before any result was
reported, verified against Monte Carlo, and is covered by regression tests. Two independent
implementations — simulation and non-central *t* — now agree to within 0.001.
