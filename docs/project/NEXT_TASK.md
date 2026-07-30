# Next Task

> ## ⚠ THIS CONTRACT IS COMPLETE AND SUPERSEDED — DO NOT EXECUTE IT
>
> `TRACK-A-REAL-DATA-READINESS-001` finished on 2026-07-29. All seven workstreams are
> done, and the stage-4 runs it prepared have since been **executed** under D-011.
> Reading it as a live contract would re-run completed work and, worse, re-impose
> prohibitions that later decisions lifted.
>
> **For live status, read `docs/project/CURRENT_STATE.md`.** The text below is retained
> as the historical record of what was contracted.
>
> ### What has changed since this contract was written
>
> | Then | Now |
> | --- | --- |
> | Censoring ruling: **draft only**, must not be adopted | **Adopted** (D-010) |
> | Exploratory trio: E08 / E14 / E21, runs prepared but **not executed** | Trio confirmed and **executed** (D-011); the proposed E18 substitution was declined |
> | Stage-4 execution: **blocked** | **Granted** for stage 4 only (D-011) |
> | Weather input: deferred, no feature table | Regional temperature index **imported and used** (D-012) |
> | Context construction: nearest-neighbour only | Both nearest and paper-faithful sampling (D-013) |
> | Training length: fixed 300 steps | Chosen on inner validation (D-014) |
> | "Nothing committed until PI approval" | Committed on PI instruction — `0dded2c`, `e5ddfa2`, `575b4dc` |
>
> ### The next task is not yet written
>
> Stage 5 (full leave-one-event-out sweep) is **blocked**, and its blockers are
> decisions rather than implementation:
>
> 1. **An execution-gate decision extending D-011**, which grants stage 4 only.
> 2. **The inferential procedure the freeze never specified** — unit of analysis,
>    fold aggregation, variance estimation, and the criterion for judging a
>    difference real. This must be settled *first*: it determines what the sweep
>    records, and deciding it afterwards risks a re-run.
>
> Three items that a stage-5 task definition must settle, identified during the
> stage-4 pass:
>
> - **Scale.** The full factorial is 17 folds × 2 arms × 2 feature sets × 2 context
>   conditions × 3 seeds ≈ **408 runs** (~6 h at the observed ~50 s/run); at ten
>   seeds ≈ **1,360 runs** (~19 h). Decide whether stage 5 runs the whole factorial
>   or designates one primary cell with the rest as predeclared sensitivities.
> - **Seed count.** `POWER_ANALYSIS_v1.md` finds initialisation noise dominates and
>   that more seeds is the cheapest improvement available — but freeze §8 fixes
>   three seeds, so raising it **amends a frozen item** and needs its own decision.
> - **E05 under the temperature feature set** drops from 3 held-out days to 1
>   (D-012 discloses this). Either a disclosure rule or a ruling on whether a
>   single-day fold is scoreable at all.

---

## Task ID

TRACK-A-REAL-DATA-READINESS-001 — **COMPLETE, superseded (see above)**

## Title

Prepare the verified Track A real-data pipeline, run normal-period validation, and stage the
first exploratory event experiment without held-out-event scoring

## Track

A

## Purpose

Bring Track A from a synthetic scaffold to a verified real-data pipeline, execute freeze
execution **stage 3** (normal-period validation) only, and prepare — but not run — the
stage 4 exploratory event experiment.

This task performs the first import of real artifacts into the repository. It does not score
any held-out event, and does not adopt the censoring ruling that stage 4 requires.

## Authority

- `docs/project/PI_AUTHORITY_DETERMINATION_v1.md` and decision D-005 authorize Track A
  neural architectures.
- `docs/track_a/EXPERIMENT_FREEZE_v1.md` remains controlling for the frozen comparison, data
  rules, metrics, partitions, seeds, and leakage safeguards.
- Decisions D-006 (controlling inventory) and D-007 (UTC axis, `America/Chicago` calendar,
  09:00 CT D-1 issuance) govern all data handling here.
