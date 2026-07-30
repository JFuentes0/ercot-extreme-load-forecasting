# Current State

## Primary active track

Track A — Standard CNP versus AdaCNP.

Track A is a **separately authorized extension**, constituted under
`docs/project/PI_AUTHORITY_DETERMINATION_v1.md` and governed by
`docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md` (decision D-005).

Standard CNP and AdaCNP are authorized within Track A only, as a bounded exception to
historical ruling R-5. Authorization is by Jonathan Fuentes as project decision authority.
No prior approval by John Brewer is claimed.

## Secondary frozen track

Track B — quantile GBDT Model A versus Model B.

Track B is the **frozen historical benchmark**. Its design is preserved unchanged, including
DR-1 ruling R-5, which continues to prohibit neural architectures within Track B. Track B is
executable on explicit request but is not the default development priority, and it runs only
when a task explicitly states `TRACK=B`.

## Current stage

Synthetic scaffold complete. Track A experiment freeze committed. **Minimal verified import
complete; execution stages 3 and 4 both executed for both arms.** The censoring-treatment
ruling is **adopted** (D-010) and applied. The stage-4 exploratory experiment is **executed**
under D-011. Stages 5 and 6 remain **blocked**.

The Track A synthetic scaffold (`TRACK-A-SCAFFOLD-001`) is implemented and committed: nine
modules, 21 passing tests, CPU-only, synthetic fixtures only. Scaffold trainable parameter
counts were CNP 110,512 and AdaCNP 123,569, with an identical shared encoder/decoder backbone.

**Real-data import** — the controlling load artifact (D-009), the controlling headline event
inventory (D-006), the three V7 censoring artifacts, and the regional temperature index
(D-012), each hash-verified at source and destination and recorded in
`docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv`. No artifact outside that set has been imported.

`regional_index.parquet` is the **definitional basis of the controlling event inventory**:
every inventory `peak_val` equals its `roll24` at the corresponding `peak` timestamp, verified
for all inventory rows and asserted by test. Importing it added no new data source; it imported
the source the frozen event definition already depended on.

**Stage 3 has been executed** for both arms at seed `20260729` under D-008, with zero
event-period hours in any batch and byte-identical context-index files consumed by both arms.
Run manifests are at `runs/track_a/stage3/`. Real-data trainable parameter counts are
CNP 115,888 and AdaCNP 130,289.

**Stage 4 has been executed** under D-011, as a factorial over the replication-fidelity axes
identified in `docs/track_a/REPLICATION_FIDELITY_v1.md`: events E08/E14/E21 × arms CNP/AdaCNP
× feature set (base, temperature) × context condition (nearest, sampled) × all three frozen
seeds, with the D-010 censoring treatment applied throughout. Run manifests are at
`runs/track_a/stage4/`; results are reported in
`docs/track_a/STAGE4_EXPLORATORY_RESULTS_v1.md`. **Every stage-4 result is exploratory and
adjudicates nothing**; the confirmatory comparison is stages 5 and 6, which remain blocked.

**A leakage defect found and fixed 2026-07-29.** The first stage-4 execution computed the
episode lag span from the target day's first hour instead of from the issuance cutoff — two
instants ~15 hours apart — so the ±7-day buffer under-excluded and 11 of 17 folds admitted one
training day each whose lag features reached into the buffered window. Both originally executed
folds were affected. **No event-window hour leaked**, so the scientific impact was small, but
the guarding test hard-coded the same wrong constant and so could not fail. Both are fixed;
`stage4.episode_lag_start` now derives the span from `issuance_cutoff_utc`, and
`tests/shared/test_frozen_constants.py` carries a regression guard that recomputes the
expectation from the load axis.

## Governance decisions in force

| ID | Decision |
| --- | --- |
| D-005 | Neural-process extension boundary — resolves IB-6 |
| D-006 | `event_inventory_headline.csv` is the controlling event inventory — resolves IB-1 |
| D-007 | UTC canonical axis; `America/Chicago` calendar; 09:00 CT D-1 issuance — resolves IB-3 |
| D-008 | Track A real-data execution gate, **stage 3 only** — normal-period validation |
| D-009 | Controlling Track A load artifact; bounded IB-2 disposition |
| D-010 | Censoring-treatment ruling **adopted** — satisfies the freeze §11.1 stage-4 gate |
| D-011 | Stage-4 execution gate granted; exploratory trio confirmed as E08/E14/E21 |
| D-012 | Temperature features adopted; `regional_index.parquet` imported as controlling |
| D-013 | Context-construction conditions — nearest-neighbour **and** paper-faithful sampling |
| D-014 | Stopping rule chosen on inner validation, never on the held-out event |

