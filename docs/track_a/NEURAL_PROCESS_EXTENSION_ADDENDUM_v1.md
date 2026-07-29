# Track A — Neural-Process Extension Addendum v1

**Task ID:** GOVERNANCE-EXTENSION-001
**Date:** 2026-07-29
**Applies to:** Track A only — Standard CNP versus AdaCNP
**Authorizing instrument:** `docs/project/PI_AUTHORITY_DETERMINATION_v1.md`
**Authorizing authority:** Jonathan Fuentes, final project decision authority
**Status:** Adopted

---

## 1. Scope of this addendum

This addendum governs **Track A and nothing else**.

It does not apply to Track B. It does not apply to the shared foundation. It does not
amend `Milestone1_Decision_Record_DR1.md`, `Experiment_Freeze_Register_v1.md`,
`Milestone1_Research_Specification_v0_1.md`, or any other historical artifact. Those
artifacts remain unaltered and continue to govern the frozen Phase 1 study in full.

---

## 2. The bounded exception to R-5

### 2.1 What R-5 says

Quoted exactly from `Milestone1_Decision_Record_DR1.md`, ruling R-5:

> **R-5 — No neural architectures.** Reaffirmed. The contribution is the regime-aware
> uncertainty design and its evaluation, not model complexity.

R-5 was issued by John Brewer with full authority over Phase 1, and is restated in the
Freeze Register as part of a FROZEN §10 item.

### 2.2 What this addendum does to R-5

**This addendum creates a bounded exception to R-5 that operates only within Track A.**

Stated precisely, so it cannot be read more broadly than intended:

- R-5 is **superseded within Track A only**.
- R-5 **remains fully in force within Track B**, where it continues to prohibit neural
  architectures in the Model A versus Model B experiment.
- R-5 is **not** replaced, revoked, repealed, or globally superseded.
- DR-1 is **not** replaced, amended, or superseded, globally or in part. This addendum is
  an instrument of the Track A extension; it is not a decision record of Phase 1.
- The exception is **prospective and track-scoped**. It has no retroactive effect on any
  Phase 1 ruling, artifact, result, or interpretation.

### 2.3 What is authorized

Within Track A, the following are authorized as the object of study:

- **Standard Conditional Neural Process (CNP)** using uniform mean aggregation of context
  representations;
- **Adaptive Conditional Neural Process (AdaCNP)** using target-conditioned adaptive
  weighting of the same context representations.

The intended controlled difference between the two arms is the **aggregation mechanism**.
Context-set construction, encoders, decoders, partitions, normalization, optimization, and
evaluation conditions must otherwise be paired, consistent with
`docs/track_a/CURRENT_STATUS.md`.

### 2.4 What is not authorized by this addendum

- No neural architecture is authorized in Track B, under any circumstance, by this
  addendum.
- No third architecture family, and no architecture outside the CNP/AdaCNP pair described
  above, is authorized in Track A by this addendum. Extending the Track A architecture set
  requires a further determination.
- No claim of mentor approval is created. **No prior approval by John Brewer is claimed.**
  This addendum is not evidence of mentor endorsement and may not be cited as such. Any
  future statement that Track A was mentor-approved requires separate confirmation. That
  boundary governs what may be claimed to third parties; it does not suspend or condition
  the authorization in §2.3.

---

## 3. Track B is unchanged

For the avoidance of doubt:

| Track B property | Effect of this addendum |
| --- | --- |
| R-5 architecture prohibition | **Unchanged — still prohibits neural architectures** |
| Hypotheses H1 and H2, endpoints, support rules | Unchanged |
| Model A / Model B feature classes and the §10 regime-feature list | Unchanged |
| Shared-hyperparameter and tuning protocol | Unchanged |
| Gates, guardrails, interval-width metric | Unchanged |
| Frozen scientific history and audit chain | Unchanged |
| Executability | Unchanged — Track B runs only when a task explicitly states `TRACK=B` |

Track A results may not be used to revise Track B's frozen design, consistent with
`PROJECT_CHARTER.md`. The reverse boundary also stands: Track A may not alter Track B's frozen
design.

---

## 4. Shared safeguards Track A continues to inherit

Track A inherits the shared foundation unchanged. This addendum relaxes **none** of it.

1. **ERCOT event inventory** — Track A uses the same frozen cold-event inventory as
   Track B. Neither track may independently redefine event membership.
2. **Event buffers** — ±7-day buffers around each event, per the shared partition
   specification.
3. **Leave-one-event-out outer partitions** — including exclusion of each held-out event
   and its buffer from training.
4. **Leakage protection** — no feature containing future load, post-event classification,
   test-period outcomes, or information unavailable at the issuance cutoff.
5. **Source-data provenance** — source-inventory and partition hashes must be recorded and
   verified.
6. **Censoring evidence** — the shared censoring rule, registry, and censored-demand
   artifacts apply as adjudicated for the shared foundation.
7. **Issuance-time availability** — features must respect the issuance cutoff as it is
   ultimately ratified.
8. **Held-out-event safeguards** — see §5.

**These inherited rules are referenced, not settled.** Several of them depend on questions
this addendum expressly does not answer — see §6.

---

## 5. Execution remains prohibited

This addendum authorizes an architecture family. It does **not** authorize execution.

The following remain prohibited for Track A and are unaffected by this addendum:

- implementing model or partition code;
- training models;
- generating held-out-event predictions;
- inspecting held-out-event performance.

Consistent with decision D-003, execution authority requires, at minimum: resolution of the
outstanding import blockers, a completed and hash-verified import of the authoritative
shared artifacts, and a frozen Track A protocol. None of those has occurred.

---

## 6. Questions this addendum does not answer

Recorded so that no reader treats the architecture authorization as broader clearance.

| ID | Deferred question |
| --- | --- |
| IB-1 | Which event inventory is authoritative |
| IB-2 | The unexplained gzip hash mismatch (`e4d300b3…`) |
| IB-3 | Whether the UTC join axis and the 09:00 CT D−1 issuance cutoff are adopted |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts, including the W1 weighting vector |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts |
| IB-7 | Four same-name / different-content pairs whose authoritative copy is undetermined |
| — | Approval of the proposed import manifest |
| — | Whether Track A work is later presented as part of the NETL SULI deliverable — an institutional question that does **not** condition the Track A authorization (see `PI_AUTHORITY_DETERMINATION_v1.md` §4.3) |

---

## 7. Relationship to other governing documents

| Document | Relationship |
| --- | --- |
| `docs/project/PI_AUTHORITY_DETERMINATION_v1.md` | Authorizing instrument for this addendum |
| `docs/project/DECISION_LOG.md` D-005 | Records the extension boundary |
| `docs/track_a/CURRENT_STATUS.md` | Track A operational status; unchanged by this addendum |
| `docs/shared/PARTITION_SPECIFICATION.md` | Shared partition rules Track A inherits |
| `Milestone1_Decision_Record_DR1.md` | Historical, unaltered; R-5 excepted only within Track A |
| `Experiment_Freeze_Register_v1.md` | Historical, unaltered |
| `docs/track_b/CURRENT_STATUS.md` | Unchanged |