- `TRACK-A-SCAFFOLD-001` is complete and committed (`bc3a326`). Its 21 tests are the
  regression baseline for this task.

### What this contract grants

Freeze §11 lists the **real-data execution gate** as "Not yet requested or approved". This
contract **grants that gate for execution stage 3 only**, on the decision authority of
Jonathan Fuentes. Stages 4, 5, and 6 remain blocked.

> **Governance action required separately.** Granting the stage-3 execution gate and
> authorizing the first real-data import are decisions of record. A `DECISION_LOG.md` entry
> and a `CURRENT_STATE.md` update should be authored in a separate governance pass; this
> authoring pass is restricted to `NEXT_TASK.md` and did not make them.

### How the stage-3 import blockers are handled

Freeze §11 lists **IB-2, IB-4, IB-5, IB-7** as gating stage 3. This task does **not**
adjudicate any of them. It handles them by **scoped exclusion**: the minimal import set is
defined so that no artifact touched by those findings is imported at all.

If any artifact required by the minimal set turns out to be entangled with IB-2, IB-4, IB-5,
or IB-7, **stop and report**. Do not resolve the blocker inside this task, and do not import
the artifact under an assumption.

---

## Workstream 1 — Packaging cleanup

Make the repository importable through the **existing** uv environment (`.venv`), so that
`import ercot_forecasting` resolves without path manipulation.

### Authorized change

`pyproject.toml` currently has no `[build-system]` section, which is what prevents an
editable installation. Adding the **minimum valid `[build-system]` section** required for
editable installation is authorized, subject to **every** condition below.

### Binding conditions

1. **Inspect first.** Read the existing `pyproject.toml` and inspect the current environment
   before making any change.
2. **Use a backend already available** in the existing environment.
3. **Do not install or download a build backend.**
4. **Do not add dependencies** of any kind — runtime, development, optional, or test.
5. **Do not change dependency versions.**
6. **Do not update `uv.lock`** merely to obtain packaging support.
7. **Do not alter unrelated project metadata** — name, version, description, `requires-python`,
   dependency groups, or any other existing field.
8. **Do not restructure the package** beyond what the existing `src/ercot_forecasting` layout
   requires.
9. **Verify editable installation without relying on `tests/conftest.py`.** Demonstrate that a
   plain `import ercot_forecasting` succeeds with the bootstrap inactive.
10. **Remove `tests/conftest.py` only after** normal imports and all existing tests succeed.
11. **If no suitable build backend is already available, stop the entire
    `TRACK-A-REAL-DATA-READINESS-001` task and report the finding** before importing data,
    modifying real-data pipeline code, or executing any real-data validation. Read-only
    inspection already completed may be reported, but **no later workstream may proceed**. Do
    not select, install, or download a backend.

Condition 11 is a hard stop on the whole task, not a preference and not a workstream-local
failure. A backend chosen for convenience is a new dependency by another name.

### Scope of this change

**The `[build-system]` addition is packaging infrastructure only.** It does not authorize
real-data execution beyond the stage-3 scope stated in this contract, does not widen the
import set, does not relax any freeze item, and carries no scientific effect. It changes how
the package is installed, and nothing else.

### Regression requirement

**All 21 scaffold tests must still pass, unchanged in intent.** Any scaffold test that must be
edited to accommodate packaging is a finding to report, not a routine fix.

## Workstream 2 — Minimal verified data import

### Identification precedes copying

**This contract is not blanket approval to import whichever files have convenient or
plausible-looking names.** The artifact classes below describe *roles*, not filenames. A file
is importable only once its **source hash, governing status, purpose, and destination** have
all been established and recorded, and only once they are consistent with each other and with
the governing decision cited for that row.

Selecting a file because its name matches a role in the table below is not identification. If
two candidates could plausibly fill a role, or if a candidate's governing status cannot be
established from `docs/audit/ARTIFACT_INVENTORY_001.md`, **stop and report that role** rather
than choosing between them. Import nothing on an assumption about what a file probably is.

