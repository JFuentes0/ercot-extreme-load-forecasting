# Project Charter

## Project

ERCOT Extreme-Load Forecasting

## Decision authority

Jonathan Fuentes is the final project decision authority.

## Primary active experiment

Track A compares:

- Standard Conditional Neural Process using uniform mean aggregation.
- Adaptive Conditional Neural Process using target-conditioned adaptive
  weighting of the same context representations.

The primary research question is whether learned target-aware weighting of
historical examples improves probabilistic forecasting during held-out ERCOT
extreme-cold events.

## Provenance of the research question

**Track A is a replication attempt, on new data, of a specific published result.**
This context is load-bearing for interpreting any Track A finding and is recorded
here because it is not derivable from the code or the artifacts.

- **Source paper.** Chenxi Hu, Yue Ma, Yifan Wu, Yunhe Hou, *Resilient Load
  Forecasting under Climate Change: Adaptive Conditional Neural Processes for
  Few-Shot Extreme Load Forecasting*, arXiv:2602.04609v1 (4 Feb 2026). Local copy
  at `~/ercot-model-references/adacnp_arxiv_2602.04609.pdf`. AdaCNP was found
  during the project's preliminary literature review.
- **The paper's data is not this project's data.** Hu et al. evaluate on **PJM**
  and **ISO-NE**. Track A asks whether their positive AdaCNP-over-CNP finding
  reproduces on **ERCOT**. Differences from their protocol are therefore fidelity
  questions, catalogued in `docs/track_a/REPLICATION_FIDELITY_v1.md`.
- **Institutional context.** A summer research internship, brief titled
  *"Advancing Frontiers of Energy Forecasting with Novel Methods"*: RTOs and ISOs
  increasingly manage extreme-weather forecast uncertainty and sometimes still
  shed load; early generation commitment mitigates this but conflicts with
  least-cost dispatch. The brief asks for research into novel uncertainty-management
  methods using AI/ML that industry could adopt.

### Two consequences that must not be re-derived incorrectly

1. **The extreme-event framing comes from the internship brief, not from the
   paper.** Hu et al. evaluate on continuous multi-year series with a standard
   test split. Restricting evaluation to discrete extreme cold events is Track A's
   own choice, answering the brief. It makes the evaluation harder and
   statistically thinner than the source paper's, which is a legitimate
   contribution — **but it means a null on the events says nothing about the
   paper's claim.**
2. **The n = 17 event count is a consequence of that framing, not a design
   defect.** It follows from ERCOT's cold-event history and the load-eligibility
   rule. `docs/track_a/POWER_ANALYSIS_v1.md` quantifies what it permits: a
   minimum detectable paired-NLL effect of roughly 0.28–0.57, against a
   paper-reported margin of 0.02–0.12. **A null stage-5 result is therefore
   uninformative about the source finding and must not be reported as failing to
   replicate it.**

## Secondary frozen experiment

Track B compares:

- Quantile-gradient-boosting Model A.
- Regime-aware quantile-gradient-boosting Model B.

Track B retains its frozen scientific design and may be executed only when a
task explicitly states TRACK=B.

## Shared foundation

Both tracks must use the same:

- frozen ERCOT cold-event inventory;
- leave-one-event-out outer partitions;
- plus/minus-7-day event buffers;
- issuance-time conventions;
- source-data hashes;
- censoring evidence;
- leakage protections.

## Current priority

Freeze execution stages 1–4 are complete. Stage 4 ran as an exploratory
factorial under D-011, with the censoring ruling adopted (D-010) and the
replication-fidelity closures in force (D-012, D-013, D-014).

**Stages 5 and 6 are blocked.** Two things gate stage 5, and neither is code:

1. an execution-gate decision extending D-011, which grants stage 4 only;
2. **the inferential procedure the freeze still lacks** — unit of analysis, how
   folds aggregate, how variance is estimated, and the rule by which a
   difference is judged real. `POWER_ANALYSIS_v1.md` supplies the numbers to
   write it against. It must be settled *before* the sweep, because it
   determines what the sweep has to record.

See `docs/project/CURRENT_STATE.md` for the authoritative live status.
