# Stage-5 Analysis Plan — v1 (PRE-REGISTRATION)

> ## COMMITTED BEFORE THE DATA EXISTS
>
> This document and `scripts/analyze_stage5.py` are committed **before any stage-5 run
> executes**. The commit timestamp is what makes the stage-5 result confirmatory rather
> than exploratory. Nothing here may be changed after the sweep without an entry in the
> deviations register (§8).
>
> **Status: adopted by D-016, pending PI ratification.** Authored on PI instruction with
> the three substantive choices confirmed in advance (§1). If the PI would have chosen
> differently, that variant is reported too, clearly labelled post-hoc, with the
> pre-committed version primary.

**Date:** 2026-07-29
**Governs:** freeze execution stage 5, the full leave-one-event-out sweep
**Instruments:** this document; `scripts/analyze_stage5.py`
**Relates to:** freeze §7 (metrics), §8 (seeds), §10 (stages); D-010, D-011, D-012,
D-013, D-014; `POWER_ANALYSIS_v1.md`; `REPLICATION_FIDELITY_v1.md`

---

## 1. Why a pre-registration is needed at all

`EXPERIMENT_FREEZE_v1.md` §7 names one primary metric and states that secondary metrics
"do not adjudicate the comparison". That solves metric multiplicity. Two gaps remain, and
this document closes them:

1. **The freeze contains no inferential procedure.** No unit of analysis, no test, no α,
   no rule for judging a difference real. "Confirmatory" is defined by *stage number* —
   a result is confirmatory if it comes from stage 5 or 6, not because it meets any
   criterion.
2. **D-012 and D-013 created four experimental cells** that the freeze predates. Testing
   all four would spend statistical power the design does not have.

`POWER_ANALYSIS_v1.md` measured the minimum detectable effect at **0.28–0.57** paired NLL
at 17 events and 3 seeds. That permits **exactly one** confirmatory test. Everything below
follows from that constraint.

### Choices confirmed by the PI before authoring

| Choice | Decision |
| --- | --- |
| Primary cell | **temperature / sampled** |
| Sidedness | **Two-sided** |
| Freeze §7 secondary metrics | **All eight computed** |

---

## 2. Primary endpoint — one test, fixed in advance

| Element | Specification |
| --- | --- |
| **Quantity** | Per-event paired difference **CNP − AdaCNP** in held-out event-period Gaussian NLL under the D-010 censoring treatment |
| **Unit of analysis** | One value per load-eligible event, with the three frozen seeds averaged |
| **n** | The derived load-eligible event count, read from the run manifests. **Never a literal** (D-006, freeze §10.1) |
| **Cell** | `feature_set = temperature`, `context_condition = sampled` |
| **Test** | Two-sided one-sample paired *t*-test against zero |
| **α** | 0.05 |
| **Reported** | Mean difference, 95% CI, *p*, **and the MDE alongside** |

Positive means **AdaCNP better** (lower NLL).

### Why the unit of analysis is the per-event paired difference

The freeze requires normalization fitted per fold. That makes raw NLL values **not
comparable across folds** — a number for E14 and a number for E08 sit on different scales.
Only the *within-event* CNP−AdaCNP difference is comparable, because both arms in a fold
share that fold's normalizer and its persisted context-index file. Averaging seeds first
removes initialisation noise, which `POWER_ANALYSIS_v1.md` found dominates the
measurement.

### Why temperature/sampled is the primary cell

It is the cell most faithful to Hu et al.: temperature features corresponding to their
PJM inputs (past-day temperature and non-linear functions of it), and randomly sampled
context matching their Algorithm 1 line 3 and Algorithm 2 line 2.