Import **only** what Track A requires:

| # | Artifact class | Purpose |
| --- | --- | --- |
| 1 | Controlling headline event inventory | Fold definition (D-006) |
| 2 | Harmonized ERCOT load artifact, from the verified controlling set | Target series |
| 3 | Weather input required by the frozen Track A feature design | Model input |
| 4 | Load-eligibility information | Event eligibility rule (D-006) |
| 5 | Censoring-status artifact | Stage-4 gating evidence; not applied in stage 3 |
| 6 | Schema, zone-weight, or provenance files strictly required to interpret the above | Interpretation |

Nothing outside this list may be imported by this task.

### Prohibited imports

- artifacts with unexplained prior-hash mismatches (IB-2);
- ambiguous same-name / different-content artifacts (IB-7);
- artifacts marked `AWAITING RATIFICATION` (IB-4), unless separately approved;
- Track B-only artifacts not required by Track A;
- historical duplicates and unreconciled `unknown` rows (IB-5).

### Import manifest requirements

`docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` is **non-authoritative**. It may be read as a
candidate list. It becomes authoritative for Track A only through this task's own manifest.

Produce `docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv`. Every row must carry:

1. exact **source path**;
2. **source SHA-256**, computed at read time, not copied from a prior document;
3. exact **destination path** inside the repository;
4. **destination SHA-256**, computed after copying, and asserted equal to the source hash;
5. **purpose** — which workstream or model input the artifact serves;
6. **governing status** — controlling, sensitivity, evidence, or reference;
7. **governing decision or document** — e.g. D-006, freeze §, inventory finding;
8. **blocker check** — an explicit statement that the row is clear of IB-2, IB-4, IB-5,
   and IB-7.

A row that cannot be completed on all eight fields is not importable. Report it and stop for
that artifact; continue with the rest.

### Permitted destination paths

```
data/frozen/track_a/      immutable verified inputs, write-once
data/track_a/             Track A derived artifacts
data/shared/              shared inventory and eligibility artifacts
```

Source paths are **not** pre-authorized by this contract because they must be established
from `docs/audit/ARTIFACT_INVENTORY_001.md` at run time and recorded with hashes. Enumerate
each one in the manifest before copying. Do not read from `data/track_b/`.

Source artifacts are **read-only**. No source file may be modified, moved, renamed, or
deleted.

## Workstream 3 — Data validation

Required checks, each producing recorded output:

1. source SHA-256 **before** copying;
2. destination SHA-256 **after** copying, asserted equal;
3. schema and column validation against the declared schema;
4. duplicate-timestamp detection;
5. monotonic UTC timestamps;
6. timezone-aware `America/Chicago` conversion, via a timezone database;
7. hourly continuity report, including gaps and DST transitions;
8. missing-value report;
9. event membership and eligibility report;
10. a test asserting the **fold count is derived** from the imported inventory under the
    load-eligibility rule, not hard-coded (D-006, freeze §10.1);
11. a test asserting **no fixed UTC offset** appears anywhere in time handling (D-007).

Checks 10 and 11 are assertions about the code, not only about the data.

## Workstream 4 — Partition and issuance safeguards

Implement or validate:

- UTC as the canonical storage, join, partition, and model-alignment axis;
- `America/Chicago` for calendar features, day boundaries, and the issuance cutoff only;
- day-ahead issuance frozen at **09:00 `America/Chicago` on D-1**;
- only information available at or before the issuance cutoff enters a target-day prediction;
- leave-one-event-out outer partition construction;
- **±7-day** exclusion buffer;
- exclusion of the held-out event **and its buffer** from both training **and** context
  retrieval;
- context retrieval restricted to issuance-time-available information;
- **identical saved context indices consumed by both arms**, persisted once per episode and
  re-read by both, per freeze §4 and the Track A rules.

