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

## D-008 — Track A real-data execution gate, stage 3 only

Status: Adopted

Decision authority: Jonathan Fuentes

Task: TRACK-A-REAL-DATA-READINESS-001

Relates to: `docs/track_a/EXPERIMENT_FREEZE_v1.md` §10 (execution stages), §11
(open items gating the real-data stages), §11.1 (censoring treatment)

Decision:

- **Verified real data may be used for freeze execution stage 3.** The real-data
  execution gate, which freeze §11 recorded as "Not yet requested or approved",
  is granted for stage 3 and for no other stage.
- **Stage 3 is restricted to non-event periods.** It is normal-period validation
  only.
- **Every event-period hour must be excluded from stage-3 training, validation,
  and scoring.** This exclusion is what permits stage 3 to proceed before the
  censoring-treatment ruling exists, per freeze §11.1, which requires that
  ruling only from stage 4 onward. Exclusion must be enforced and demonstrated
  by test, not by inspection.
- **This does not authorize exploratory or full held-out-event scoring.** No
  held-out-event prediction and no held-out-event performance inspection is
  authorized by this decision.
- **Stage 4 remains blocked** pending adoption of the censoring-treatment ruling
  required by freeze §11.1. A draft of that ruling may be prepared under
  TRACK-A-REAL-DATA-READINESS-001; a draft is not an adoption, and adoption
  requires a separate decision-log entry. Stages 5 and 6 likewise remain blocked.
- **Imports are limited to the artifacts approved through
  TRACK-A-REAL-DATA-READINESS-001**, each identified by exact source path,
  source SHA-256, destination path, destination SHA-256, purpose, governing
  status, and governing decision before it is copied. Identification precedes
  copying; a filename is not an identification.
  `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` remains non-authoritative and is
  not approved as a whole by this decision.
- **IB-2, IB-4, IB-5, and IB-7 are avoided by exclusion and remain unresolved.**
  Freeze §11 lists them as gating stage 3. This decision does not adjudicate any
  of them. The minimal Track A import set is scoped so that no artifact touched
  by those findings is imported. If a required artifact proves entangled with
  one of them, the task must stop and report rather than resolve it.
- **No mentor approval is claimed.** This decision is made on Jonathan Fuentes's
  current project decision authority. It does not amend DR-1, does not
  constitute the Data Readiness Decision, and makes no claim of mentor
  ratification. Any institutional submission independently requiring mentor
  sign-off requires separate confirmation.
- **Track B is unaffected.** Its frozen design, hypotheses, feature rules,
  architecture prohibition, and history are unchanged, and no Track A result may
  revise them.

Not authorized by this decision:

- held-out-event prediction;
- held-out-event performance inspection;
- freeze execution stages 4, 5, and 6;
- adoption of the censoring-treatment ruling;
- approval of the proposed import manifest as a whole;
- resolution of IB-2, IB-4, IB-5, or IB-7;
- any change to a frozen item.

Supporting note (context, not part of the ruling):

- A `[build-system]` addition to `pyproject.toml` is authorized under
  TRACK-A-REAL-DATA-READINESS-001 workstream 1. It is packaging infrastructure
  only, carries no scientific effect, and does not widen the scope granted here.

## D-009 — Controlling Track A load artifact and bounded IB-2 disposition

Status: Adopted

Decision authority: Jonathan Fuentes

Task: TRACK-A-REAL-DATA-READINESS-001

Relates to:

- `docs/audit/ARTIFACT_INVENTORY_001.md`, findings F-06, F-07, and IB-2;
- decisions D-005 through D-008;
- `docs/project/NEXT_TASK.md`, workstreams 2 through 5;
- the read-only Track A Import Evidence Checkpoint dated 2026-07-29;
- `docs/track_a/EXPERIMENT_FREEZE_v1.md` §§10, 11, 11.1.

Decision:

- **The clean harmonized ERCOT load artifact is adopted for Track A.** For Track A
  only, `ercot_hourly_load_harmonized.csv` with SHA-256
  `272af17cd1b2df14b921756738c6625b22c7702a6d14139886c3ff32728689eb` is adopted as
  the controlling harmonized ERCOT load artifact.
- **The adoption is content-specific, not filename-based.** It applies only to a
  source file whose complete SHA-256 exactly matches the digest above and whose
  observed size is 54,688,032 bytes. Any file with a different digest is not
  adopted by this decision, regardless of its filename or location.
- **The stale CSV content is explicitly excluded.**
  `ercot_hourly_load_harmonized.csv` with SHA-256
  `9f1817f78d1bb56ad3c5ea08b95b83e235616bd90ff85809182841f36f09bb35` is the
  documented stale pre-CC-8 delivery identified by finding F-06, produced without
  the `pre_apr2003_restated` column. It is not a controlling Track A artifact and
  must not be imported, substituted for the adopted content, used for training or
  validation, or treated as an equivalent copy. It remains in its existing location
  as historical provenance evidence and must not be modified, moved, renamed,
  copied into the repository, or deleted under this decision.
- **The unexplained gzip content is governance-quarantined.**
  `ercot_hourly_load_harmonized.csv.gz` with SHA-256
  `e4d300b36fdbd56a8e86e660b9770ad5888e348e62a2ae136ddb5ad7ff55579e` remains
  unexplained. It is excluded from all Track A import, interpretation, training,
  validation, and evaluation. It must remain in its current location and must not
  be modified, decompressed, parsed, opened for content comparison, moved, renamed,
  copied into the repository, or deleted.
