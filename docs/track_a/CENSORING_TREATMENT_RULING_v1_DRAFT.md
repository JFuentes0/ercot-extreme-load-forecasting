# Censoring Treatment Ruling — v1 **DRAFT**

> ## THIS IS A DRAFT. IT IS NOT ADOPTED.
>
> No censoring treatment is selected by this document. It has **no** entry in
> `docs/project/DECISION_LOG.md`, and it **must not be applied to any scoring**. Adoption
> requires a separate decision by Jonathan Fuentes and a new decision-log entry.
>
> Freeze §11.1 makes the adopted ruling a **hard gate on execution stage 4**. Stage 3
> (normal-period validation) proceeds without it, provided every event-period hour is
> excluded.

**Task:** TRACK-A-REAL-DATA-READINESS-001, workstream 6
**Date drafted:** 2026-07-29
**Status:** DRAFT — recommendation only
**Controlling documents:** `docs/track_a/EXPERIMENT_FREEZE_v1.md` §11.1; decision D-008

---

## 1. Evidence base

This draft rests on the imported, hash-verified artifact
`data/frozen/track_a/v7_demand_censored_v3.csv`
(SHA-256 `3e7bd358d7bb39527c367f1070b958fe2715397abd54b8275cfca30474077406`), together with
`v7_censoring_windows_v3.csv` (`bc51b7c5…`) and `v7_censoring_mapping_rule_v3.md`
(`2984b799…`). All three are members of the 13-item declared controlling set, verified
byte-exact with zero drift.

### 1.1 Counts derived from the artifact

| Measure | Value |
| --- | --- |
| Load-tier event-hours | **1,271** |
| `verified_shed` | **80** |
| `unresolved` | **1,191** |
| `verified_no_shed` | **0** |
| Load-eligible events enumerated | **derived at run time** — see note |
| Events with **no** primary-source determination | all except two |

> Counts of events and folds are deliberately **not** written as literals here, per D-006 and
> freeze §10.1. They are derived by
> `ercot_forecasting.track_a.event_eligibility.derive_eligible_events` and asserted by test.

### 1.2 The two established shed windows

| Window | Event | Status | Affected hours | Source status |
| --- | --- | --- | --- | --- |
| `W-2011-0202-v3` | E08_20110202 | `verified_shed` | 9 | URL confirmed; **quotation PI-supplied, not independently read** |
| `W-2021-0215-v3` | E14_20210212 | `verified_shed` | 71 | `RETRIEVED_VERIFIED_OCR` |
| `W-2021-0215-WIDE-v3` | E14_20210212 | **`NOT_APPLIED`** | 106 | Sensitivity envelope only |

The wide February 2021 envelope is recorded but **not applied**: EEA3 status alone does not
establish firm shed in every hour. That distinction is preserved by this draft.

**Concentration matters.** Of the 80 `verified_shed` hours, **71 fall in E14 (February 2021)**
— out of that event's 208 hours, i.e. **34%** of the most extreme event in the record are
lower-bound observations rather than observed demand. The censoring question is therefore not
evenly spread; it is concentrated in precisely the event most likely to dominate an
extreme-load result.

### 1.3 Provenance limits carried in the artifact

The artifact records its own evidentiary weaknesses, and this draft does not paper over them:

- The 2011 window's quoted wording and page numbers are **PI-supplied and were not
  independently read**; the source PDF exposes no extractable text layer.
- The 2021 window was read via an **OCR reproduction** that renders "ERCOT" as "ERGOT";
  substance is corroborated across two pages, but character-level verbatim is unconfirmed.
- For 1,113 hours the source status is `NOT_RETRIEVED`, with the artifact stating that no
  authoritative ERCOT event history was retrieved that could support an affirmative finding
  of **absence** of shed.
- `distribution_outage_status` is `not_assessed` for every row.

---

## 2. What the three states mean

| State | Meaning | Inferential weight |
| --- | --- | --- |
| `verified_shed` | Directed firm load shed affirmatively documented | Served load is an **established lower bound** on latent demand |
| `unresolved` | **Censoring status unknown.** No primary-source determination either way | **None.** Carries no evidence in either direction |
| `verified_no_shed` | Affirmatively documented **absence** of directed firm shed | Would license treating served load as observed demand — **but zero hours hold this state** |

### 2.1 Why served load may be a lower bound