The scaffold's structural guarantee that target outcomes `y` cannot reach retrieval must be
preserved. Any change that gives the retrieval path access to a target outcome is a defect.

## Workstream 5 — Normal-period validation (execution stage 3 only)

- Use **non-event periods only**. **All event-period hours must be excluded**, per
  freeze §11.1's stage-3 condition.
- Run **both arms** with **one frozen seed** initially (`20260729`).
- Verify: data shapes; loss behavior; scale positivity; deterministic execution under a
  repeated seed; context identity across arms; saved run manifests.
- Report **exact trainable parameter counts for both arms**, per the PI determination
  recorded in `MODEL_MECHANICS_NOTE_v1.md` §7.3. Scaffold baseline for comparison:
  CNP 110,512; AdaCNP 123,569; shared backbone identical.
- **Do not inspect held-out-event performance.**

### Normal-period validation acceptance criteria

- every imported artifact appears in the manifest with matching source and destination
  hashes;
- all eleven workstream-3 checks pass or are reported with an explicit finding;
- both arms train on non-event data without error on CPU;
- no event-period hour appears in any stage-3 batch — asserted by test, not by inspection;
- predicted scales are strictly positive and at or above the frozen floor;
- two runs at seed `20260729` produce identical results;
- both arms consume byte-identical saved context-index files;
- a run manifest is written for each run, recording seed, config hash, input hashes, context
  index file hash, and trainable parameter counts;
- the derived fold count equals the number of load-eligible events in the imported inventory;
- all 21 scaffold tests still pass.

## Workstream 6 — Censoring ruling draft

Draft `docs/track_a/CENSORING_TREATMENT_RULING_v1_DRAFT.md`. **Draft only — do not adopt it,
and do not apply it to any scoring.**

It must cover:

- `verified_shed` hours;
- `unresolved` hours;
- `verified_no_shed` hours;
- the primary event-NLL treatment;
- an all-hours served-load diagnostic;
- whether a censored Gaussian likelihood is required or optional.

The draft should **recommend**:

1. **exclude `verified_shed` hours from the primary latent-demand NLL**;
2. **retain `unresolved` hours, flagged and disclosed** — consistent with freeze §11.1, which
   forbids resolving unknown hours by default in either direction;
3. **report all-hours served-load NLL as a secondary diagnostic**, with the estimand stated
   as served load;
4. treat a **censored Gaussian likelihood as an optional sensitivity** unless implementation
   time permits.

The draft must state the evidence it rests on and must not assert a censoring determination
the record does not support. Adoption requires a separate PI decision and a
`DECISION_LOG.md` entry.

## Workstream 7 — Exploratory run preparation (no execution)

Prepare configs and run manifests for **six planned runs**: events **E08**, **E14**, **E21**
× arms **CNP** and **AdaCNP**, at one frozen seed.

- **Do not execute these runs.**
- **Do not generate or inspect held-out-event predictions.**
- Stage 4 remains blocked until the censoring ruling is separately adopted.

> **E08, E14, and E21 are event identifiers, not counts, and this contract asserts nothing
> about inventory size.** Each must be verified to exist in the derived controlling inventory
> and to satisfy the load-eligibility rule. If any of the three is absent or ineligible, stop
> and report; do not substitute another event. No literal event count or fold count may be
> introduced anywhere (D-006, freeze §10.1).

---

## Permitted files

### Code

```
src/ercot_forecasting/shared/          shared data, time, and partition modules
src/ercot_forecasting/track_a/         Track A pipeline extensions
scripts/                               import and validation entry points
```

Per `PROJECT_CHARTER.md`, shared modules may not contain model-specific features, and any shared-code
change requires tests for **both** tracks.

### Configuration

```
configs/track_a/
configs/shared/
```

### Tests

```
tests/track_a/    tests/shared/    tests/leakage/    tests/reproducibility/
```

`tests/conftest.py` may be modified or deleted only as part of workstream 1.

### Documentation and manifests

