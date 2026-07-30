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

## D-010 — Adoption of the censoring-treatment ruling

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Task: governance pass following TRACK-A-REAL-DATA-READINESS-001

Relates to:

- `docs/track_a/EXPERIMENT_FREEZE_v1.md` §7 (primary metric), §11, §11.1 (censoring
  treatment, recorded as a hard gate on execution stage 4);
- decision D-008, which authorized stage 3 only and expressly did not adopt this ruling;
- decision D-009, which adopted the controlling harmonized load artifact;
- `docs/track_a/CENSORING_TREATMENT_RULING_v1_DRAFT.md`, the unadopted draft prepared under
  workstream 6.

Instrument:

- `docs/track_a/CENSORING_TREATMENT_RULING_v1.md` — **ADOPTED**. The draft is superseded and
  retained only as the record of the recommendation that preceded adoption.

Evidentiary basis:

- Recomputed at adoption time from the imported, hash-verified artifacts
  `v7_demand_censored_v3.csv` (`3e7bd358…`), `v7_censoring_windows_v3.csv` (`bc51b7c5…`), and
  `v7_censoring_mapping_rule_v3.md` (`2984b799…`): across 1,271 load-tier event-hours the V7
  censoring state is **80 `verified_shed`, 1,191 `unresolved`, 0 `verified_no_shed`**, with 71
  of the 80 `verified_shed` hours falling in E14 (February 2021).
- The two established shed windows are `W-2011-0202-v3` (E08, 9 hours) and `W-2021-0215-v3`
  (E14, 71 hours). `W-2021-0215-WIDE-v3` remains `NOT_APPLIED`.
- The provenance limits recorded in the artifact are carried forward unchanged and are **not**
  upgraded by this decision: PI-supplied unread quotation for the 2011 window, OCR
  reproduction for the 2021 window, `NOT_RETRIEVED` source status for 1,113 hours, and
  `distribution_outage_status` `not_assessed` for every row.

Decision — the five determinations required by freeze §11.1:

1. **`verified_shed` hours are EXCLUDED from the primary latent-demand NLL.** The number
   excluded must be reported per event in every result table. These are the only hours where
   the record affirmatively establishes that the observation is a lower bound.
2. **`unresolved` hours are RETAINED in the primary metric, explicitly flagged, with the
   limitation disclosed.** This determination is made explicitly and is not a default.
   Treating them as censored would reclassify 1,191 of 1,271 hours on an inference the record
   does not support; treating them as uncensored would assert the `verified_no_shed` finding
   that no hour carries. The residual risk — that some retained `unresolved` hour was in fact
   shed — is **accepted knowingly and must be disclosed in every affected result**.
3. **The all-hours served-load NLL diagnostic is REQUIRED, not optional.** It is computed over
   all 1,271 hours including `verified_shed`, with the estimand explicitly stated as served
   load rather than latent demand. It is diagnostic only and does not adjudicate the
   CNP-versus-AdaCNP comparison, which freeze §7 reserves to the primary metric.
4. **A censored Gaussian likelihood is an OPTIONAL sensitivity.** If implemented it must be
   applied identically to both arms and reported alongside, never in place of, the primary
   metric.
5. **Disclosure language is mandatory** in every table, figure, and log reporting event-period
   results, in the terms set out at `CENSORING_TREATMENT_RULING_v1.md` §3.5. A result reported
   without that disclosure is not a compliant Track A result.

Consequential determination:

- **Censoring state does not govern event selection.** `unresolved` is the majority state of
  the event record. Under this ruling an event is neither disqualified from scoring nor
  preferred for scoring on the ground that its hours are `unresolved`. Event selection is
  governed by the load-eligibility rule (D-006) and by the freeze. Any proposal to include or
  exclude a specific event on censoring grounds requires its own decision and must state
  evidence that distinguishes that event from the rest of the record.

Implementation requirement:

