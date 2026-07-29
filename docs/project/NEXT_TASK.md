# Next Task

## Task ID

TRACK-A-SCAFFOLD-001

## Title

Implement and test the Track A neural-process infrastructure on synthetic data

## Track

A

## Purpose

Implement and test the Track A neural-process infrastructure using **synthetic data only**.

This task builds and validates the model machinery. It touches no real ERCOT, EIA, weather,
event, or censoring artifact, constructs no real partition, and produces no held-out-event
result.

## Authority

- `docs/project/PI_AUTHORITY_DETERMINATION_v1.md` and decision D-005 authorize Track A
  neural architectures.
- `docs/track_a/EXPERIMENT_FREEZE_v1.md` §10 authorizes execution stages 1 and 2
  (synthetic unit tests, synthetic CPU smoke training) and no others.

## Read-only reference materials

These are **read-only references**. They may be read to establish model mechanics. They may
not be modified, moved, copied into the repository, or imported as artifacts.

| Role | Path |
| --- | --- |
| AdaCNP paper | `/home/johnny_fuentes/ercot-model-references/adacnp_arxiv_2602.04609.pdf` |
| CNP paper | `/home/johnny_fuentes/ercot-model-references/cnp_arxiv_1807.01613.pdf` |
| Reference hashes | `/home/johnny_fuentes/ercot-model-references/paper_hashes.sha256` |

**Hash verification is a hard precondition.** `paper_hashes.sha256` must be verified with
`sha256sum -c` or a byte-exact equivalent, and every entry must pass, **before any model
implementation begins**. If any entry fails, or if any listed path is absent, stop and
report; do not proceed to model code.

> **Precondition status:** as of 2026-07-29 all three reference paths above exist, and
> `sha256sum -c paper_hashes.sha256` reported `OK` for both
> `adacnp_arxiv_2602.04609.pdf` and `cnp_arxiv_1807.01613.pdf`. This records the
> materials as present; it does **not** discharge the precondition. Verification must be
> re-run at the start of scaffold execution, its output captured as completion evidence,
> and every entry must pass before any model implementation begins.

## Authorized modules

- `src/ercot_forecasting/track_a/dataset.py`
- `src/ercot_forecasting/track_a/context_retrieval.py`
- `src/ercot_forecasting/track_a/encoder.py`
- `src/ercot_forecasting/track_a/aggregation.py`
- `src/ercot_forecasting/track_a/decoder.py`
- `src/ercot_forecasting/track_a/cnp.py`
- `src/ercot_forecasting/track_a/adacnp.py`
- `src/ercot_forecasting/track_a/losses.py`
- `src/ercot_forecasting/track_a/train.py`

Package `__init__.py` files required to make the above importable are authorized.

## Authorized additional output

- `docs/track_a/MODEL_MECHANICS_NOTE_v1.md`

**This note must be written before any model code.** Sequence for this task is: verify paper
hashes → read the papers → write the mechanics note → implement modules → write tests.

### Required contents of the mechanics note

- standard CNP context encoding and aggregation;
- AdaCNP target-conditioned weighting;
- decoder inputs;
- predictive distribution;
- training objective;
- paper-stated tensor relationships;
- unspecified details requiring project engineering choices.

### Citation requirement

For each model-mechanics claim, cite the paper **page, section, equation, figure, or table**
where possible. Where a claim cannot be traced to a specific location, say so rather than
implying a citation exists.

### Required provenance separation

Every statement in the note must be labeled with exactly one of:

| Label | Meaning |
| --- | --- |
| `PAPER-SPECIFIED` | Stated in the cited paper |
| `ERCOT-APPLICATION CHOICE` | A choice this project makes to apply the method to ERCOT data |
| `ENGINEERING DEFAULT` | An implementation default not driven by the paper or the science |
| `NOT SPECIFIED BY PAPER` | The paper is silent; a project decision is required |

### Precedence

**`docs/track_a/EXPERIMENT_FREEZE_v1.md` remains controlling.** The papers may clarify model
mechanics. They may **not** silently override the frozen comparison, data rules, metrics,
partitions, seeds, or leakage safeguards.

**If a paper-described mechanic conflicts with the experiment freeze, stop and report the
conflict before implementing code.** Do not resolve such a conflict inside this task, and do
not implement either side of it.

## Authorized tests

- CNP output shapes;
- AdaCNP output shapes;
- positive scales;
- adaptive weights sum to one;
- no target-`y` retrieval leakage;
- uniform-weight equivalence;
- deterministic fixed-seed smoke run;
- tiny synthetic overfit.

## Restrictions

- synthetic fixtures only;
- no ERCOT, EIA, weather, event, or censoring artifact may be loaded;
- no source artifact may be imported;
- no real event partition may be constructed;
- no held-out-event prediction or performance inspection;
- no Track B modification;
- no new package installation without a separate approval;
- CPU compatibility is required;
- GPU use is not required;
- no fold count, event count, or inventory size may be hard-coded anywhere (decision D-006,
  freeze §10.1);
- fixed UTC offsets are prohibited in any time handling (decision D-007).

## Design constraints inherited from the freeze

These are not new decisions; they are the frozen items this scaffold must satisfy.

- Output is 24 Gaussian means and 24 positive Gaussian scales; scale via softplus plus a
  frozen numerical floor.
- The aggregation mechanism is the only permitted difference between the CNP and AdaCNP
  arms. Encoders, decoder, normalization, optimizer settings, and seeds are shared.
- Context retrieval may consume target inputs `x` and must be structurally incapable of
  consuming target outcomes `y`.
- Headline context size 64; context size 32 as a sensitivity.
- Seeds 20260729, 20260730, 20260731.
- Uniform AdaCNP weighting must reproduce CNP aggregation numerically within a recorded
  tolerance.

## Required completion evidence

- paper-hash verification output;
- `docs/track_a/MODEL_MECHANICS_NOTE_v1.md`;
- pytest results;
- Ruff results;
- module inventory;
- synthetic smoke-training result;
- deterministic-repeat result;
- uniform-equivalence tolerance and result;
- any paper-versus-freeze conflict found, or an explicit statement that none was found;
- `git diff` summary;
- **no commit until PI approval.**

## Acceptance criteria

- every entry in `paper_hashes.sha256` verified before model implementation began;
- the mechanics note exists, was written before model code, and labels every statement
  `PAPER-SPECIFIED`, `ERCOT-APPLICATION CHOICE`, `ENGINEERING DEFAULT`, or
  `NOT SPECIFIED BY PAPER`;
- every authorized module exists and imports cleanly on CPU;
- all eight authorized tests exist and pass;
- uniform-weight equivalence passes within a stated numerical tolerance;
- the target-`y` leakage test demonstrates structural impossibility, not merely absence;
- two runs at the same seed produce identical smoke results;
- each arm overfits a tiny synthetic fixture;
- no real data file is read at any point;
- no event count or fold count appears as a literal;
- `git diff` shows changes only under `src/ercot_forecasting/track_a/`, `tests/`,
  `configs/` if configuration is required, and `docs/track_a/MODEL_MECHANICS_NOTE_v1.md`;
- no reference file under `/home/johnny_fuentes/ercot-model-references/` is modified,
  moved, or copied into the repository;
- nothing is committed.

## Out of scope for this task

Deferred and untouched: IB-2, IB-4, IB-5, IB-7, import-manifest approval, the censoring
treatment ruling (freeze §11.1), the real-data execution gate, and freeze execution stages
3 through 6.
