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

Governance complete for the neural-process extension. Track A experiment freeze drafted.
Transitioning from audit to implementation.

No artifact has been imported. No model code exists yet.

## Governance decisions in force

| ID | Decision |
| --- | --- |
| D-005 | Neural-process extension boundary — resolves IB-6 |
| D-006 | `event_inventory_headline.csv` is the controlling event inventory — resolves IB-1 |
| D-007 | UTC canonical axis; `America/Chicago` calendar; 09:00 CT D-1 issuance — resolves IB-3 |

## Track A experiment freeze

`docs/track_a/EXPERIMENT_FREEZE_v1.md` — **drafted, frozen on commit.**

Freezes the CNP/AdaCNP comparison, the controlled-comparison requirement, episode and
context definitions, Gaussian output, primary and calibration metrics, three seeds, nine
required validations, and six sequential execution stages.

Execution stages **1 and 2 (synthetic) are authorized**. Stages 3–6 (real data) are not.

## Next authorized implementation task

`TRACK-A-SCAFFOLD-001` — Track A synthetic scaffold. See `docs/project/NEXT_TASK.md`.

Synthetic fixtures only. Nine modules, eight tests, CPU. No real artifact may be loaded.

## Still blocked

- real-data import, and approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv`;
- held-out-event model predictions;
- held-out-event performance inspection;
- freeze execution stages 3 through 6;
- changes to the frozen event inventory;
- Track B design amendments.

## Import blockers

Resolved: **IB-6** (D-005), **IB-1** (D-006), **IB-3** (D-007).

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
