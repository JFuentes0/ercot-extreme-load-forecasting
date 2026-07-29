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

## D-006 — Controlling event inventory

Status: Adopted

Decision authority: Jonathan Fuentes

Resolves: artifact-inventory finding IB-1
(`docs/audit/ARTIFACT_INVENTORY_001.md` §8.2)

Decision:

- `event_inventory_headline.csv` is the controlling headline event inventory.
- Track A modeling uses only those events satisfying the pre-existing
  load-eligibility rule.
- `event_inventory_S_QC1.csv` and `event_inventory_S_QC2.csv` are sensitivity
  inventories. They are retained for predeclared QC sensitivity analysis and are
  not primary fold definitions.
- The exact modeling-event count and the exact LOEO fold count must be derived
  by verifying the imported controlling artifact against the load-eligibility
  rule at run time. Neither count may be hard-coded, as either 17 or 21 or any
  other literal.
- No event timestamp, onset, recovery, duration, peak, or eligibility value is
  changed by this ruling. The artifact is adopted as-is.

Supporting observation (evidence, not part of the ruling):

- All three candidate inventories carry identical event membership, onsets, and
  peak timestamps, and identical Gate determinations. Headline and S-QC1 differ
  only in the derived `margin_C` column. S-QC2 additionally differs in two
  `peak_val` entries and in one event's recovery hour (a one-hour duration
  delta). Fold membership is therefore near-invariant across the three
  candidates, which is why this ruling is low-risk.
- The historical record states 21 detected events, of which four are pre-2002
  and weather-only, leaving 17 load-eligible. Those figures are recorded here as
  context for review; they are not the operative values. The operative values
  are whatever the imported artifact yields under the load-eligibility rule.

Not authorized by this decision: artifact import, held-out-event prediction,
held-out-event performance inspection.

## D-007 — Timezone and issuance-time conventions

Status: Adopted

Decision authority: Jonathan Fuentes

Resolves: artifact-inventory finding IB-3
(`docs/audit/ARTIFACT_INVENTORY_001.md` F-09, F-10)

Decision:

- UTC is the canonical storage, join, partition, and model-alignment axis. All
  persisted timestamps, all cross-source joins, all partition boundaries, and all
  model input and target alignment are expressed in UTC.
- `America/Chicago` is the local calendar and issuance-time reference. It is used
  for calendar features, day boundaries, and the issuance cutoff, and for nothing
  else.
- Day-ahead issuance is frozen at **09:00 America/Chicago on day D-1** for a
  target day D.
- Only information available at or before that issuance time may enter a
  target-day prediction. The most recent usable load observation is the last
  complete hour before the issuance cutoff.
- Timezone-aware conversion is mandatory throughout. Fixed UTC offsets are
  prohibited; daylight-saving transitions must be handled by a timezone database,
  not by a constant offset.
- This ruling adopts conventions for repository and Track A purposes. It does not
  approve any artifact import and does not authorize held-out-result inspection.

Relationship to the historical record:

- These conventions match what the historical record proposed but never ratified:
  the UTC join axis proposed at DRD item D5, and the 09:00 local D-1 cutoff at
  DR-1 amendment AM-5, which DR-1 itself marked provisional pending the Data
  Readiness Decision, and which `D11_Blocker_Memorandum_v1.md` lists as DP-5
  `[AWAITING RATIFICATION]`.
- This ruling is made on PI authority for the current project direction. It does
  not amend DR-1, does not constitute the Data Readiness Decision, and makes no
  claim of mentor ratification.
