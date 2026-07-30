# Censoring Treatment Ruling — v1 **ADOPTED**

> ## STATUS: ADOPTED
>
> Adopted by Jonathan Fuentes, project decision authority, on 2026-07-29 under decision
> **D-010** (`docs/project/DECISION_LOG.md`).
>
> This ruling satisfies the hard gate that `docs/track_a/EXPERIMENT_FREEZE_v1.md` §11.1
> places on freeze execution stage 4. **Satisfying that gate is not the same as opening
> stage 4.** Stage-4 execution requires its own execution-gate decision; D-008 authorizes
> stage 3 and no other stage.

**Supersedes:** `docs/track_a/CENSORING_TREATMENT_RULING_v1_DRAFT.md` (draft, unadopted)
**Controlling documents:** `EXPERIMENT_FREEZE_v1.md` §7, §11.1; decisions D-006, D-008, D-009
**Date adopted:** 2026-07-29

---

## 1. Evidence base

This ruling rests on the imported, hash-verified artifacts:

| Artifact | SHA-256 (prefix) |
| --- | --- |
| `data/frozen/track_a/v7_demand_censored_v3.csv` | `3e7bd358…` |
| `data/frozen/track_a/v7_censoring_windows_v3.csv` | `bc51b7c5…` |
| `data/frozen/track_a/v7_censoring_mapping_rule_v3.md` | `2984b799…` |

Every count below was recomputed from those artifacts at adoption time, not carried forward
from the draft or from any historical document.

### 1.1 Censoring state of the load-tier event record

| Measure | Value |
| --- | --- |
| Load-tier event-hours | **1,271** |
| `verified_shed` | **80** |
| `unresolved` | **1,191** |
| `verified_no_shed` | **0** |
| Load-eligible events | **derived at run time** — never a literal |

Counts of events and folds are deliberately not written as literals here, per D-006 and
freeze §10.1. They are derived by
`ercot_forecasting.track_a.event_eligibility.derive_eligible_events` and asserted by test.

### 1.2 The two established shed windows

| Window | Event | Status | Hours | Source status |
| --- | --- | --- | --- | --- |
| `W-2011-0202-v3` | E08_20110202 | `verified_shed` | 9 | URL confirmed; **quotation PI-supplied, not independently read** |
| `W-2021-0215-v3` | E14_20210212 | `verified_shed` | 71 | `RETRIEVED_VERIFIED_OCR` |
| `W-2021-0215-WIDE-v3` | E14_20210212 | **`NOT_APPLIED`** | 106 | Sensitivity envelope only |

The wide February 2021 envelope remains **not applied**. EEA3 status alone does not establish
firm shed in every hour, and this ruling does not extend it.

**Concentration.** Of the 80 `verified_shed` hours, **71 fall in E14 (February 2021)** — 34% of
that event's 208 hours. The censoring question is concentrated in precisely the event most
likely to dominate an extreme-load result, and every E14 result must say so.

### 1.3 Provenance limits carried forward, not resolved

This ruling adopts a treatment; it does not upgrade the evidence. The following limits stand:

- the 2011 window's quoted wording and page numbers are **PI-supplied and were not
  independently read**; the source PDF exposes no extractable text layer;
- the 2021 window was read via an **OCR reproduction** rendering "ERCOT" as "ERGOT";
  substance is corroborated across two pages, character-level verbatim is unconfirmed;
- for 1,113 hours the source status is `NOT_RETRIEVED`, and the artifact states that no
  authoritative ERCOT event history was retrieved supporting an affirmative finding of the
  **absence** of shed;
- `distribution_outage_status` is `not_assessed` for every row.

---

## 2. What the three states mean

| State | Meaning | Inferential weight |
| --- | --- | --- |
| `verified_shed` | Directed firm load shed affirmatively documented | Served load is an **established lower bound** on latent demand |
| `unresolved` | **Censoring status unknown.** No primary-source determination either way | **None.** Carries no evidence in either direction |
| `verified_no_shed` | Affirmatively documented **absence** of directed firm shed | Would license treating served load as observed demand — **zero hours hold this state** |

Where firm load shed was directed, metered served load is not the demand that would have
materialised absent the shed. The observation is censored from below relative to latent
demand. Because the Track A primary metric is Gaussian NLL on load (freeze §7), scoring a
likelihood against a censored value as though it were uncensored **estimates a different
quantity** — served load, not latent demand.