```
docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv
docs/track_a/CENSORING_TREATMENT_RULING_v1_DRAFT.md
docs/track_a/REAL_DATA_READINESS_REPORT_v1.md
docs/track_a/CURRENT_STATUS.md
```

### Packaging

`pyproject.toml` — workstream 1 only, for installability. No dependency additions.

### Not permitted

`docs/track_a/EXPERIMENT_FREEZE_v1.md`, `docs/project/DECISION_LOG.md`,
`docs/project/CURRENT_STATE.md`, `docs/project/PI_AUTHORITY_DETERMINATION_v1.md`,
`docs/audit/ARTIFACT_INVENTORY_001.md`, any Track B path, and any file under
`data/track_b/`.

---

## Explicit held-out-event prohibitions

These hold for the entire task, without exception:

- **No held-out-event prediction.**
- **No held-out-event performance inspection.**
- No event-period hour may enter stage-3 validation.
- No stage 4, 5, or 6 execution.
- No inspection of any exploratory result, because none may be produced.
- No metric, table, figure, or log that reports event-period model performance.

If any of these appears to be required to complete a workstream, stop and report.

## Restrictions

- no package installation without separate approval;
- no modification of any source artifact outside the repository;
- no import beyond the minimal set;
- no Track B modification;
- CPU compatibility required; GPU not required;
- no fold count, event count, or inventory size as a literal (D-006, freeze §10.1);
- fixed UTC offsets prohibited (D-007);
- no change to any frozen item without a decision-log entry per the freeze preamble;
- nothing committed until PI approval.

## Required completion evidence

- packaging change and editable-install verification;
- confirmation that `tests/conftest.py`'s bootstrap is removed and discovery still works;
- all 21 scaffold tests passing after packaging changes;
- `TRACK_A_IMPORT_MANIFEST_001.csv`, complete on all eight fields per row;
- source and destination SHA-256 for every imported artifact, and their equality;
- all eleven workstream-3 validation outputs;
- derived fold count, with the assertion that it was derived;
- partition and issuance safeguard verification, including buffer exclusion;
- proof that both arms consumed byte-identical context indices;
- stage-3 normal-period validation results for both arms at seed `20260729`;
- deterministic-repeat result;
- trainable parameter counts for both arms;
- run manifests for every stage-3 run;
- censoring ruling **draft**, explicitly marked not adopted;
- six prepared stage-4 configs and manifests, with explicit confirmation that none was run;
- explicit statement that no held-out-event prediction or inspection occurred;
- Ruff and pytest results;
- `git diff --check` and `git status --short`;
- exact list of modified, new, and deleted files;
- **no commit until PI approval.**

## Acceptance criteria

- the repository installs and imports without the test-path bootstrap;
- all 21 scaffold tests pass, unmodified in intent;
- every imported artifact is manifest-listed, hash-verified at source and destination, and
  clear of IB-2, IB-4, IB-5, and IB-7;
- no prohibited artifact class was imported;
- all eleven validation checks are reported;
- fold count is derived and asserted, never a literal;
- no fixed UTC offset appears in any time handling;
- the ±7-day buffer and held-out-event exclusion are demonstrated by test;
- retrieval remains structurally incapable of consuming target outcomes;
- stage-3 validation excludes every event-period hour, asserted by test;
- both arms consumed byte-identical context indices;
- trainable parameter counts are reported for both arms;
- the censoring ruling exists as a draft and is not applied;
- six stage-4 configs exist and none was executed;
- no held-out-event prediction or performance inspection occurred anywhere;
- `git diff` touches only the permitted files;
- nothing is committed.

## Out of scope for this task

Deferred and untouched: adjudication of IB-2, IB-4, IB-5, and IB-7; adoption of the censoring
ruling; approval of `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` as a whole; freeze
execution stages 4, 5, and 6; any Track B work; and the `DECISION_LOG.md` and
`CURRENT_STATE.md` entries recording the stage-3 gate grant, which require a separate
governance pass.