**This choice is made on fidelity, not on observed effect size.** In the stage-4
exploratory grid, temperature/**nearest** showed a marginally *larger* difference (+0.59
versus +0.55). Selecting the smaller one because it is the more faithful replication is
what distinguishes a pre-registration from a rationalisation, and it is recorded here so
the reasoning is auditable.

---

## 3. Everything else is descriptive

The following are reported **without p-values and without inferential claims**:

- the other three cells (base/nearest, base/sampled, temperature/nearest);
- the freeze §7 "key calibration metric", |empirical 90% coverage − 0.90|;
- all eight freeze §7 secondary metrics;
- the D-010 all-hours served-load diagnostic;
- per-event and per-seed breakdowns.

The calibration metric is deliberately **not** treated as a co-primary endpoint. Freeze §7
calls it "key" but does not make it primary, and promoting it would reintroduce the
multiplicity this plan exists to avoid.

---

## 4. Robustness checks — predeclared, and not additional tests

1. **Wilcoxon signed-rank** on the same per-event values. **If it disagrees with the
   *t*-test at α = 0.05, the result is reported INCONCLUSIVE.** The favourable one is
   never selected.
2. **Small-fold sensitivity.** Folds with fewer than **2** held-out days are excluded and
   the primary recomputed. Under the temperature feature set E05 drops to a single
   held-out day (D-012 discloses this), so this check is known in advance to bite.
3. **Leave-one-fold-out jackknife** of the primary mean, reporting the range and whether
   the sign is stable — to show no single event drives the result.

None of these can produce a "significant" finding on its own. They qualify the primary
result; they do not supplement it.

---

## 5. Decision rule — fixed before the data

| Outcome | Reported as |
| --- | --- |
| *p* < 0.05 and mean > 0 | **AdaCNP advantage detected** on held-out ERCOT extreme events at this n |
| *p* < 0.05 and mean < 0 | **CNP advantage detected** on held-out ERCOT extreme events at this n |
| *p* ≥ 0.05 | **No detectable difference.** MDE = X. Hu et al.'s margin (0.02–0.12 in these units) lies **below** the MDE, so this **neither confirms nor refutes** the source finding and **must not be reported as a failure to replicate** |
| t-test and Wilcoxon disagree | **Inconclusive.** Both reported, neither preferred |

The MDE is reported beside the result in **every** branch.

---

## 6. Fixed design — no optional stopping

- All load-eligible folds × 3 frozen seeds × both arms. The sweep runs to completion.
- **No adding seeds after seeing *p*.** Raising the seed count would amend freeze §8 and
  requires its own decision; doing so in response to a result would invalidate this plan.
- **No peeking-and-extending**, no interim analyses, no post-hoc cell reselection.
- Folds that fail to build are logged in the skip register and reported; the primary is
  computed on those that completed, and the count is stated.

---

## 7. Metric definitions (pre-registered, since each embeds a choice)

| Metric | Definition |
| --- | --- |
| Primary NLL | Gaussian NLL over scored hours; `verified_shed` excluded per D-010 |
| Served-load NLL | Same over **all** held-out hours; estimand is served load |
| CRPS | Closed form for a Gaussian; verified against adaptive quadrature to 1e-15 |
| RMSE, MAE | Over scored hours |
| 90% interval width | 2·z₀.₉₅·σ |
| Empirical 90% coverage, \|coverage − 0.90\| | Central predictive interval |
| High-load exceedance | Observed rate above the **fold's training-partition** 99th-percentile load, versus the model's predicted exceedance probability. The threshold comes from training, never from the held-out event |
| AdaCNP weight entropy | Shannon entropy (nats) of the context weights |
| Effective context count | exp(entropy); equals the context size exactly under uniform weighting |
| Cold-context weight | Share of weight on context days whose cutoff `roll24` falls below the **fold's training pool** 10th percentile. Relative, so no absolute temperature is hard-coded. **N/A in base cells** — undefined, not zero |

All secondary metrics are computed over the **same scored hours** as the primary, so they
describe the same estimand.

---

## 8. Deviations register

Any departure from this plan is recorded here with its reason, before the affected result
is reported.

| Date | Deviation | Reason |
| --- | --- | --- |
| — | *(none at time of pre-registration)* | — |

---

## 9. What this plan does not do

- It does not authorize stage 6 or any further stage.
- It does not amend freeze §8's three seeds.
- It does not resolve IB-2, IB-4, IB-5, or IB-7.
- It does not change the censoring ruling, the event inventory, or any frozen item.
- It does not predict the outcome, and it commits to reporting a null as a null.