## Track A load artifact (D-009)

| Content | SHA-256 | Status under D-009 |
| --- | --- | --- |
| `ercot_hourly_load_harmonized.csv` | `272af17cd1b2df14b921756738c6625b22c7702a6d14139886c3ff32728689eb` | **CONTROLLING for Track A.** Adoption is content-specific, not filename-based: it applies only at this exact digest and an observed size of 54,688,032 bytes. |
| `ercot_hourly_load_harmonized.csv` | `9f1817f78d1bb56ad3c5ea08b95b83e235616bd90ff85809182841f36f09bb35` | **EXCLUDED.** Documented stale pre-CC-8 delivery (F-06). Not importable, not substitutable, not an equivalent copy. Remains in place as historical provenance evidence. |
| `ercot_hourly_load_harmonized.csv.gz` | `e4d300b36fdbd56a8e86e660b9770ad5888e348e62a2ae136ddb5ad7ff55579e` | **GOVERNANCE-QUARANTINED.** Remains in place; must not be modified, decompressed, parsed, opened for content comparison, moved, renamed, copied into the repository, or deleted. Metadata-only checks (`stat`, `file`, `sha256sum`) remain permitted. No inference is adopted about its decompressed contents. |

The load artifact **has been imported** under D-009 at the controlling digest `272af17c…`,
verified byte-exact at source and destination, and is recorded in
`docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv`. The excluded and quarantined contents remain in
place, unmodified, and were not read for content.

## Track A experiment freeze

`docs/track_a/EXPERIMENT_FREEZE_v1.md` — **drafted, frozen on commit.**

Freezes the CNP/AdaCNP comparison, the controlled-comparison requirement, episode and
context definitions, Gaussian output, primary and calibration metrics, three seeds, nine
required validations, and six sequential execution stages.

Execution stages **1, 2 (synthetic), 3 (normal-period validation), and 4 (exploratory
held-out-event) are complete**. Stage 3 was executed under D-008, restricted to non-event
periods; stage 4 under D-011, exploratory only. Stages **5 and 6 remain blocked**.

## Next authorized implementation task

`TRACK-A-REAL-DATA-READINESS-001` is **complete**, and the stage-4 exploratory experiment it
prepared has since been executed under D-011.

**No implementation task is currently authorized.** Stages 5 and 6 — the full leave-one-event-out
sweep and the confirmatory comparison — are blocked by their sequential gates, and D-011
expressly does not grant them. Opening stage 5 requires a further recorded decision.

**Before any stage-5 decision**, the exploratory results should be read against their stated
limitations: one seed, three events, no variance estimate, and normalized units that are not
comparable across folds. See `docs/track_a/STAGE4_EXPLORATORY_RESULTS_v1.md` §2.1 and §4.

## Still blocked

- freeze execution stages **5 and 6** — the full leave-one-event-out sweep and the confirmatory
  comparison. D-011 granted the execution gate for stage 4 only. Opening stage 5 requires a
  separate recorded decision;
- held-out-event prediction or scoring for **any event outside the E08/E14/E21 trio**, and at
  **any seed other than `20260729`**;
