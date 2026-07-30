# Seed Count — Options for Decision

**Status:** decision paper, no decision taken. Raising the seed count **amends a frozen
item** (`EXPERIMENT_FREEZE_v1.md` §8 fixes three seeds: 20260729, 20260730, 20260731) and
therefore requires its own recorded decision.
**Date:** 2026-07-30
**Evidence:** `POWER_ANALYSIS_v1.md`, regenerated from the 408-run stage-5 sweep.

---

## 1. Why this is on the table

The power analysis decomposed the measured noise into two components, per cell:

| Cell | σ_event (between events) | σ_seed (initialisation) | σ_total |
| --- | ---: | ---: | ---: |
| base / nearest | 0.530 | 0.864 | 1.014 |
| base / sampled | 0.000* | 1.173 | 1.173 |
| temperature / nearest | 0.621 | 1.006 | 1.182 |
| **temperature / sampled** (primary) | **0.570** | **0.655** | **0.868** |

\* estimated as zero; the random-effects estimator clips at zero where seed noise dominates.

**Initialisation noise is the larger component in every cell.** Unlike the between-event
term, it is reducible: averaging over more seeds shrinks it as $1/\sqrt{n_\text{seeds}}$.
The event count cannot be increased — ERCOT's history supplies 17 — so seeds are the only
remaining lever on precision.

## 2. What each option buys

Minimum detectable effect at 17 events, from the measured variance components:

| Cell | 1 seed | **3 seeds (current)** | 10 seeds |
| --- | ---: | ---: | ---: |
| base / nearest | 0.729 | 0.530 | 0.431 |
| base / sampled | 0.850 | 0.490 | 0.268 |
| temperature / nearest | 0.859 | 0.615 | 0.505 |
| **temperature / sampled** | 0.631 | **0.495** | **0.441** |

Compute cost, at the measured 42.2 s per run and the current 2×2×2 factorial:

| Seeds | Runs | Serial wall-clock |
| ---: | ---: | --- |
| 3 (current) | 408 | ~4.8 h *(already spent)* |
| 5 | 680 | ~8.0 h |
| 10 | 1,360 | ~15.9 h |

## 3. The options

### Option A — Keep three seeds. No amendment.

The freeze stands unchanged. The stage-5 result is reported as it is, with its MDE of 0.495
and the honest note that power at the realised effect was ~77%.

*For:* no frozen item is touched; nothing is re-run; the pre-registered result stands
exactly as committed. *Against:* the headline effect (0.459) sits just below the MDE, and
that gap is the single most attackable feature of the finding.

### Option B — Raise to ten seeds for the primary cell only. *(Recommended)*

Amend §8 to permit additional seeds, re-run **only** `temperature`/`sampled` at seven further
seeds (17 folds × 2 arms × 7 = 238 runs, ~2.8 h), and report the ten-seed estimate as a
**predeclared precision extension**, with the three-seed pre-registered result remaining
primary.

*For:* MDE falls from 0.495 to 0.441, moving the observed effect from just below the
detection threshold to just above it. Cheapest available improvement — under three hours.
*Against:* extending after seeing a significant result is exactly the move pre-registration
exists to constrain. **This is only defensible if the extension is declared before the new
runs and the three-seed result stays primary regardless of what the extension shows** —
including if it weakens the finding.

### Option C — Raise to ten seeds across the full factorial.

1,360 runs, ~15.9 h serial. Tightens every cell, not just the primary.

*For:* the descriptive cells (which currently carry wide spreads) become far more
informative, and the temperature-vs-context decomposition firms up. *Against:* an overnight
job for a marginal gain on cells that are explicitly not confirmatory.

## 4. The trap to avoid

**Adding seeds because the result was significant, and stopping when it looks best, is
optional stopping.** It inflates the false-positive rate and would void the pre-registration.
The plan (§6) forbids it: *"No adding seeds after seeing p."*

Option B is only clean if all three conditions hold:

1. the extension is **recorded as a decision before the additional runs execute**;
2. the seed count is **fixed in advance** (ten, not "until it stabilises");
3. the three-seed pre-registered result **remains the primary reported result**, and the
   ten-seed figure is labelled a precision extension — whichever direction it moves.

Under those conditions the extension is a legitimate improvement in precision. Without them
it is a *p*-hacking pattern wearing a lab coat.

## 5. Recommendation

**Option B, or Option A if there is any doubt about honouring the three conditions.**

The scientific case for B is real: seed noise dominates, the fix is cheap, and the current
MDE sits awkwardly close to the effect. But the value of this project's result rests
substantially on the discipline of its pre-registration, and a precision extension executed
carelessly would cost more credibility than the tighter interval buys.

If B is taken, the decision entry should state the seed list explicitly, cite this paper,
and repeat condition 3 in its own words.

---

**Not decided by this document.** It records options and their costs only. Raising the seed
count requires a decision-log entry amending freeze §8.