---

## 3. The adopted treatment

### 3.1 Primary metric — `verified_shed` hours are EXCLUDED

**The 80 `verified_shed` hours are excluded from the primary latent-demand NLL.** The count
excluded must be reported **per event** in every result table.

*Basis.* These are the only hours where the record affirmatively establishes the observation
is a lower bound. Excluding them keeps the primary estimand coherent, at a cost of 80 of
1,271 hours (6.3%).

*Mandatory disclosure.* The exclusion falls disproportionately on E14 (71 of 80). Any E14
result must state that 34% of that event's hours are excluded from the primary metric.

### 3.2 `unresolved` hours — RETAINED, flagged, disclosed

**All 1,191 `unresolved` hours are retained in the primary metric, explicitly flagged**, with
the limitation disclosed wherever the primary metric is reported.

*Basis.* Retention is the option that adds no unsupported inference. Freeze §11.1 forbids
resolving unknown hours by default in either direction, and this ruling does not:

- treating `unresolved` as censored would reclassify 1,191 of 1,271 hours on an inference the
  record does not support;
- treating `unresolved` as verified-uncensored would assert exactly the finding that
  `verified_no_shed` requires, and **no hour carries that state**.

*Stated risk.* If some `unresolved` hours were in fact shed, the primary metric is contaminated
by an unknown number of censored observations. **This risk is accepted knowingly and must be
disclosed, not hidden.** It cannot be resolved from the current record. This is the weakest
point of the ruling and is recorded as such.

*Scope consequence — recorded explicitly.* `unresolved` is the majority state of the event
record and is **not** a property that distinguishes one event from another for the purpose of
selecting events to score. Under this ruling, an event is not disqualified from scoring, and is
not preferred for scoring, on the ground that its hours are `unresolved`. Event selection is
governed by the load-eligibility rule (D-006) and by the freeze, not by censoring state.

### 3.3 Secondary diagnostic — all-hours served-load NLL is REQUIRED

**An all-hours served-load NLL is required, not optional**, computed over all 1,271 hours
including `verified_shed`, with the estimand explicitly stated as **served load, not latent
demand**.

*Basis.* It is a well-defined quantity requiring no censoring inference, and it lets a reader
see how far the §3.1 exclusion moved the result. It is **diagnostic only**: it does not
adjudicate the CNP-versus-AdaCNP comparison, which freeze §7 reserves to the primary metric.

### 3.4 Censored likelihood — OPTIONAL sensitivity

**A lower-bound-aware censored Gaussian likelihood is an optional sensitivity**, implemented
only if time permits after the primary results exist.

*Basis.* It is the statistically principled treatment and would recover the 80 excluded hours,
but it applies to 6.3% of hours and requires new estimator code with its own validation.
Freeze §11.1 preserves it as an option; this ruling keeps it optional.

*If implemented,* it must be applied identically to both arms and reported **alongside, never
in place of**, the primary metric.

### 3.5 Required disclosure language

Every table, figure, and log reporting event-period results must carry, verbatim or in
substance:

> Primary metric excludes `verified_shed` hours (N per event stated). `unresolved` hours are
> retained and flagged; their censoring status is unknown and is not resolved in either
> direction. Served-load diagnostic reports a different estimand (served load, not latent
> demand).

A result reported without this disclosure is not a compliant Track A result.

---

## 4. What this ruling does not do

- It does not infer the censoring status of any hour.
- It does not resolve `unresolved` hours by default in either direction.
- It does not upgrade the provenance limits recorded in §1.3.
- It does not apply the `W-2021-0215-WIDE-v3` sensitivity envelope.
- It does not modify the experiment freeze.
- **It does not authorize freeze execution stage 4, 5, or 6.** It removes the §11.1 gate and
  nothing else. Stage-4 execution requires a separate recorded decision.
- It does not authorize any held-out-event prediction or performance inspection.

---

## 5. Application

This ruling applies to every Track A computation that evaluates a likelihood against
event-period load, from stage 4 onward. It has no effect on stage 3, which excluded every
event-period hour and has already been executed under D-008.

Implementation must be by test-asserted code, not by manual selection: the `verified_shed`
exclusion and the `unresolved` flag must be derived from
`data/frozen/track_a/v7_demand_censored_v3.csv` at run time, and no hour's censoring state may
be hard-coded.
