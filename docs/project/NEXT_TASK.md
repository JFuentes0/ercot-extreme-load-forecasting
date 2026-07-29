# Next Task

## Task ID

GOVERNANCE-EXTENSION-001

## Title

Authorize the neural-process extension without altering the frozen benchmark

## Track

PROJECT GOVERNANCE

## Objective

Prepare a formal project-authority determination and a separate Track A extension
addendum that resolves the conflict between historical DR-1 ruling R-5 and the newly
selected CNP-versus-AdaCNP research direction.

This task produces governance documents only. It imports nothing, adjudicates no other
blocker, and authorizes no modeling.

## Decision authority

Jonathan Fuentes is the final project decision authority for the current project
direction.

## Background

`docs/audit/ARTIFACT_INVENTORY_001.md` finding **IB-6** records the conflict:

- `Milestone1_Decision_Record_DR1.md` ruling **R-5 — "No neural architectures.
  Reaffirmed. The contribution is the regime-aware uncertainty design and its
  evaluation, not model complexity."**
- R-5 is restated in `Experiment_Freeze_Register_v1.md` and reaffirmed in
  `DR1_Reconciliation_Memorandum_v1.md`.
- R-5 sits inside the SHARED controlling record that `PROJECT_CHARTER.md` requires both tracks
  to inherit, and it prohibits the architecture family of the primary active track.
- `Missing_or_Unrecoverable_Artifacts_v1.md` §1 already recorded, neutrally, that the
  two cannot both proceed silently.

## Authoritative inputs

| Role | Path |
| --- | --- |
| Inventory evidence | `docs/audit/ARTIFACT_INVENTORY_001.md` |
| Project charter | `docs/project/PROJECT_CHARTER.md` |
| Decision log | `docs/project/DECISION_LOG.md` |
| Current state | `docs/project/CURRENT_STATE.md` |
| Repository rules | `PROJECT_CHARTER.md` |

Historical artifacts are **read-only reference** for this task. They may be quoted; they
may not be edited, and they are not imported by this task.

## Required interpretation

1. DR-1 ruling R-5 remains historically controlling for the original frozen Phase 1
   Model A versus Model B experiment, now identified as Track B.

2. R-5 must not be deleted, rewritten, backdated, or represented as though it never
   applied.

3. Track A is a new and formally separate extension. It may authorize neural
   architectures, specifically standard CNP and AdaCNP.

4. Track A does not retroactively alter Track B, its feature rules, hypotheses,
   architecture prohibition, or frozen scientific history.

5. Both tracks continue to inherit shared rules governing:
   - the ERCOT event inventory;
   - event buffers and leakage protection;
   - source-data provenance;
   - censoring evidence;
   - issuance-time availability;
   - partition integrity;
   - held-out-event safeguards.

6. No held-out-event model predictions or performance inspection are authorized by this
   governance task.

## Permitted edits

- `docs/project/PI_AUTHORITY_DETERMINATION_v1.md`
- `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`
- `docs/project/DECISION_LOG.md`
- `docs/project/CURRENT_STATE.md`

No other file may be created or modified.

## Forbidden actions

- do not modify DR-1 or any historical artifact;
- do not rewrite R-5;
- do not alter Track B;
- do not resolve the event-inventory, issuance-time, hash-mismatch, or import blockers
  in this task;
- do not import files;
- do not write model or partition code;
- do not train models;
- do not generate or inspect held-out-event results;
- do not modify `data/`, `artifacts/`, `runs/`, `src/`, `configs/`, or `tests/`.

## Required outputs

1. `docs/project/PI_AUTHORITY_DETERMINATION_v1.md`
2. `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`
3. One new decision-log entry recording the extension boundary.
4. An updated `CURRENT_STATE.md` identifying Track A as the separately authorized
   primary extension and Track B as the frozen historical benchmark.

## Acceptance criteria

- R-5 remains quoted or characterized accurately as a historical restriction;
- the addendum explicitly supersedes R-5 only for Track A;
- no claim is made that John Brewer approved the Track A extension;
- Jonathan Fuentes is identified as the current decision authority;
- Track B remains unchanged;
- held-out predictions remain prohibited;
- no other import blocker is silently adjudicated;
- `git diff` contains only the four permitted files.

## Blockers explicitly deferred to later bounded tasks

These remain open after this task and must not be touched here.

| ID | Deferred blocker |
| --- | --- |
| IB-1 | Authoritative event-inventory ruling |
| IB-2 | Unexplained gzip hash mismatch (`e4d300b3…`) forensics |
| IB-3 | Issuance-time and timezone convention adoption |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts |
| IB-7 | Four same-name / different-content pairs |
| — | Import-manifest approval, which follows all of the above |
