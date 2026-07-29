# PI Authority Determination v1

**Task ID:** GOVERNANCE-EXTENSION-001
**Date:** 2026-07-29
**Determining authority:** Jonathan Fuentes, final project decision authority for the
current project direction.
**Subject:** Resolution of inventory finding **IB-6** — the conflict between historical
DR-1 ruling R-5 and the CNP-versus-AdaCNP research direction.
**Companion document:** `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`

This determination is a governance instrument. It imports no artifact, adjudicates no
other import blocker, authorizes no modeling, and modifies no historical record.

---

## 1. The conflict being resolved

`docs/audit/ARTIFACT_INVENTORY_001.md` §9.1 recorded finding IB-6: a standing prohibition
in the historical controlling record forbids the architecture family selected for the
current primary track.

The prohibition, quoted exactly from `Milestone1_Decision_Record_DR1.md`:

> **R-5 — No neural architectures.** Reaffirmed. The contribution is the regime-aware
> uncertainty design and its evaluation, not model complexity.

R-5 is restated in `Experiment_Freeze_Register_v1.md` as part of a **FROZEN (§10)** item
("**No neural architectures.**") and confirmed as discharged in
`DR1_Reconciliation_Memorandum_v1.md`.

`Missing_or_Unrecoverable_Artifacts_v1.md` §1 raised this neutrally at migration time,
observing that CNP and AdaCNP are ordinarily neural architectures, that R-5 is a standing
prohibition, and that the two "cannot both proceed silently."

---

## 2. Findings of fact

These are observations from the historical record, not decisions.

1. **DR-1 was issued by the mentor.** `Milestone1_Decision_Record_DR1.md` states:
   "**Issued by:** John Brewer. These rulings are made with full authority." R-5 is one of
   those rulings.

2. **DR-1 freezes Phase 1.** The same document states its effect: "Specification v0.1
   together with this Decision Record constitutes Working Specification v1.0 — Frozen for
   Phase 1."

3. **R-5's subject matter is the Model A versus Model B experiment.** The Freeze Register
   places "No neural architectures" inside the §10 frozen item that defines the core
   experiment as "**Model A vs Model B** as specified above," with sanity baselines and at
   most one calibration extension.

4. **The historical record contains no Track A material.** Both
   `Project_Migration_Manifest_v1.md` and `Missing_or_Unrecoverable_Artifacts_v1.md`
   record a zero-match content search for `Track A`, `Track B`, `CNP`, and `AdaCNP`. The
   artifact inventory independently confirmed this. Track A did not exist when R-5 was
   issued, and R-5 was not written in contemplation of it.

5. **Model A / Model B is Track B.** The inventory established the naming correspondence
   from `Milestone1_Research_Specification_v0_1.md`: Model A is the regime-agnostic
   quantile-gradient-boosting model, Model B the regime-aware variant, sharing a quantile
   gradient boosting backbone. That experiment is the object R-5 governs.

---

## 3. Determination

**D-1. R-5 remains historically controlling for Track B.**
Ruling R-5 stands, unaltered, as issued. Within the original frozen Phase 1 Model A versus
Model B experiment — now designated Track B — neural architectures remain prohibited. No
part of this determination weakens, narrows, or retires that prohibition inside Track B.

**D-2. R-5 is preserved as written.**
R-5 is not deleted, rewritten, backdated, reinterpreted, or represented as having been
inapplicable at any time. `Milestone1_Decision_Record_DR1.md`,
`Experiment_Freeze_Register_v1.md`, and `DR1_Reconciliation_Memorandum_v1.md` are historical
artifacts and remain byte-unchanged. Any future import of those artifacts must carry R-5
intact.

**D-3. Track A is a new and formally separate extension.**
Track A — Standard CNP versus AdaCNP — is constituted as a separate experiment, authorized
under the present project direction. It is not a continuation, amendment, revision, or
successor of the frozen Phase 1 study. It is a distinct experiment that reuses the shared
data foundation.