- reporting any stage-4 result as confirmatory or as adjudicating the frozen hypothesis;
- approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` as a whole;
- import of any artifact not identified and hash-verified under
  `TRACK-A-REAL-DATA-READINESS-001`;
- changes to the frozen event inventory;
- Track B design amendments.

Stage 3 was executed with every event-period hour excluded from training, validation, and
scoring (D-008, freeze §11.1), asserted by test. Stage 4 scores event-period hours under the
D-010 treatment: `verified_shed` excluded from the primary metric, `unresolved` retained and
flagged, all-hours served-load NLL reported as a required diagnostic.

## Recorded corrections to evidence documents

- **`docs/audit/ARTIFACT_INVENTORY_001.md` §8.2 states the candidate inventories carry "19 event
  rows". The controlling file carries 21.** The imported artifact's digest matches the one
  declared controlling, so the file is right and the audit's row count is wrong. Recorded here
  rather than edited into the audit document, which is preserved as historical evidence. D-006
  cites that section, and its ruling is unaffected: the operative values are derived from the
  artifact at run time, and the derived load-eligible count is 17.

## Import blockers

Resolved: **IB-6** (D-005), **IB-1** (D-006), **IB-3** (D-007).

**IB-2, IB-4, IB-5, and IB-7 remain unresolved.** D-008 does not adjudicate them; the Track A
minimal import set is scoped to avoid every artifact they touch. Avoidance by exclusion is
not resolution, and they continue to gate any import beyond that minimal set.

**IB-2 — bounded disposition under D-009.** IB-2 **remains open** as a provenance issue
concerning the identity and history of the unexplained gzip content `e4d300b3…`. The
underlying discrepancy is **not resolved**. It **no longer blocks the Track A stage-3 path**,
because that content is explicitly excluded and governance-quarantined while the controlling
load artifact is identified independently by its complete digest. IB-4, IB-5, and IB-7 are
untouched by D-009 and continue to block any artifact they entangle.

Still deferred, each requiring a separate bounded task:

| ID | Blocker |
| --- | --- |
| IB-2 | Unexplained gzip hash mismatch (`e4d300b3…`) |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts |
| IB-7 | Four same-name / different-content pairs |
| — | Approval of the proposed import manifest |

**Resolved 2026-07-29:** censoring treatment of the target series (freeze §11.1) — adopted by
**D-010**, instrument `docs/track_a/CENSORING_TREATMENT_RULING_v1.md`. `verified_shed`
excluded from the primary NLL; `unresolved` retained, flagged, disclosed; all-hours
served-load diagnostic required; censored likelihood optional. Censoring state does not govern
event selection.

## Resolved — the proposed E18-for-E21 substitution was declined

`configs/track_a/exploratory_stage4_runs.yaml` (commit `7923593`) proposed replacing **E21** with
**E18** in the stage-4 exploratory trio, marked `PROPOSED_PENDING_PI_DECISION`. It was put to the
PI on 2026-07-29 and **declined** by **D-011**, because verification against the controlling
artifacts contradicted the proposal's stated ground. The committed trio E08/E14/E21 stands, and
stage 4 was executed on it.

The proposal's ground was that E21's censoring status is unresolvable while E18's is "RESOLVED
but not clean". Checked against `data/frozen/track_a/v7_demand_censored_v3.csv`:

| Event | Hours | `censor_status` | `source_status` | `confidence` |
| --- | --- | --- | --- | --- |
| E18_20240114 | 83 | all `unresolved` | `NOT_RETRIEVED` | `none` |
| E21_20260125 | 78 | all `unresolved` | `RETRIEVED_VERIFIED` | `none` |

Three findings follow:

1. **Both events are entirely `unresolved`.** Neither is resolved. The substitution does not
   replace an unknowable with a knowable.
2. **E21 carries the stronger recorded provenance of the two.** Its 78 hours are
   `RETRIEVED_VERIFIED`, with a sourced determination that the DOE FPA 202(c) orders are
   supply-side authorities and not evidence of shed. E18's 83 hours are `NOT_RETRIEVED`. On the
   controlling record the swap moves *away* from the better-documented event.
3. **The supporting evidence is not in the record.** The OE-417 sweep, the EIA Appendix B
   public-appeal filings, and the claim that E16 holds "the strongest affirmative no-shed
   evidence" appear nowhere in the repository except in that config file's own comments. No
   hour carries `verified_no_shed`; the state has zero occurrences.

**Interaction with D-010.** D-010 retains `unresolved` hours in the primary metric, flagged and
disclosed, and records that censoring state does not govern event selection. `unresolved` is the
state of 1,191 of 1,271 event-hours, including every hour of E18. Under the adopted ruling, E21
is scorable on exactly the same terms as E18 and as most of the record, which removes the
premise the substitution rests on.

**Disposition.** Declined by D-011. Reopening it would require either evidence in the
controlling record that distinguishes E18 from E21, or an explicit decision on a different
ground — an event-selection decision, not a censoring one — stating that ground and its
consequences for the exploratory comparison.

Recorded because it was sound: the proposal deliberately rejected E16, the apparently cleanest
candidate, on the reasoning that substituting the cleanest available event would bias the
exploratory run toward a favourable result. That instinct about selection bias was correct even
though the substitution itself did not survive verification.

## Current task

The authoritative task definition is:

`docs/project/NEXT_TASK.md`
