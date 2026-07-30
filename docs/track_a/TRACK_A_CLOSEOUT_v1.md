# Track A — Closeout

**Status:** experimental programme complete through freeze execution stage 5.
**Date:** 2026-07-30
**Decision authority:** Jonathan Fuentes Rosales

This document records what Track A set out to do, what it established, what remains open,
and where the evidence lives. It is a closeout of the *experiment*, not of the repository:
several items below are deliberately left unresolved and are listed so that a future reader
does not mistake avoidance for completion.

---

## 1. What Track A was

A replication attempt, on new data, of a published result. Hu et al.
(arXiv:2602.04609) propose Adaptive Conditional Neural Processes (AdaCNP) and report
improved extreme-load forecasting on the PJM and ISO-NE systems. Track A asked whether that
advantage reproduces on **ERCOT** data, under an evaluation restricted to extreme cold
events — a restriction that comes from the internship brief, not from the source paper.

Track A was constituted as a bounded exception to historical ruling R-5, which prohibits
neural architectures within the frozen Track B design (D-005). Track B is untouched.

## 2. What was established

### The pre-registered result

**AdaCNP advantage detected on held-out ERCOT extreme events.** Mean paired difference
$+0.4593$ in Gaussian negative log likelihood, 95% CI $[+0.1075, +0.8111]$, two-sided paired
*t* $p = 0.0137$, Wilcoxon $p = 0.0202$ agreeing, $n = 17$ events × 3 seeds. Robustness
predeclared and consistent: excluding the single-day fold gives $+0.4855$ ($p = 0.0139$);
the leave-one-fold-out jackknife spans $[+0.343, +0.501]$ with the sign stable across all 17
refits; 11 of 17 events favour AdaCNP.

**Three qualifications are part of the result, not caveats to it.** The effect lies just
below the minimum detectable effect of 0.4953, so power at the realised size was ~77%. The
advantage appears only in the pre-registered cell — `temperature`/`nearest` ran $-0.240$.
And it is not a measurement of the source paper's effect size, which is roughly an order of
magnitude below what this design can resolve.

### The calibration finding

More consequential for grid operations than the arm comparison. The nominal 90% prediction
interval contains the observed load for **96% of normal-period hours** but only **63% of
held-out extreme-event hours**, and the reliability curve sits below the diagonal throughout
— the models systematically under-forecast demand while reporting high confidence. Coverage
degrades further with severity (~3.5 percentage points per °C of cold margin; CNP
$r = -0.55$, AdaCNP $r = -0.51$). Exploratory, but observed consistently across both arms and
all configurations.

### The mechanism finding

AdaCNP places **less** weight on cold historical analogues than uniform weighting does
(0.079 against CNP's 0.105), with only mildly non-uniform weighting overall (57.5 effective
contexts of 64). It scores better, but not by the mechanism its authors describe. Open
question.

## 3. Governance record

Seventeen decisions of record, D-001 through D-017. Those that shaped the experiment:

| ID | Decision |
| --- | --- |
| D-005 | Track A constituted as a bounded exception to R-5 |
| D-006 | Controlling event inventory; fold count derived, never a literal |
| D-007 | UTC axis, `America/Chicago` calendar, 09:00 CT D−1 issuance |
| D-008–D-009 | Stage-3 gate; controlling load artifact by content hash |
| D-010 | Censoring treatment adopted |
| D-011 | Stage-4 gate; E18-for-E21 substitution declined on the evidence |
| D-012 | Temperature features; `regional_index.parquet` imported |
| D-013 | Both context conditions run |
| D-014 | Stopping on inner validation, never on the held-out event |
| D-015 | Stage-5 execution gate |
| D-016 | Analysis plan pre-registered, committed before any stage-5 run |
| D-017 | Ratification of D-016 — **awaiting signature** |

## 4. Defects found and corrected

Recorded because a closeout that lists only successes is not a closeout.

**Lag-span buffer leakage.** The episode lag span was computed from the target day's first
hour rather than the issuance cutoff — instants ~15 hours apart — so the ±7-day buffer
under-excluded. 11 of 17 folds admitted one training day each whose features reached into the
buffered window. No event-window hour leaked, so the metric impact was negligible, but the
guarding test hard-coded the same wrong constant and could not fail. Both fixed; a regression
test now recomputes the expectation from the load axis independently.

