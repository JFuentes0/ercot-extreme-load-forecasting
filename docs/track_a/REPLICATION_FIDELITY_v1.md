# Replication Fidelity — Track A against Hu et al. (2026)

**Source:** Chenxi Hu, Yue Ma, Yifan Wu, Yunhe Hou. *Resilient Load Forecasting under Climate
Change: Adaptive Conditional Neural Processes for Few-Shot Extreme Load Forecasting.*
arXiv:2602.04609v1, 4 Feb 2026. Local copy: `~/ercot-model-references/adacnp_arxiv_2602.04609.pdf`

**Purpose.** Track A attempts to reproduce the paper's positive AdaCNP-over-CNP finding on ERCOT
data. This document states, item by item, where Track A matches the paper's protocol and where it
departs. Deviations are not automatically defects — but a null result can only speak to the
paper's claim in the dimensions where the protocols agree.

---

## 1. The paper's reported effect is small, and its uncertainties overlap

Paper Table 2, verbatim:

| PJM | AdaCNP | CNP | ANP | GP | NP |
| --- | --- | --- | --- | --- | --- |
| MSE (%) | **0.95 ± 0.09** | 0.99 ± 0.11 | 1.44 ± 0.16 | 75.72 ± 6.40 | 1.21 ± 0.11 |
| NLL | **−0.92 ± 3.4%** | −0.89 ± 3.8% | −0.80 ± 3.2% | 0.97 ± 4.1% | −0.80 ± 3.6% |
| Pinball | **0.02 ± 0.09%** | 0.02 ± 0.10% | 0.03 ± 0.11% | 0.19 ± 0.82% | 0.03 ± 0.10% |

| ISO-NE | AdaCNP | CNP | ANP | GP | NP |
| --- | --- | --- | --- | --- | --- |
| MSE (%) | **0.10 ± 0.01** | 0.11 ± 0.01 | 0.11 ± 0.01 | 3.39 ± 0.01 | 0.113 ± 0.28 |
| NLL | **−1.33 ± 4.6%** | −1.32 ± 6.6% | −1.32 ± 6.1% | 0.818 ± 8.1% | −1.32 ± 6.7% |
| Pinball | **0.012 ± 0.02%** | 0.013 ± 0.03% | 0.013 ± 0.02% | 0.013 ± 0.03% | 0.099 ± 0.02% |

**Against CNP specifically — the only baseline Track A runs — the margins are:**

| Dataset | Metric | AdaCNP | CNP | Margin | Reported spread |
| --- | --- | --- | --- | --- | --- |
| PJM | NLL | −0.92 | −0.89 | **3.4%** | ±3.4% / ±3.8% |
| PJM | MSE | 0.95 | 0.99 | **4.0%** | ±0.09 / ±0.11 |
| ISO-NE | NLL | −1.33 | −1.32 | **0.8%** | ±4.6% / ±6.6% |
| ISO-NE | MSE | 0.10 | 0.11 | **9%** | ±0.01 / ±0.01 |

Three observations that bear directly on replication:

1. **The AdaCNP-vs-CNP NLL margin is 0.8–3.4%, smaller than the reported spread in every case.**
   On ISO-NE, AdaCNP's NLL advantage over CNP is 0.8% against spreads of 4.6% and 6.6%. The paper
   performs no significance test.
2. **The paper's headline framing is against the *weakest* baselines, not CNP.** The abstract's
   "22% MSE reduction relative to the strongest baseline" does not correspond to the CNP column;
   §4.2 states it for ISO-NE, where the table shows 0.10 vs CNP 0.11 (≈9%). CNP is consistently
   the second-best model, and AdaCNP's edge over it is the narrowest margin in the paper.
3. **Consequence for Track A.** Reproducing a 1–3% NLL difference requires far more statistical
   resolution than 17 paired events provide. Track A's stage-4 margins (0.02–0.14 in normalized
   NLL) are not obviously inconsistent with the paper — they are simply unresolvable at n=17.
   **A null on the events is not evidence against the paper.**

