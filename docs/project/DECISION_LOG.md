# Decision Log

## D-001 — Dual-track organization

Status: Adopted

Decision authority: Jonathan Fuentes

Decision:

- Track A is the primary active experiment.
- Track A compares CNP with AdaCNP.
- Track B remains a frozen executable quantile-GBDT benchmark.
- Unless a task explicitly states TRACK=B, modeling requests apply to Track A.

## D-002 — Shared experimental foundation

Status: Adopted

Both tracks must use the same frozen ERCOT event inventory, outer
leave-one-event-out partitions, event buffers, source-data provenance, and
leakage protections.

## D-003 — Current setup boundary

Status: Adopted

Repository setup and protocol preparation are authorized.

Held-out-event prediction, event-performance inspection, and model training are
not yet authorized.

## D-004 — Deferred GPU environment risk

Status: Accepted, deferred

CUDA-built PyTorch is installed, but no GPU is currently visible to WSL.

GPU configuration is deferred until substantial Track A training.

This does not block setup, artifact inventory, hashing, partition work,
deterministic tests, context construction, or tiny CPU smoke tests.

## D-005 — Neural-process extension boundary

Status: Adopted

Decision authority: Jonathan Fuentes

Task: GOVERNANCE-EXTENSION-001

Resolves: artifact-inventory finding IB-6 (`docs/audit/ARTIFACT_INVENTORY_001.md` §9.1)

Instruments:

- `docs/project/PI_AUTHORITY_DETERMINATION_v1.md`
- `docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md`

Decision:

- DR-1 ruling R-5 ("No neural architectures. Reaffirmed.") remains historically
  controlling for the original frozen Phase 1 Model A versus Model B experiment,
  now designated Track B. It is preserved as written and is not deleted,
  rewritten, backdated, or invalidated.
- Track A is constituted as a new and formally separate extension, not a
  continuation or amendment of the frozen Phase 1 study.
- Within Track A only, standard CNP and AdaCNP are authorized. This operates as
  a bounded, track-scoped exception to R-5 — not a global supersession of R-5,
  and not an amendment of DR-1.
- The extension has no retroactive effect. Track B's design, hypotheses, feature
  rules, architecture prohibition, and frozen history are unchanged.
- Both tracks continue to inherit the shared event-inventory, buffer, leakage,
  provenance, censoring, issuance-time, and partition-integrity rules. None of
  those conventions is adopted or settled by this decision.
- Track A is scientifically authorized for implementation under Jonathan
  Fuentes's current project decision authority.
- No prior approval by John Brewer is claimed. This decision is made on PI
  authority over the current project direction and does not amend a mentor ruling
  inside Phase 1; the historical Phase 1 record and DR-1 remain unchanged.
- Any future statement that Track A was mentor-approved, and any institutional
  submission that independently requires mentor sign-off, requires separate
  confirmation. That institutional-approval boundary does not suspend or
  condition the Track A authorization established here.

Not authorized by this decision:

- model or partition implementation;
- model training;
- held-out-event prediction;
- held-out-event performance inspection;
- artifact import, or approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv`.

Expressly not adjudicated: IB-1, IB-2, IB-3, IB-4, IB-5, IB-7. Only IB-6 is
resolved.
