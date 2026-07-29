# Track A — Experiment Freeze v1

**Track:** A — Standard CNP versus AdaCNP
**Date:** 2026-07-29
**Decision authority:** Jonathan Fuentes
**Authorized by:** `docs/project/PI_AUTHORITY_DETERMINATION_v1.md` and
`docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md` (decision D-005)
**Status:** Drafted — frozen on commit

Everything in §§1–9 is **FROZEN**. Changing any frozen item after this document is
committed requires a new decision-log entry stating the reason, whether any held-out-event
result had been inspected at the time of the change, and the expected interpretive effect.

---

## 1. Primary comparison

| Arm | Aggregation |
| --- | --- |
| **CNP** | Uniform mean aggregation over context representations |
| **AdaCNP** | Target-conditioned adaptive weighting of the same context representations |

**The aggregation mechanism is the intended and only model difference.**

## 2. Controlled comparison

Both arms must use identical:

- data;
- partitions;
- context candidate pools;
- context encoder and target encoder;
- decoder;
- normalization statistics and procedure;
- optimizer, learning rate, schedule, batch size, and stopping rule;
- seeds.

Any difference between the arms other than aggregation is a defect, not a design choice.

## 3. Episode definition

- One episode targets **one target day**.
- The target output is a **24-hour load vector** for that day.
- **All context days must precede the target issuance time** defined in §5.
- The held-out event and its **±7-day buffer** are excluded from both training **and**
  context retrieval.
- Retrieval may use target **inputs `x`** (calendar, weather, issuance-time-available
  features). Retrieval may **never** use target **outcomes `y`**.

## 4. Context

| Setting | Value |
| --- | --- |
| Headline context size | **64** |
| Sensitivity context size | **32** |

**Identical saved context sets must be supplied to both models.** Context selection is
performed once per episode and persisted; both arms consume the same persisted set. Neither
arm may re-select or re-order context.

## 5. Time and issuance conventions

Inherited from decision **D-007**, frozen here for Track A:

- UTC is the canonical storage, join, partition, and model-alignment axis.
- `America/Chicago` is the local calendar and issuance-time reference.
- Day-ahead issuance is **09:00 America/Chicago on D-1**.
- Only information available at or before that issuance time may enter a target-day
  prediction.
- Timezone-aware conversion is mandatory; fixed UTC offsets are prohibited.

## 6. Output

- **24 Gaussian means.**
- **24 positive Gaussian scales.**
- Scale is produced by **softplus plus a small numerical floor**. The floor is a frozen
  constant recorded in configuration, not tuned.
- Probabilistic intervals are **derived from the Gaussian output**, not modeled separately.

## 7. Metrics

**Primary metric**

- Held-out event-period **Gaussian negative log likelihood**.

**Key calibration metric**

- **|empirical 90% coverage − 0.90|** over held-out event periods.

**Secondary metrics**

- CRPS;
- RMSE;
- MAE;
- 90% interval width;
- high-load exceedance behavior;
- AdaCNP weight entropy;
- effective context count;
- weight assigned to cold-context days.

Secondary metrics are reported for interpretation. They do not adjudicate the comparison.

## 8. Seeds

```
20260729
20260730
20260731
```

Frozen. Both arms use the same three seeds in the same order.

## 9. Required validation

Every item must pass before the corresponding execution stage is considered complete.

1. Adaptive weights sum to one.
2. Predicted scales are strictly positive.
3. CNP output shapes are correct.
4. AdaCNP output shapes are correct.
5. **Uniform AdaCNP weighting reproduces CNP aggregation numerically**, within a recorded
   tolerance.
6. Target `y` cannot influence context retrieval.
7. A fixed seed reproduces the same smoke result.
8. Each model can overfit a tiny synthetic fixture.
9. A target-shuffle ablation is supported.

Item 5 is the load-bearing test of the design: if uniform-weight AdaCNP does not reduce to
CNP, the two arms differ in more than the aggregation mechanism and §2 is violated.

---

## 10. Execution stages

Stages are sequential. No stage may begin before the previous one passes.

| # | Stage | Data | Gate to enter |
| --- | --- | --- | --- |
| 1 | Synthetic unit tests | Synthetic only | This freeze committed |
| 2 | Synthetic CPU smoke training | Synthetic only | Stage 1 passes |
| 3 | Normal-period validation | Real, **non-event periods only** | Real-data execution gate approved. Event-period hours must be excluded from this validation — see §11.1 |
| 4 | Three-event exploratory run, one seed | Real | Stage 3 passes **and** the censoring-treatment ruling is adopted (§11.1) |
| 5 | Full load-eligible LOEO, one seed | Real | Stage 4 passes |
| 6 | Full load-eligible LOEO, three seeds | Real | Stage 5 passes **and** time permits |