---

## 2. Deviation table

Status column records what has since been done. D1, D2, D4 and D6 are **closed** by
decisions D-012, D-013 and D-014; the rest remain open and are stated as limitations.

| # | Dimension | Hu et al. | Track A | Severity | Status |
| --- | --- | --- | --- | --- | --- |
| D1 | **Temperature features** | PJM: past day's load **and temperature**, **next day's temperature forecast**, non-linear functions of temperature. ISO-NE: "past load and weather information" | Originally **none**. Now a 57-dim set adding 24 temperature lags, `roll24`, heating/cooling degrees and a squared term | **CRITICAL** | **CLOSED (D-012)** — partially: past-observed only, no forecast temperature exists in the corpus |
| D2 | **Context construction** | Randomly **sampled** context set `C ⊆ D_H` each iteration (Alg. 1 line 3, Alg. 2 line 2) | Originally nearest-64 by Euclidean distance. Now **both** conditions are run | **CRITICAL** | **CLOSED (D-013)** |
| D3 | **Event definition** | **DTW shape distance**, sliding ±7-day window, 3-σ threshold on mean DTW distance → individual extreme **days** | **Temperature-derived** multi-day event windows (`peak_val`, `margin_C`) from a frozen inventory | **HIGH** | OPEN — the inventory is frozen under D-006 |
| D4 | **Training length** | ~1000 epochs (Fig. 4; loss still descending at 200–400) | Originally 300 optimizer steps. Now trained to a ceiling with the checkpoint chosen on **inner validation** | **HIGH** | **CLOSED (D-014)** |
| D5 | **Baselines** | AdaCNP vs CNP, **ANP**, **GP**, **NP** | AdaCNP vs CNP only | MEDIUM | OPEN |
| D6 | **Variance reporting** | mean ± std across runs, every cell | Originally one seed. Now all three frozen seeds, reported as mean ± sd of paired differences | MEDIUM | **CLOSED (D-014 / freeze §8)** |
| D7 | **Metrics** | MSE (%), NLL, **Pinball loss** | Gaussian NLL (primary), served-load NLL (diagnostic) | MEDIUM | OPEN — no Pinball or MSE |
| D8 | **Test-set construction** | Normal/Extreme split; extreme test set "kept separate" | **Leave-one-event-out with ±7-day buffers** excluded from training *and* retrieval | Track A **stricter** |
| D9 | **Censoring treatment** | Not addressed | D-010 ruling; `verified_shed` excluded from primary metric | Track A **stricter** |
| D10 | **Issuance-time discipline** | Not stated; PJM uses "next day's temperature forecast" | 09:00 CT D−1 cutoff enforced and tested | Track A **stricter** |
| D11 | **Dataset span** | PJM 8 years; ISO-NE 1985-01-01 → 1992-10-12 | ERCOT 2002-01-01 → 2026-06-30 (24.5 years) | LOW |
| D12 | **Context size** | 5/10/15 in the 1-D toy; real-data value not stated | 64 headline, 32 sensitivity | LOW (unverifiable) |

---

## 3. The two critical deviations, in detail

> **This section describes the state as found, before D-012 and D-013.** It is kept in the
> present tense because it is the diagnosis that motivated those decisions; §2's Status column
> records that both are now closed, and §7–§8 report what changed as a result.

### D1 — Track A has no temperature signal at all

The paper's PJM feature set is explicit: *"For each day, we input the past day's electrical load
and temperature, the next day's temperature forecast, and additional features such as non-linear
functions of the temperatures, binary indicators for weekends or holidays, and yearly features."*

Track A's feature vector is 5 calendar features + 24 load lags (`features.py:46-55`). **Every
temperature term in the paper's feature set is absent.**