**Minimum detectable effect overstated 4.8×.** `scipy.stats.nct.cdf` returns NaN at large
non-centrality; NaN fails every `>=` comparison, so the bisection read "cannot evaluate" as
"insufficient power" and reported 2.36 where the true value is 0.4953. Caught before any
result was reported. Verified against Monte Carlo; 19 regression tests added; two independent
implementations now agree to 0.001.

**Primary metric had no test coverage.** `gaussian_nll` — the study's sole adjudicating
metric — was untested until an audit found it. Now checked against closed forms and scipy.

**Two tautological tests.** Assertions that compared the implementation against itself and
could not fail. Replaced with independent checks.

## 5. What remains open

**Nothing below was resolved. Avoidance is recorded as avoidance.**

| Item | State |
| --- | --- |
| IB-2, IB-4, IB-5, IB-7 | Unresolved. Handled by scoped exclusion — the minimal import set was defined to avoid every artifact they touch. Each needs its own bounded task. |
| D-017 ratification | Drafted, awaiting PI signature. |
| Seed count | Freeze §8 fixes three. `SEED_COUNT_OPTIONS_v1.md` sets out the options; no decision taken. |
| Forecast weather | No day-ahead product with historical issuance timestamps exists in the corpus. The largest remaining divergence from the source protocol. |
| Event definition | All 17 events are cold-season. Broadening to summer peaks would roughly double *n*, the binding constraint. |
| Track B | Frozen, untouched, and unaffected by any Track A result. |
| Stage 6 | Freeze §10 gates it on "stage 5 passes **and** time permits". The three-seed sweep satisfies its content; no separate stage-6 execution was authorized or run. |
| Mentor/institutional approval | **No approval by John Brewer is claimed anywhere in Track A.** The neural-process extension rests on PI authority alone. Any submission independently requiring mentor sign-off remains subject to that separate requirement. |

## 6. Where the evidence lives

| Artifact | Path |
| --- | --- |
| Confirmatory result | `docs/track_a/STAGE5_RESULTS_v1.md` |
| Interpretation | `docs/track_a/FINDINGS_v1.md` |
| Pre-registration | `docs/track_a/ANALYSIS_PLAN_v1.md` |
| Power analysis | `docs/track_a/POWER_ANALYSIS_v1.md` |
| Fidelity to source | `docs/track_a/REPLICATION_FIDELITY_v1.md` |
| Figures + caveats | `docs/track_a/FIGURES_v1.md`, `docs/track_a/figures/` |
| Censoring ruling | `docs/track_a/CENSORING_TREATMENT_RULING_v1.md` |
| Decisions | `docs/project/DECISION_LOG.md` |
| Live status | `docs/project/CURRENT_STATE.md` |
| Run manifests | `runs/track_a/stage5/` (gitignored; 408 manifests, empty skip register) |

Every reported figure and table is regenerated from committed artifacts by script —
`report_stage4.py`, `analyze_stage5.py`, `make_figures.py`, `power_analysis.py` — rather than
transcribed. 170 tests pass; `ruff check` and `ruff format` clean.

## 7. Reproduction

```
make stage4                                   # exploratory grid
python scripts/run_stage5.py                  # 408-run sweep, resumable, ~4.8 h
python scripts/analyze_stage5.py              # the pre-registered test
python scripts/capture_predictions.py         # per-hour predictions for figures
python scripts/make_figures.py                # four exploratory figures
python scripts/power_analysis.py              # variance components and MDE
```

The stage-5 runner refuses to start unless the analysis plan is present and the run plan
declares stage 5 authorized with no outstanding gates.

## 8. If this work continues

In order of expected value:

1. **Fix calibration before changing architecture.** The arm difference is small beside a
   90% interval delivering 63%. Variance inflation conditioned on forecast temperature, or a
   conformal wrapper calibrated on cold days, would likely repay more.
2. **Report a regime-conditional coverage diagnostic.** Coverage degrades predictably with
   severity, so it is forecastable — a model that flags its own unreliability is directly
   usable for early-commitment decisions.
3. **Acquire day-ahead forecast weather with issuance timestamps.**
4. **Broaden the event definition** to raise *n*.
5. **Resolve the mechanism question** — why does AdaCNP help while de-emphasising cold
   analogues?