- **Metadata-only provenance checks remain permitted** — `stat`, `file`,
  `sha256sum`, and equivalents — when needed to confirm the quarantined file's
  identity and unchanged state, and only where they do not inspect or transform its
  contents.
- **No inference is adopted** concerning the gzip file's decompressed contents or
  its relationship to either CSV version.
- **IB-2 receives a bounded Track A disposition.** This decision resolves the effect
  of IB-2 on selection of the controlling Track A load artifact by adopting the
  `272af17c…` content, excluding the `9f1817f7…` content, and
  governance-quarantining the `e4d300b3…` content. **This is not a finding that the
  unexplained gzip discrepancy has been resolved.** IB-2 remains open as a
  provenance issue concerning the identity and history of the `e4d300b3…` content.
  It no longer blocks the Track A stage-3 path, because that content is explicitly
  excluded and quarantined while the controlling artifact is identified
  independently by the complete digest stated here.

Evidentiary basis:

- `ARTIFACT_INVENTORY_001.md` records the clean CSV at 54,688,032 bytes, matching
  prior recorded hash evidence across six independent sources, present in multiple
  source locations, and carrying no direct blocking flag.
- Finding F-06 identifies `9f1817f7…` as stale pre-CC-8 content produced without the
  `pre_apr2003_restated` column.
- Finding F-07 establishes that `e4d300b3…` does not match the recorded gzip digest,
  remains unexplained by the available corpus, and was not decompressed.
- The read-only Track A Import Evidence Checkpoint reports that the relevant source
  hashes were independently re-verified, that no harmonized load artifact had been
  copied into the repository, and that the repository remained byte-for-byte
  unchanged during that checkpoint.
- D-008 requires exact artifact identification before copying, and requires the task
  to stop rather than import an artifact whose governing status remains unresolved.

This evidence establishes the identity and provenance basis for the bounded Track A
selection made here. It does not establish the contents of the quarantined gzip file
and does not authorize an investigation of those contents.

Authority and approval boundary:

- Made by Jonathan Fuentes under his present project decision authority.
- **No approval by John Brewer is claimed or implied.**
- Not mentor ratification; does not amend any historical mentor ruling, DR-1, or the
  historical Phase 1 record.
- Not institutional approval, and not the formal Data Readiness Decision.
- Any submission or action independently requiring mentor or institutional approval
  remains subject to that separate requirement. Project authority, mentor approval,
  and institutional approval remain distinct.

Execution authorized after adoption:

- Resumption of TRACK-A-REAL-DATA-READINESS-001 at the stopped load-artifact portion
  of workstream 2, and nothing else.
- Reading and hashing a source copy of the adopted clean content before copying,
  verifying both the complete digest and the observed 54,688,032-byte size.
- Copying only content whose complete SHA-256 exactly equals
  `272af17cd1b2df14b921756738c6625b22c7702a6d14139886c3ff32728689eb`.
- Computing and verifying the destination SHA-256 after copying.
- Subsequently adding or updating the corresponding row in
  `docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv` so it records the complete digest,
  source and destination paths, independently computed source and destination
  hashes, their equality, the artifact purpose, governing status, **D-009** as the
  governing decision, and the required IB-2, IB-4, IB-5, and IB-7 blocker check.
- Completion of remaining minimal-import work only for artifacts independently
  identified, hash-verified, governed, and permitted by the existing task.
- Progression to workstreams 3 and 4 only after the complete minimal import
  satisfies all manifest, blocker-check, and acceptance requirements in
  `NEXT_TASK.md`.

**D-009 does not itself authorize immediate stage-3 execution.** It removes the
bounded load-artifact selection blocker and authorizes resumption of workstream 2.
D-008 remains the stage-3 authority. Stage 3 may begin only after every import,
data-validation, partition, issuance-time, leakage, and acceptance prerequisite
imposed by D-008, `NEXT_TASK.md`, and the experiment freeze has been satisfied and
documented. Any eventual stage-3 execution remains restricted to normal, non-event
periods; every event-period hour must be excluded from stage-3 training, validation,
and scoring, and that exclusion must be enforced and demonstrated **by test**, not
assumed or established by manual inspection.

Not authorized by this decision:

- importing, copying, decompressing, parsing, or inspecting the contents of the
  `e4d300b3…` gzip artifact;
- importing or using the stale `9f1817f7…` CSV content;
- selecting any artifact based only on its filename;
- treating the current uncommitted import manifest as the authority for this
  decision;
- import of any artifact entangled with IB-4, IB-5, or IB-7 without a separate
  adopted decision;
- approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` as a whole;
- any change to the frozen Track A experimental design;
- adoption or application of the censoring-treatment ruling;
- freeze execution stages 4, 5, or 6, or execution of any prepared stage-4
  configuration;
- held-out-event prediction;
- held-out-event performance inspection;
- generation or inspection of any metric, table, figure, log, or artifact reporting
  event-period model performance;
- use of any event-period hour in stage-3 training, validation, or scoring;
- any Track B change;
- package installation;
- modification of any source artifact outside the repository;
- a repository commit without separate PI approval.

Stage 4 remains blocked until stage 3 passes **and** the censoring-treatment ruling
required by freeze §11.1 is separately adopted through a recorded PI decision.
Stages 5 and 6 remain blocked by their sequential gates. Track B remains unaffected:
its frozen design, hypotheses, feature rules, architecture prohibition, and
historical record are unchanged.