This is not a peripheral difference. AdaCNP's mechanism is target-conditioned similarity in a
learned embedding of `x`. If `x` carries no temperature, the adaptive layer cannot learn "this
historical day was cold like today" — it can only infer that from load shape and calendar
position. The paper's extreme regime is a *temperature-driven* regime, and the mechanism is being
asked to find temperature analogues without temperature.

**Track A's own event inventory is temperature-defined** (`peak_val` in °C, `margin_C`), so the
events are selected by a variable the model cannot observe. Freeze §7 even lists "weight assigned
to cold-context days" as a secondary metric — uncomputable as built.

**Mitigating fact: most of the paper's temperature features are issuance-legal.** The past day's
temperature is fully available at the 09:00 CT D−1 cutoff. Only *next-day forecast* temperature
requires an archived forecast product. The corpus already contains realized weather
(`ghcnh_hourly_station_qcfiltered.parquet`, `regional_index.parquet`) that was deliberately
deferred at import, not found to be absent.

### D2 — Nearest-neighbour retrieval partially pre-empts the mechanism under test

The paper samples the context set: Algorithm 1 line 3, *"Sample context set C = {(x_i, y_i)} ⊆
D_H"*; Algorithm 2 line 2 likewise at inference. Nothing in the paper selects context by
similarity **before** the model sees it — that selection is precisely what the adaptive layer is
introduced to perform, and what uniform-mean CNP is claimed to do badly.

Track A instead pre-selects the 64 nearest days by Euclidean distance in input space
(`stage3.select_context_indices`), and hands **that same filtered set to both arms**.

This is a plausible mechanism for the null. Uniform averaging over 64 *already-similar* days is a
much stronger baseline than uniform averaging over 64 *random* days. Track A has, in effect,
implemented part of AdaCNP's relevance selection inside the data pipeline and given it to CNP for
free — compressing the gap the experiment is trying to measure.

This deviation was introduced for a good reason (issuance-safe retrieval, freeze §3–4) and it is
tested for leakage. But it changes what the comparison means.

---

## 4. What Track A's existing results look like through this lens

**Stage 3, non-event periods, 1,766 validation episodes, one seed:**

| Arm | Validation Gaussian NLL |
| --- | --- |
| CNP | 2.3547 |
| **AdaCNP** | **2.0547** |

AdaCNP better by 0.30 — a ~13% NLL improvement, *larger* than the paper's own 0.8–3.4% margins,
on a sample ~100× the event set. This is the closest analogue to the paper's standard test split.
Caveats: stage 3 was not designed as an arm comparison, one seed, 300 steps, no variance estimate.

**Stage 4, three events, one seed, n=3 paired differences:** CNP lower on primary NLL in all three
events by 0.02/0.07/0.14, with the ordering reversing on E14's served-load diagnostic.

Read together, the tentative shape is: **AdaCNP's advantage appears in the aggregate regime where
n is adequate, and is unresolvable in the extreme-event regime where n=3 (stage 4) or n=17
(stage 5).** That is a coherent and reportable finding, and it is consistent with the paper rather
than contradicting it — the paper's own extreme-regime margins are 1–9%.

---

## 5. Recommended actions, ordered by leverage per unit of effort

1. **Run a paper-faithful random-sampling context arm alongside the nearest-neighbour arm (D2).**
   Small code change; directly tests whether the retrieval step is suppressing the effect. If the
   CNP–AdaCNP gap opens under random sampling, that is the finding.
2. **Import realized weather and add past-day temperature features (D1).** Issuance-legal, no new
   acquisition, restores the axis the mechanism operates on. Requires a decision-log entry, since
   freeze §3 contemplates weather and the executed pipeline dropped it without one.
   For next-day temperature, use realized temperature explicitly labelled as a **perfect-forecast
   oracle condition** and report it as an upper bound — standard practice, and honest.
3. **Train to convergence (D4).** ~1000 epochs vs 300 steps. Compute is not a constraint; this is
   minutes.
