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

Synthetic scaffold complete and committed. Track A experiment freeze committed. Preparing the
first verified real-data import and normal-period validation.

The Track A synthetic scaffold (`TRACK-A-SCAFFOLD-001`) is implemented and committed: nine
modules, 21 passing tests, CPU-only, synthetic fixtures only. Trainable parameter counts are
CNP 110,512 and AdaCNP 123,569, with an identical shared encoder/decoder backbone.

**No artifact has been imported yet.** Real-data import is authorized in principle by D-008
but occurs only through `TRACK-A-REAL-DATA-READINESS-001`, and only for artifacts identified
and hash-verified by that task.

## Governance decisions in force

| ID | Decision |
| --- | --- |
| D-005 | Neural-process extension boundary — resolves IB-6 |
| D-006 | `event_inventory_headline.csv` is the controlling event inventory — resolves IB-1 |
| D-007 | UTC canonical axis; `America/Chicago` calendar; 09:00 CT D-1 issuance — resolves IB-3 |
| D-008 | Track A real-data execution gate, **stage 3 only** — normal-period validation |

## Track A experiment freeze

`docs/track_a/EXPERIMENT_FREEZE_v1.md` — **drafted, frozen on commit.**

Freezes the CNP/AdaCNP comparison, the controlled-comparison requirement, episode and
context definitions, Gaussian output, primary and calibration metrics, three seeds, nine
required validations, and six sequential execution stages.

Execution stages **1 and 2 (synthetic) are complete**. Stage **3 (normal-period validation)
is authorized** by D-008, restricted to non-event periods. Stages **4, 5, and 6 remain
blocked**.

## Next authorized implementation task

`TRACK-A-REAL-DATA-READINESS-001` — verified real-data pipeline, stage-3 normal-period
validation, and preparation of the stage-4 exploratory runs. See `docs/project/NEXT_TASK.md`.

Seven workstreams: packaging cleanup, minimal verified import, data validation, partition and
issuance safeguards, stage-3 normal-period validation, a censoring-ruling **draft**, and
preparation of six exploratory runs that must **not** be executed.

## Still blocked

- **held-out-event model predictions;**
- **held-out-event performance inspection;**
- freeze execution stages 4, 5, and 6;
- adoption of the censoring-treatment ruling (freeze §11.1) — gates stage 4;
- approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` as a whole;
- import of any artifact not identified and hash-verified under
  `TRACK-A-REAL-DATA-READINESS-001`;
- changes to the frozen event inventory;
- Track B design amendments.

Stage 3 may proceed only with every event-period hour excluded from training, validation, and
scoring (D-008, freeze §11.1).

## Import blockers

Resolved: **IB-6** (D-005), **IB-1** (D-006), **IB-3** (D-007).

**IB-2, IB-4, IB-5, and IB-7 remain unresolved.** D-008 does not adjudicate them; the Track A
minimal import set is scoped to avoid every artifact they touch. Avoidance by exclusion is
not resolution, and they continue to gate any import beyond that minimal set.

Still deferred, each requiring a separate bounded task:

| ID | Blocker |
| --- | --- |
| IB-2 | Unexplained gzip hash mismatch (`e4d300b3…`) |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts |
| IB-7 | Four same-name / different-content pairs |
| — | Approval of the proposed import manifest |
| — | Censoring treatment of the target series (freeze §11.1) — gates real-data stages |

## Current task

The authoritative task definition is:

`docs/project/NEXT_TASK.md`
