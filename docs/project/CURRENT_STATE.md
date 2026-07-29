# Current State

## Primary active track

Track A — Standard CNP versus AdaCNP.

Track A is a **separately authorized extension**, constituted under
`docs/project/PI_AUTHORITY_DETERMINATION_v1.md` and governed by
`docs/track_a/NEURAL_PROCESS_EXTENSION_ADDENDUM_v1.md` (decision D-005).

Standard CNP and AdaCNP are authorized within Track A only, as a bounded exception to
historical ruling R-5. Authorization is by Jonathan Fuentes as project decision authority.
No mentor approval of the extension is claimed.

## Secondary frozen track

Track B — quantile GBDT Model A versus Model B.

Track B is the **frozen historical benchmark**. Its design is preserved unchanged, including
DR-1 ruling R-5, which continues to prohibit neural architectures within Track B. Track B is
executable on explicit request but is not the default development priority, and it runs only
when a task explicitly states `TRACK=B`.

## Current stage

Dual-track repository initialization.

Artifact inventory complete (`docs/audit/ARTIFACT_INVENTORY_001.md`). Governance extension
boundary established (D-005). No artifact has been imported.

## Authorized work

- import and hash existing project artifacts, once the outstanding import blockers are
  resolved;
- establish shared ERCOT data and partition interfaces;
- freeze the Track A extension protocol;
- preserve the Track B frozen protocol;
- create deterministic tests.

## Not yet authorized

- held-out-event model predictions;
- held-out-event performance inspection;
- model or partition implementation;
- model training;
- changes to the frozen event inventory;
- Track B design amendments;
- artifact import, and approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv`.

## Open import blockers

Resolved: **IB-6** (R-5 versus Track A architecture conflict), by decision D-005.

Still open, each requiring a separate bounded task:

| ID | Blocker |
| --- | --- |
| IB-1 | Authoritative event inventory not uniquely ratified |
| IB-2 | Unexplained gzip hash mismatch (`e4d300b3…`) |
| IB-3 | Timezone (UTC join axis) and issuance-cutoff conventions unratified |
| IB-4 | Controlling-versus-descriptive status of `AWAITING RATIFICATION` artifacts |
| IB-5 | Unreconciled manifest rows and `unknown` artifacts |
| IB-7 | Four same-name / different-content pairs |

## Current task

The authoritative task definition is:

`docs/project/NEXT_TASK.md`