4. **Report mean ± spread over the three frozen seeds (D6)**, matching the paper's presentation and
   supplying the variance estimate the freeze never specified.
5. **Add ANP as a third arm (D5)** if time permits — it is the baseline AdaCNP is actually arguing
   against, and the paper's margin over ANP (11–19% MSE) is far larger than over CNP.
6. **Report the aggregate (stage-3-like) comparison as a first-class result, not just a
   validation step.** It is the paper-comparable setting and it currently holds the strongest
   signal in the project.
7. **Consider adding a DTW-based extreme-day set (D3)** as a secondary event definition, to test
   whether the paper's finding reproduces under the paper's own event criterion. The
   temperature-based inventory can stay as the primary, ERCOT-specific definition.

## 6. What not to conclude

- **Do not report "AdaCNP does not replicate on ERCOT" on the strength of stage 4.** With n=3
  events, no variance estimate, no temperature features, and a retrieval step that advantages the
  baseline, a null is uninformative about the paper's claim.
- **Do not treat the ±7-day buffer / LOEO protocol as a fidelity failure.** It is stricter than the
  paper's split (D8) and is a genuine methodological contribution of this work.

---

## 7. Aggregate (non-event) comparison — executed 2026-07-29

The paper-comparable setting: non-event periods only (D-008 scope), 1,667 validation
day-episodes per run, three frozen seeds, both feature sets and both context conditions.
Generated by `scripts/run_aggregate_comparison.py`.

| Feature set | Context | n seeds | mean Δ | sd | AdaCNP wins |
| --- | --- | ---: | ---: | ---: | ---: |
| base | nearest | 3 | −0.0235 | 0.0831 | 1/3 |
| base | sampled | 3 | +0.0035 | 0.0514 | 1/3 |
| temperature | nearest | 3 | +0.1146 | 0.3360 | 1/3 |
| temperature | sampled | 3 | −0.0705 | 0.0731 | 0/3 |

Positive means AdaCNP better. **AdaCNP wins 3 of 12 runs; every cell mean is within its own
spread of zero.** In the aggregate regime the two arms are indistinguishable.

**This supersedes an earlier reading of the stage-3 record.** A single stage-3 run at one seed
and 300 steps showed AdaCNP ahead by 0.30 NLL (2.0547 versus 2.3547), which was described as a
possible partial replication. Repeated across three seeds with converged training that gap does
not survive: it was initialisation noise. The power analysis makes the reason explicit —
seed-to-seed variation dominates the measurement, and a single pair of runs cannot separate an
effect from it.

**Read against the paper's own thesis, this is the expected shape.** Hu et al. argue AdaCNP
helps specifically under distribution shift, where relevant context is scarce and uniform
averaging dilutes it. In-distribution normal periods are where uniform aggregation should be
adequate, so **no aggregate advantage is a prediction of the paper, not a contradiction of it.**
The two results together — no effect in aggregate, a directional effect on extreme events with
temperature present — are the pattern the mechanism story implies. Neither is established.

## 8. Statistical power — see `POWER_ANALYSIS_v1.md`

Measured from the stage-4 grid rather than assumed:

- **Minimum detectable effect at 17 events × 3 seeds: 0.28–0.57** paired NLL, at 80% power.
- **Hu et al.'s margin in these units: 0.02–0.12.** Power to detect it: **0.05–0.15.** Detecting
  a PJM-sized effect would need roughly 150–412 events; an ISO-NE-sized effect, 3,000+.
  ERCOT's inventory supplies 17. **A null stage-5 result cannot speak to the paper's claim.**
- **The effect observed in the temperature cells (~0.55–0.59) is detectable** — the full sweep
  would find it with 0.82–0.93 power. That is the comparison stage 5 can actually settle.
- **Initialisation noise dominates**, so raising the seed count above the frozen three is the
  cheapest remaining improvement. Caveat: between-event variance is estimated as zero in three
  of four cells because three events cannot resolve it, so the stated MDEs are optimistic.