**Stages 1 and 2 are authorized now.** Stages 3–6 are not.

Stage 4 results are **exploratory** and must be labeled as such in every table and figure.

### 10.1 Fold count is derived, never hard-coded

Per decision **D-006**, the number of full LOEO folds must be **derived at run time** from
the authoritative inventory after applying the load-eligibility rule. It must not appear as
a literal — not 17, not 21, not any other constant — in code, configuration, tests, or
reports. A test must assert that the derived fold count equals the number of load-eligible
events found in the imported artifact.

---

## 11. Open items that gate the real-data stages

These do **not** block stages 1–2. Each is recorded here with the stage it gates, so the
freeze is not mistaken for readiness.

| Item | Gates from | Note |
| --- | --- | --- |
| Minimum verified Track A data import | Stage 3 | No real artifact is in the repository |
| Real-data execution gate | Stage 3 | Not yet requested or approved |
| **Censoring treatment of the target series** | **Stage 4** | Stage 3 may proceed without it, subject to §11.1 |
| IB-2, IB-4, IB-5, IB-7 | Stage 3 | Deferred; see `CURRENT_STATE.md` |

### 11.1 Censoring treatment — required before held-out-event scoring

#### Execution gate

- **Stages 1–2 (synthetic): not required.** No real target series is involved.
- **Stage 3 (normal-period validation): not required**, provided **event-period hours are
  excluded from that validation**. Stage 3 scores non-event periods only, where the
  censoring question does not arise.
- **Stage 4 and beyond: mandatory.** The censoring-treatment ruling must be adopted before
  the first exploratory held-out-event scoring. Stage 4 is the first stage at which a
  likelihood is evaluated against event-period load.

#### Observed state of the record

`Mentor_Decision_Sheet_v5.md` records that across the 1,271 load-tier event-hours the V7
censoring state is **80 `verified_shed`, 1,191 `unresolved`, 0 `verified_no_shed`**, and
that **15 of 17 load-eligible events have no primary-source censoring determination**. Of
the 80 `verified_shed` hours, 71 fall in the February 2021 event, which the same document
describes as "71 of the 208 hours (34%) ... are lower-bound observations, not observed
demand."

#### What the states mean

| State | Meaning |
| --- | --- |
| `verified_shed` | Directed firm load shed is affirmatively documented. **Served load is an established lower bound on latent demand** for that hour. |
| `unresolved` | **The censoring status is unknown.** No primary-source determination exists either way. |
| `verified_no_shed` | Affirmatively documented absence of directed firm load shed. **Zero hours currently carry this state.** |

**`unresolved` must not be automatically treated as censored, and must not be automatically
excluded.** Unknown is not the same as censored. Treating 1,191 unknown hours as censored
would discard most of the event record on an inference the record does not support;
treating them as verified-uncensored would assert a finding that `verified_no_shed`
explicitly requires and that no hour currently has.

#### Why this matters for Track A specifically

The primary metric is Gaussian NLL on load. Where served load is a lower bound on latent
demand, scoring a likelihood against it as though it were an observation estimates a
different quantity. This is forced more sharply by a likelihood-based primary metric than it
was by a quantile-based one.

#### Options preserved — none selected

**No censoring-treatment option is selected by this authoring pass.** This freeze does not
infer censoring status, does not choose a treatment, and does not exclude any hour. The
ruling required before stage 4 must select among, or explicitly extend, the following:

1. **Exclude `verified_shed` hours from the primary metric**, reporting them separately.
2. **Use a lower-bound-aware censored likelihood** for `verified_shed` hours.
3. **Retain them under an explicitly served-load interpretation**, with the estimand stated
   as served load rather than latent demand, and the limitation disclosed in every result.

The ruling must also state its treatment of `unresolved` hours, on evidence, and must not
resolve them by default.

---

## 12. Prohibitions in force

- No held-out-event prediction until this freeze is committed **and** the real-data
  execution gate is separately approved.
- No held-out-event performance inspection under the same condition.
- No inspection of stage 4–6 results before the stage's entry gate is passed.
- No change to any frozen item without a decision-log entry per the preamble.
- No Track B modification. Track A results may not revise Track B's frozen design.

---

## 13. Related documents

| Document | Role |
| --- | --- |
| `docs/project/PI_AUTHORITY_DETERMINATION_v1.md` | Authorizes Track A |
| `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md` | Scopes the R-5 exception to Track A |
| `docs/project/DECISION_LOG.md` D-005 / D-006 / D-007 | Extension boundary; controlling inventory; time conventions |
| `docs/shared/PARTITION_SPECIFICATION.md` | Shared LOEO and buffer rules |
| `docs/audit/ARTIFACT_INVENTORY_001.md` | Evidence base and open blockers |
| `docs/track_a/CURRENT_STATUS.md` | Track A operational status |
