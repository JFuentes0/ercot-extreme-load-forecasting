# Next Task

## Task ID

ARTIFACT-INVENTORY-001

## Title

Inventory and classify existing ERCOT project artifacts

## Track

SHARED

## Objective

Perform a read-only inventory of the located existing project materials.
Identify, hash, and classify candidate artifacts before any copying or import
is authorized. This task produces evidence only. It does not import anything.

## Authoritative inputs

The discovery step is complete. The inventory must use exactly these inputs.
No other discovery scan may be substituted for them.

### Discovery scan outputs

| Role | Path |
| --- | --- |
| Source-root list | `/home/johnny_fuentes/project-location-scan/source_roots.txt` |
| Named top-level Downloads candidates | `/home/johnny_fuentes/project-location-scan/downloads_top_level_files.txt` |
| Original discovery list | `/home/johnny_fuentes/project-location-scan/candidates.tsv` |
| Discovery-input snapshot | `/home/johnny_fuentes/project-location-scan/inventory_input_snapshot.sha256` |

### Migration root

| Role | Path |
| --- | --- |
| Migration root | `/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29` |
| Reference manifest | `/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29/Project_Migration_Manifest_v1.csv` |
| Missing-item report | `/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29/Missing_or_Unrecoverable_Artifacts_v1.md` |
| Archive provenance directory | `/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29/_original_archives` |

## Scope

- recursively inventory only the seven roots listed in `source_roots.txt`;
- within Downloads, inspect only the 41 named top-level files listed in
  `downloads_top_level_files.txt`; do not walk the rest of Downloads;
- treat `candidates.tsv` as the original discovery list and reconcile it
  against what is observed;
- reconcile all candidates against the 75-row
  `Project_Migration_Manifest_v1.csv`;
- treat `inventory_input_snapshot.sha256` as the record of the discovery
  inputs as they stood at discovery time, and verify it before use.

## Permitted actions

- recursively enumerate only the seven roots in `source_roots.txt`;
- read files as needed to identify their purpose;
- record relative path, absolute source root, size, modification time,
  extension or format, and SHA-256 for every candidate;
- compute SHA-256 by streaming the file; do not load large files into memory;
- classify every candidate as one of: control artifact, governing document,
  source data, derived data, source code, notebook, result artifact, manifest,
  provenance archive, duplicate, obsolete, or unknown;
- identify exact duplicates by SHA-256;
- report same-name files whose content differs;
- verify complete prior hashes wherever a prior digest is available;
- label any file lacking a prior digest `FIRST_RECORDED_AT_MIGRATION`;
- identify candidate authoritative event inventories;
- identify candidate Track A and Track B controlling documents;
- locate existing hash manifests, censoring evidence, issuance-time rules,
  event definitions, partition definitions, feature registers, and prior code;
- compare duplicates and report drift;
- produce a proposed import manifest;
- write only the inventory report and proposed manifest under `docs/audit/`.

## Migration-root rules

The migration root has a specific structure and must be handled as follows.

- treat the 58 top-level extracted files under the migration root as candidate
  artifacts and inventory them like any other candidate;
- treat the four ZIP files under `_original_archives` as provenance packages,
  not as ordinary candidate artifacts;
- integrity-check each ZIP and record its SHA-256;
- record ZIP membership, listing the entries contained in each archive;
- do not double-count ZIP members as separate candidate artifacts when an
  extracted copy already exists at the migration root;
- report any ZIP member whose extracted counterpart is missing, and any whose
  extracted counterpart differs in content;
- do not extract the ZIPs again.

## Forbidden actions

- do not copy, move, rename, delete, or modify source artifacts;
- do not extract, re-extract, or unpack any archive;
- do not write into `data/`, `artifacts/`, `runs/`, `src/`, `configs/`,
  or `tests/`;
- do not modify `.gitignore` or the `data/frozen` policy;
- do not select an authoritative artifact when evidence is ambiguous;
- do not infer missing schemas, timezones, event membership, censoring status,
  or issuance-time conventions;
- do not implement partition or model code;
- do not install packages;
- do not train models;
- do not generate or inspect held-out-event performance.

## Inventory behavior

The inventory continues through adverse conditions. Continue even when:

- a listed candidate is missing;
- a file is unreadable or permission-denied;
- an item is ambiguous or cannot be classified with confidence;
- candidate copies conflict with each other;
- a recorded hash does not match its file;
- censoring evidence is missing;
- multiple candidate inventories disagree;
- timezone documentation is ambiguous;
- existing hashes are absent;
- schemas are incomplete.

Record each such condition as a finding. These reduce confidence in the
inventory; they do not terminate it.

### Expected historical conditions

These are not errors and must not be reported as inventory failures.

- The historical materials predate the current CNP versus AdaCNP Track A.
  The absence of Track A artifacts in the historical record is expected.
- Historical documents describing Model A versus Model B correspond to the
  frozen benchmark now designated Track B. Map them to Track B and record the
  naming correspondence.

## Import-blocking conditions

The inventory itself continues to completion. Separately, no later import may
be approved while:

- the authoritative event inventory is not uniquely identified;
- candidate controlling artifacts materially disagree;
- a recorded hash does not match its file;
- schema or timezone conventions remain unresolved;
- the distinction between controlling and descriptive documents is unclear;
- a manifest row cannot be reconciled to an observed file;
- a ZIP member has no extracted counterpart, or the counterpart differs.

## Required outputs

1. `docs/audit/ARTIFACT_INVENTORY_001.md`
2. `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv`

The report must include:

- the authoritative inputs used, and verification of the discovery-input
  snapshot;
- source roots inspected;
- inventory scope and exclusions, including the Downloads restriction;
- artifact classification summary;
- reconciliation against the 75-row migration manifest, itemizing manifest rows
  with no observed file and observed files with no manifest row;
- migration-root results: extracted top-level files, ZIP integrity, ZIP
  membership, and extracted-counterpart status;
- candidate controlling documents;
- candidate authoritative inventories;
- Model A / Model B to Track B naming correspondence;
- exact duplicates by SHA-256;
- same-name, different-content files;
- hash verification results, including items labeled
  `FIRST_RECORDED_AT_MIGRATION`;
- missing, unreadable, ambiguous, and conflicting items;
- unresolved questions;
- import-blocking findings;
- recommended next bounded task.

## Acceptance criteria

- no source artifact is changed, extracted, or re-extracted;
- only the seven roots in `source_roots.txt` were walked;
- only the 41 named top-level Downloads files were inspected;
- every listed artifact has a SHA-256 computed by streaming;
- every listed artifact has a classification;
- unknown items remain explicitly classified as unknown;
- duplicates and conflicting copies are reported;
- every one of the 75 manifest rows has a reconciliation status;
- ZIP members are not double-counted against their extracted copies;
- no large file is copied into the repository;
- the output distinguishes observed facts from interpretations;
- `git diff` shows changes only under `docs/audit/` and this task contract.