- The `verified_shed` exclusion and the `unresolved` flag must be derived at run time from
  `data/frozen/track_a/v7_demand_censored_v3.csv` and asserted by test. No hour's censoring
  state may be hard-coded, and no event count or fold count may appear as a literal (D-006,
  freeze §10.1).

Effect on the stage gates:

- **The freeze §11.1 gate on execution stage 4 is satisfied.**
- **Stage 4 is not thereby opened.** D-008 granted the real-data execution gate for stage 3
  and for no other stage. Execution of stage 4 requires a separate recorded decision extending
  that gate. Stages 5 and 6 remain blocked by their sequential gates.

Not authorized by this decision:

- freeze execution stages 4, 5, or 6, or execution of any prepared stage-4 configuration;
- held-out-event prediction;
- held-out-event performance inspection;
- any substitution, addition, or removal of an event in any run plan;
- resolution of IB-2, IB-4, IB-5, or IB-7;
- approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` as a whole;
- any change to a frozen item;
- any Track B change.

Authority and approval boundary:

- Made by Jonathan Fuentes under his present project decision authority.
- **No approval by John Brewer is claimed or implied.** Not mentor ratification, not
  institutional approval, and not the formal Data Readiness Decision. It does not amend DR-1
  or the historical Phase 1 record.

## D-011 — Stage-4 execution gate, and composition of the exploratory trio

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Relates to:

- `docs/track_a/EXPERIMENT_FREEZE_v1.md` §3 (LOEO partition, ±7-day buffer), §7 (primary
  metric), §10 (execution stages, exploratory labelling), §11.1;
- D-008, which granted the real-data execution gate for stage 3 only;
- D-010, which adopted the censoring-treatment ruling and thereby satisfied the §11.1 gate;
- `configs/track_a/exploratory_stage4_runs.yaml`, prepared under
  TRACK-A-REAL-DATA-READINESS-001 workstream 7;
- commit `7923593`, which proposed substituting E18 for E21 and marked the proposal
  `PROPOSED_PENDING_PI_DECISION`.

### Part 1 — the exploratory trio is E08, E14, E21; the E18 substitution is DECLINED

Decision:

- **The exploratory trio remains E08_20110202, E14_20210212, and E21_20260125**, as named in
  the committed `NEXT_TASK.md`. No substitution is adopted.
- **The proposed substitution of E18_20240114 for E21_20260125 is declined.**

Ground for declining, verified at decision time against
`data/frozen/track_a/v7_demand_censored_v3.csv`:

| Event | Hours | `censor_status` | `source_status` | `confidence` |
| --- | --- | --- | --- | --- |
| E18_20240114 | 83 | all `unresolved` | `NOT_RETRIEVED` | `none` |
| E21_20260125 | 78 | all `unresolved` | `RETRIEVED_VERIFIED` | `none` |

- The proposal's stated premise was that E21's censoring status is unresolvable while E18's is
  "RESOLVED but not clean". **The controlling artifact does not support this.** Both events are
  entirely `unresolved`, and E21 carries the stronger recorded provenance of the two.
- The supporting evidence cited for E18 — the OE-417 sweep, the EIA Electric Power Monthly
  Appendix B public-appeal filings, and the claim that E16 holds the strongest affirmative
  no-shed evidence — **appears nowhere in the imported record**, only in that configuration
  file's own comments. No hour in the artifact carries `verified_no_shed`.
- **D-010 moots the premise.** `unresolved` is the state of 1,191 of 1,271 event-hours,
  including every hour of E18. D-010 retains those hours in the primary metric, flagged and
  disclosed, and records that censoring state does not govern event selection. Under the
  adopted ruling E21 is scorable on exactly the same terms as E18.

Recorded so the reasoning is not lost: the proposal's deliberate rejection of E16 — the
apparently cleanest candidate — on anti-bias grounds was sound reasoning about selection bias,
and is preserved here as the correct instinct even though the substitution itself is declined.

### Part 2 — the real-data execution gate is extended to stage 4

Decision:

- **The real-data execution gate is extended to freeze execution stage 4**, the exploratory
  held-out-event experiment, and to no further stage. D-008's stage-3-only restriction is
  superseded to this extent and in no other respect.
- **Stages 5 and 6 remain blocked** by their sequential gates. Nothing here authorizes the full
  leave-one-event-out sweep, the confirmatory comparison, or any result intended as
  confirmatory.
- **Held-out-event prediction and held-out-event performance inspection are authorized for the
  three trio events only**, at the frozen seed `20260729`, for both arms.
- **Every stage-4 result is EXPLORATORY** and must be labelled so in every table, figure, and
  log (freeze §10). No stage-4 result may be reported as adjudicating the CNP-versus-AdaCNP
  hypothesis.
- **D-010 governs the metric.** `verified_shed` hours are excluded from the primary
  latent-demand NLL; `unresolved` hours are retained and flagged; the all-hours served-load NLL
  diagnostic is required; the D-010 §3.5 disclosure language is mandatory on every result.
- **The frozen structural protections continue to bind**: leave-one-event-out outer partition,
  ±7-day buffer excluded from training **and** context retrieval, issuance restricted to 09:00
  `America/Chicago` on D-1, both arms consuming byte-identical persisted context indices, and
  normalization fitted on the outer training partition only.

Rationale for granting now: the two conditions the freeze placed on stage 4 are both met —
stage 3 has passed for both arms with zero event-period hours and byte-identical context
indices, and the censoring ruling is adopted. The PI was advised that inspecting exploratory
event results cannot be undone for the purpose of later design choices, and elected to proceed.

Not authorized by this decision:

- freeze execution stages 5 and 6;
- any event outside the trio for held-out scoring;
- any seed other than `20260729` at stage 4;
- reporting any stage-4 result as confirmatory, or as adjudicating the frozen hypothesis;
- any change to the frozen design, the event inventory, or the adopted censoring ruling;
- resolution of IB-2, IB-4, IB-5, or IB-7;
- any Track B change.

Authority and approval boundary:

- Made by Jonathan Fuentes under his present project decision authority.
- **No approval by John Brewer is claimed or implied.** Not mentor ratification, not
  institutional approval, and not the formal Data Readiness Decision.

## D-012 — Temperature features and the regional temperature artifact

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Relates to:

- `docs/track_a/EXPERIMENT_FREEZE_v1.md` §3, which contemplates weather among the retrieval
  inputs, and §5 / D-007, which fix the issuance cutoff;
- D-006, which adopted `event_inventory_headline.csv` as the controlling event inventory;
- `docs/track_a/REPLICATION_FIDELITY_v1.md`, deviation **D1**;
- `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` rows 46 and 49.

### The deviation this corrects

Freeze §3 permits weather in the feature set and `NEXT_TASK.md` lists "weather input required
by the frozen Track A feature design" as import class 3. **The executed stage-3 and stage-4
pipelines had no weather features at all** — 5 calendar features plus 24 load lags — and no
decision-log entry recorded that departure, which the freeze preamble requires for any change
to a frozen item. This entry records it and corrects it.

The gap was material, not cosmetic. Track A's events are selected by a **temperature**
criterion (`peak_val`, `margin_C`), and the mechanism under test — AdaCNP's target-conditioned
similarity weighting — was being asked to find cold analogues in a feature space containing no
temperature. Freeze §7 lists "weight assigned to cold-context days" as a secondary metric,
which was uncomputable as built.

### Artifact adopted

- `regional_index.parquet`, SHA-256
  `2c88358be5390a3a9028c83a789c04d3135082b9ffd4236c8f66e2007cf8f788`, 7,019,745 bytes, is
  adopted as the **controlling Track A regional temperature artifact**. Adoption is
  content-specific, not filename-based.
- Verified byte-exact at source and destination before and after copying, and recorded in
  `docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv`.
- Columns: `regional_temp_c` (hourly regional temperature) and `roll24` (its 24-hour rolling
  mean). 276,737 rows spanning 1995-01-01 to 2026-07-27.

### Why this artifact, on evidence

**It is the definitional basis of the controlling event inventory.** Every one of the
inventory's `peak_val` entries equals this artifact's `roll24` at the corresponding `peak`
timestamp — verified for **all inventory rows, exactly**, at adoption time, and asserted by
test. Importing it therefore does not introduce a new data source into Track A; it imports the
source that the event definition adopted under D-006 already depends on.

That correspondence also settles the timezone question. The parquet index is timezone-naive.
It is read as **UTC**, on the same basis as `event_eligibility.INVENTORY_NAIVE_ZONE`: the
`peak_val` correspondence establishes that this artifact and the inventory share one
convention, and the inventory's UTC reading is independently corroborated against the
censoring artifact's explicit `ts_utc`. No adopted decision states the convention in words for
either file; this entry records the inference and the evidence for it. No fixed UTC offset is
constructed anywhere (D-007).

### Feature set adopted

Two feature sets are authorized, and **both are run**, so the contribution of the temperature
axis is measured rather than assumed:

| Set | Width | Contents |
| --- | --- | --- |
| `base` | 29 | 5 calendar + 24 load lags — the original Track A set, retained as the ablation |
| `temperature` | 57 | `base` + 24 temperature lags + `roll24` at the cutoff + heating degrees + cooling degrees + a squared term |

The four derived terms stand in for the "non-linear functions of the temperatures" that Hu et
al. list among their PJM inputs. `roll24` is included because it is the quantity the event
definition itself uses.

### Issuance discipline preserved

Every temperature feature is **past-observed only**, bounded by the same 09:00
`America/Chicago` D−1 cutoff as the load lags and enforced by the same `searchsorted` bound.
**No forecast temperature is used**, because the corpus contains no day-ahead forecast product
carrying historical issuance timestamps. Hu et al. additionally use the next day's temperature
forecast for PJM; Track A's temperature features are weaker by exactly that, and the gap is
recorded in `REPLICATION_FIDELITY_v1.md` rather than papered over.

### Cost disclosed

The temperature artifact has 6,307 null `regional_temp_c` hours and 7,010 null `roll24` hours.
A day whose temperature lag window contains a null is dropped, which costs **498 of 8,895
target days (5.6%)** in the `temperature` set. Two folds lose held-out days — E05 falls from 3
to 1, E07 from 4 to 3 — and **no fold loses all of them**. Every trio event (E08, E14, E21)
retains all its held-out days. Any E05 result must state that the fold rests on a single day.

Not authorized by this decision: use of forecast weather; import of the station-level
`ghcnh_hourly_station_qcfiltered.parquet` (identified, hash-recorded, not imported); any change
to the event inventory, the censoring ruling, or the stage gates; freeze stages 5 or 6.

## D-013 — Context-construction conditions

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Relates to: `EXPERIMENT_FREEZE_v1.md` §3–§4; `REPLICATION_FIDELITY_v1.md` deviation **D2**;
Hu et al. arXiv:2602.04609 Algorithms 1 and 2.

### The problem

Track A built every context set by **nearest-neighbour retrieval** — the 64 issuance-safe days
closest to the target in input space — and handed that same set to both arms. Hu et al. instead
**sample** the context set from the historical pool (Alg. 1 line 3, Alg. 2 line 2), with no
similarity pre-selection.

That difference cuts against the experiment's own hypothesis. AdaCNP's contribution is
target-conditioned reweighting of context points; standard CNP's claimed weakness is that
uniform averaging dilutes irrelevant context. Pre-filtering to 64 already-similar days performs
part of that relevance selection **in the data pipeline** and gives it to the CNP baseline for
free, compressing the very gap the experiment measures.

### Decision

Both conditions are authorized and **both are run**:

- **`nearest`** — the 64 issuance-safe days nearest the target in input space. Track A's
  original condition. Operationally motivated, and a deliberately strong CNP baseline.
- **`sampled`** — `context_size` days drawn uniformly without replacement from the
  issuance-safe pool under the run's frozen seed. Faithful to Hu et al.

Both conditions preserve every structural protection: they draw only from the fold's admissible
pool, so the held-out event and its ±7-day buffer can never supply a context day (freeze §3);
they respect the issuance cutoff (D-007); they are persisted and re-read per arm so the arms
provably consume byte-identical indices (Track A rules); and they read **inputs only**, so
neither can leak a target outcome.

Neither condition is designated primary. The comparison of interest is how the CNP−AdaCNP
paired difference behaves *across* the two, since that difference is the measurement the
retrieval choice was distorting.

## D-014 — Stopping rule chosen on inner validation

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Relates to: `EXPERIMENT_FREEZE_v1.md` §8, §10; `REPLICATION_FIDELITY_v1.md` deviation **D4**.

### The problem

The original stage-3 and stage-4 runs trained for a fixed **300 optimizer steps**. Hu et al.
train for roughly 1000 epochs (their Fig. 4). Measured at adoption time on E14, held-out
extreme-event NLL is **strongly non-monotone in training length**: with the `base` feature set
it *degrades* from 1.18 to 1.91 (CNP) between 300 and 1000 steps as the model fits the normal
regime harder, while the `temperature` set *improves* from 4.79 to 1.34 over the same range.

A hand-picked step count therefore makes the reported number an artifact of that choice, and
the choice moves the result by more than the effect being measured.

### Decision

- **Training length is not fixed by hand.** Each run trains up to a ceiling and the reported
  parameters are those with the best **inner-validation** NLL.
- **Inner validation is drawn from the fold's own training partition** — the latest 10% of
  training episodes, split chronologically, matching the stage-3 convention. It never touches
  the held-out event.
- **Selecting on the held-out event is prohibited.** That would be leakage and would invalidate
  the result. Inner validation is the leakage-free equivalent and is what makes the arms
  comparable to each other.
- Every run manifest records the inner-validation NLL, the selected step, and the full
  evaluation trace, so the choice is auditable rather than implicit.

### Finding recorded

Inner-validation NLL on normal periods is **weakly informative at best** about extreme-event
NLL: across the E14 grid, inner-validation values spanned 0.21–0.28 while held-out primary NLL
spanned 1.31–4.39. This is the distribution-shift problem the paper exists to address, observed
directly in Track A's own data, and it is a limitation of the stopping rule rather than a
defect in it — no leakage-free alternative selects on the extreme regime.

Not authorized: any stopping rule that inspects held-out-event performance; any change to the
frozen seeds or stage gates.

## D-015 — Stage-5 execution gate

Status: Adopted

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Relates to: `EXPERIMENT_FREEZE_v1.md` §10 (execution stages); D-011, which granted the
real-data execution gate for stage 4 only; `docs/track_a/ANALYSIS_PLAN_v1.md`;
`docs/track_a/POWER_ANALYSIS_v1.md`.

Decision:

- **The real-data execution gate is extended to freeze execution stage 5** — the full
  leave-one-event-out sweep over every load-eligible event. D-011's stage-4-only
  restriction is superseded to this extent and no further.
- **The sweep covers three frozen seeds**, so it satisfies the content of freeze stage 6
  as well. Freeze §10 gates stage 6 on "stage 5 passes **and** time permits"; running
  both in one pass is within that, and no separate stage-6 execution is authorized.
- **Scope**: all derived load-eligible folds × both arms × both feature sets (D-012) ×
  both context conditions (D-013) × the three frozen seeds. The fold count is derived at
  run time and never written as a literal (D-006, freeze §10.1).
- **Held-out-event prediction and performance inspection are authorized** for every
  load-eligible event, under the D-010 censoring treatment and the D-014 stopping rule.
- **The result is confirmatory only under D-016.** Any analysis not specified by the
  pre-registered plan is exploratory, and must be labelled so.

Conditions of execution, adopted because the sweep runs unattended:

- **Resumable.** Any run whose manifest already exists is skipped, so an interruption
  banks completed work rather than discarding it.
- **Fail-soft per fold.** A fold that cannot be built is logged to a skip register and the
  sweep continues. The register is reported alongside the results; a non-empty register
  must appear in any write-up.
- **Refuse rather than guess.** Anything not settled in advance stops that fold and is
  logged. No scientific choice is made without the PI while the PI is unavailable.
- **Serial, single process**, deliberately: available memory makes parallel sharding an
  out-of-memory risk part-way through, and reliability outweighs speed when nobody is
  watching.

Not authorized by this decision:

- any seed beyond the three frozen in freeze §8 — raising the count would amend a frozen
  item and needs its own decision;
- any change to the censoring ruling, the event inventory, the analysis plan, or any
  frozen item;
- resolution of IB-2, IB-4, IB-5, or IB-7;
- any Track B change.

Authority: made by Jonathan Fuentes under his present project decision authority. **No
approval by John Brewer is claimed or implied.**

## D-016 — Stage-5 analysis plan (pre-registration)

Status: Adopted — **pending PI ratification**

Decision authority: Jonathan Fuentes

Date: 2026-07-29

Instrument: `docs/track_a/ANALYSIS_PLAN_v1.md`, with
`scripts/analyze_stage5.py` as its executable form.

### Why this decision exists

Freeze §7 names a primary metric and stops. It specifies **no unit of analysis, no test,
no α, and no rule for judging a difference real** — "confirmatory" is defined by stage
number rather than by any criterion. Separately, D-012 and D-013 created four experimental
cells the freeze predates. `POWER_ANALYSIS_v1.md` measured the minimum detectable effect
at 0.28–0.57 paired NLL, which permits exactly one confirmatory test.

Decision:

- **The analysis plan is adopted as the pre-registered procedure for stage 5**, and is
  committed **before any stage-5 run executes**. The commit timestamp is what makes the
  result confirmatory.
- **One primary endpoint, one test**: per-event paired CNP−AdaCNP difference in held-out
  event-period Gaussian NLL under D-010, seeds averaged, in the **temperature/sampled**
  cell, by two-sided paired *t*-test at α = 0.05, with the MDE reported beside it.
- **The primary cell is chosen on fidelity to Hu et al., not on observed effect size.**
  temperature/nearest showed a marginally larger stage-4 difference (+0.59 vs +0.55) and
  was **not** chosen. This is recorded so the reasoning is auditable.
- **Everything else is descriptive** — the other three cells, the calibration metric, all
  eight freeze §7 secondaries, the served-load diagnostic. No p-values.
- **Robustness checks are predeclared and are not additional tests**: Wilcoxon signed-rank
  (disagreement with the *t*-test ⇒ report **inconclusive**, never select the favourable
  one), a sensitivity excluding folds with fewer than two held-out days, and a
  leave-one-fold-out jackknife.
- **The decision rule is fixed in advance**, including the null branch: a non-significant
  result is reported as "no detectable difference, MDE = X, Hu et al.'s margin lies below
  the MDE, so this neither confirms nor refutes the source finding" — and expressly **not**
  as a failure to replicate.
- **Fixed design.** No optional stopping, no added seeds after seeing *p*, no post-hoc
  cell reselection. Departures go in the plan's deviations register.

### Ratification

Authored on PI instruction ahead of an unattended overnight run, with the three
substantive choices — primary cell, sidedness, secondary-metric scope — confirmed by the
PI in advance. **It remains pending formal ratification.** If on review the PI would have
chosen differently, that variant is to be reported as well, clearly labelled post-hoc,
with the pre-committed version primary. The pre-registration survives either way.

Not authorized by this decision: any change to the freeze, the censoring ruling, the seed
count, or the stage gates.

## D-017 — Ratification of the stage-5 analysis plan

Status: **AWAITING PI SIGNATURE** — drafted 2026-07-30, not yet in force

Decision authority: Jonathan Fuentes Rosales

Relates to: D-016, which adopted `docs/track_a/ANALYSIS_PLAN_v1.md` and marked it *pending
PI ratification*; `docs/track_a/STAGE5_RESULTS_v1.md`; `docs/track_a/FINDINGS_v1.md`.

### What is being ratified, and what is not

D-016 was authored on PI instruction ahead of an unattended overnight run, with its three
substantive choices — primary cell, sidedness, secondary-metric scope — confirmed by the PI
in advance. It was committed at `11d3613`, **before any stage-5 run executed**. The plan
reserved formal ratification for review after the fact.

**This entry ratifies the plan as it was pre-committed. It does not, and cannot, alter it.**
The distinction matters: ratifying a pre-registration after seeing its result is only
meaningful if the ratification changes nothing. Every substantive element — the primary
endpoint, the cell, the test, the significance level, the robustness checks and the decision
rule including its null branch — is already fixed in the commit that predates the data.
Signing below confirms that those were the PI's choices; it does not re-open them.

### The result the plan produced

Applying the rule as written: **AdaCNP advantage detected on held-out ERCOT extreme events.**
Mean paired difference $+0.4593$, 95% CI $[+0.1075, +0.8111]$, two-sided paired *t*
$p = 0.0137$, Wilcoxon $p = 0.0202$ (agreeing, so the inconclusive branch did not fire),
$n = 17$ events, minimum detectable effect $0.4953$.

### Confirmations sought

By signing, the PI confirms:

1. **The primary cell** was `temperature`/`sampled`, chosen for fidelity to Hu et al. and
   **not** for observed effect size — `temperature`/`nearest` had shown a marginally larger
   exploratory difference and was deliberately not chosen.
2. **The test** was two-sided at $\alpha = 0.05$, on per-event paired differences with seeds
   averaged.
3. **All eight** freeze §7 secondary metrics were computed and are reported descriptively.
4. **The three qualifications** are reported alongside the result and not subordinated to it:
   the effect lies just below the MDE (~77% power at the realised size); the advantage appears
   only in the pre-registered cell; and the design cannot resolve the source paper's effect
   size.

### If the PI would have chosen differently

The plan provides for this. Any element the PI would have specified otherwise is to be
reported **as an additional, clearly-labelled post-hoc variant**, with the pre-committed
version remaining primary. Record any such disagreement here before signing:

> *Disagreements recorded:* ______________________________________________
>
> *(write "none" if the plan as committed reflects your intent)*

### Deviations register

The plan's deviations register (`ANALYSIS_PLAN_v1.md` §8) carries **one** entry, recorded
before the result was reported:

| Date | Deviation | Reason |
| --- | --- | --- |
| 2026-07-30 | The minimum detectable effect was initially computed as 2.36 by a routine that mishandled `scipy.stats.nct.cdf` returning NaN at large non-centrality. Corrected to 0.4953. | Implementation defect, not a change of method. The specified *procedure* — MDE at 80% power from observed spread — is unchanged; only its computation was repaired. Caught before any result was reported, verified against Monte Carlo, and covered by regression tests. Two independent implementations now agree to 0.001. |

No other departure from the plan occurred. The sweep completed 408/408 with an empty skip
register.

---

**Signature:** ____________________________  **Date:** ______________

*Jonathan Fuentes Rosales, project decision authority*

*No approval by John Brewer is claimed or implied by this entry.*