Where firm load shed was directed, metered served load is not the demand that would have
materialised absent the shed. Demand was involuntarily curtailed; the meter records what was
delivered, not what was wanted. The observation is **right-censored from below** relative to
latent demand.

### 2.2 Why this bites harder for Track A than for the historical Track B design

The Track A primary metric is **Gaussian negative log likelihood on load** (freeze §7).
Evaluating a likelihood against a censored value as though it were an uncensored observation
**estimates a different quantity** — it scores the model against served load while the
reported estimand is latent demand. A likelihood-based metric forces this distinction more
sharply than the quantile-based metric of the frozen Track B benchmark did.

### 2.3 Why `unresolved` must not be defaulted in either direction

Freeze §11.1 is explicit, and this draft does not soften it:

- **Treating `unresolved` as censored** would reclassify 1,191 of 1,271 hours — the
  overwhelming majority of the event record — on an inference the record does not support.
- **Treating `unresolved` as uncensored** would assert exactly the finding that
  `verified_no_shed` requires, and **no hour currently carries that state**.

**Unknown is not the same as censored, and it is not the same as verified-uncensored.** Any
treatment that silently collapses `unresolved` into either pole is a misstatement of the
evidence, not a modelling convenience.

---

## 3. Recommended treatment — **RECOMMENDATION ONLY, NOT ADOPTED**

### 3.1 Primary metric — exclude `verified_shed`

**Exclude the 80 `verified_shed` hours from the primary latent-demand NLL.** Report the count
excluded, per event, in every result table.

*Rationale.* These are the only hours where the record affirmatively establishes that the
observation is a lower bound. Scoring a Gaussian likelihood against them measures fit to
served load while the primary metric is reported as fit to demand. Excluding them keeps the
primary estimand coherent at the cost of 80 of 1,271 hours (6.3%).

*Cost to be disclosed.* The exclusion falls disproportionately on E14 (71 of 80 hours). Any
E14 result must state that 34% of that event's hours are excluded from the primary metric.

### 3.2 `unresolved` hours — retain, flag, disclose

**Retain all 1,191 `unresolved` hours in the primary metric, explicitly flagged**, with the
limitation disclosed in every table and figure that reports the primary metric.

*Rationale.* Retention is the option that adds no unsupported inference. It does, however,
carry a real and stateable risk: if some `unresolved` hours were in fact shed, the primary
metric is contaminated by an unknown number of censored observations. That risk must be
disclosed, not hidden — it cannot be resolved from the current record.

*This is the weakest point of the recommendation and should receive the most PI scrutiny.*

### 3.3 Secondary diagnostic — all-hours served-load NLL

**Report an all-hours served-load NLL as a secondary diagnostic**, computed over all 1,271
hours including `verified_shed`, with the estimand explicitly stated as **served load, not
latent demand**.

*Rationale.* This is a well-defined quantity requiring no censoring inference, and it lets a
reader see how much the primary exclusion moved the result. It is diagnostic only and does
**not** adjudicate the CNP-versus-AdaCNP comparison (freeze §7 reserves that to the primary
metric).

### 3.4 Censored likelihood — optional sensitivity

**Treat a lower-bound-aware censored Gaussian likelihood as an optional sensitivity**, to be
implemented only if time permits after the primary results exist.

*Rationale.* A censored likelihood — using the Gaussian survival function above the served
value for `verified_shed` hours — is the statistically principled treatment and would recover
the 80 excluded hours. But it applies to 6.3% of hours, requires new estimator code and its
own validation, and would delay the primary comparison. Freeze §11.1 preserves it as an
option; this draft recommends it as a sensitivity rather than a requirement.

*If implemented, it must be applied identically to both arms and reported alongside, never in
place of, the primary metric.*

---

## 4. What this draft explicitly does not do

- It does not adopt any treatment.
- It does not infer the censoring status of any hour.
- It does not exclude any hour from any current computation.
- It does not resolve `unresolved` hours by default in either direction.
- It does not license any stage-4 execution.
- It does not modify the experiment freeze.

---

## 5. Decision required from Jonathan Fuentes

To adopt, a decision-log entry must state, on evidence:

1. the treatment of `verified_shed` hours in the primary metric;
2. the treatment of `unresolved` hours, **explicitly, without defaulting**;
3. whether the all-hours served-load diagnostic is required or optional;
4. whether a censored likelihood is required or optional;
5. the disclosure language required in every table and figure reporting event-period results.

Until that entry exists, **execution stage 4 remains blocked** and no held-out-event
likelihood may be computed or inspected.