**D-4. Track A may use neural architectures.**
Within Track A, and only within Track A, standard Conditional Neural Processes and Adaptive
Conditional Neural Processes are authorized. The mechanism by which this authorization
operates is a bounded exception to R-5 scoped to Track A, set out in
`docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`.

**D-5. The extension is non-retroactive.**
Track A does not alter Track B's hypotheses, endpoints, feature rules, tuning protocol,
architecture prohibition, gates, or frozen scientific history. Track B's results, if and
when produced, are interpreted under the frozen Phase 1 design alone. Track A results may
not be used to revise Track B's design.

**D-6. Shared safeguards continue to apply to both tracks.**
Both tracks continue to inherit, unchanged, the shared rules governing the ERCOT event
inventory, event buffers and leakage protection, source-data provenance, censoring
evidence, issuance-time availability, partition integrity, and held-out-event safeguards.
This determination adopts none of those conventions and settles none of the open questions
about them; it only confirms that they are not displaced by the extension.

**D-7. No modeling is authorized.**
This determination authorizes an architecture family for a track. It does not authorize
implementation, training, held-out-event prediction, or held-out-event performance
inspection. Those remain barred by D-003 and by the Track A protocol freeze, which has not
occurred.

---

## 4. Scope and limits of this determination

Recorded so the authority basis cannot later be misread.

**4.1 What authority is being exercised.** Jonathan Fuentes is the final decision authority
for the current project direction and for this repository. That authority is sufficient to
define the scope of a new experiment, to constitute Track A as separate from the frozen
Phase 1 study, and to authorize an architecture family within that new experiment.

**4.2 What authority is not being exercised, and not claimed.**

- **This determination does not amend DR-1.** DR-1 was issued by John Brewer with full
  authority over Phase 1. Amending a mentor ruling inside the frozen study is not within
  the scope of this determination and is not attempted.
- **No prior approval by John Brewer is claimed.** Nothing in this document, the companion
  addendum, or the decision log may be cited as mentor endorsement of the Track A
  extension or of CNP or AdaCNP work.
- **This determination does not decide how Track A relates to the NETL SULI deliverable.**
  Whether Track A work is later presented as part of that program's output is a separate
  institutional question. It is recorded here as open and is not adjudicated, and it does
  not bear on whether Track A is scientifically authorized — which it is.

**4.3 Effect of 4.2 on Track A's standing.**

Track A is **scientifically authorized for implementation** under Jonathan Fuentes's
current project decision authority.

This determination does not claim prior approval by John Brewer and does not amend the
historical Phase 1 record. DR-1 and the Phase 1 artifacts remain unchanged. Any future
statement that Track A was mentor-approved, and any institutional submission that
independently requires mentor sign-off, requires separate confirmation.

**That institutional-approval boundary does not suspend or condition the Track A
authorization established by this determination.** It is a statement about what may be
claimed to third parties, not a precondition on the science.

The only gates remaining on Track A implementation are this project's own sequencing gates
— the outstanding import blockers in §5, and the Track A protocol freeze — recorded at D-7
above and in §5 of the companion addendum. Those are unchanged by this section.

---

## 5. Import blockers expressly NOT adjudicated

This determination resolves **IB-6 only**. The following remain open and are untouched.

| ID | Blocker | Status after this determination |
| --- | --- | --- |
| IB-1 | Authoritative event inventory not uniquely ratified | **Open** |
| IB-2 | Unexplained gzip hash mismatch (`e4d300b3…`) | **Open** |
| IB-3 | Timezone (UTC join axis) and issuance-cutoff conventions unratified | **Open** |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts | **Open** |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts | **Open** |
| IB-6 | R-5 versus Track A architecture conflict | **RESOLVED by this determination** |
| IB-7 | Four same-name / different-content pairs | **Open** |
| — | Approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` | **Not approved** |

No artifact was imported by this task.

---

## 6. Status

**Status:** Adopted.
**Recorded in:** `docs/project/DECISION_LOG.md` entry D-005.
**Operative instrument:** `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`.
