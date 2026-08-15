# ARTIFACT-INVENTORY-001 — Artifact Inventory and Classification

**Task ID:** ARTIFACT-INVENTORY-001
**Track:** SHARED
**Date executed:** 2026-07-29
**Executed under:** `docs/project/NEXT_TASK.md`
**Decision authority:** Jonathan Fuentes
**Nature of this document:** evidence only. Nothing was imported, copied, moved, renamed,
consolidated, deleted, modified, or extracted. No model was implemented or trained. No
held-out-event performance was generated or inspected.

Throughout, **OBSERVED** marks a measured fact and **INTERPRETATION** marks a reading of
those facts. Interpretations are not decisions and do not select authoritative artifacts.

---

## 1. Authoritative inputs and discovery-snapshot verification

The four authoritative inputs named in `NEXT_TASK.md` were used. No substitute discovery
scan was performed.

| Role | Path |
| --- | --- |
| Source-root list | `/home/johnny_fuentes/project-location-scan/source_roots.txt` |
| Named top-level Downloads candidates | `/home/johnny_fuentes/project-location-scan/downloads_top_level_files.txt` |
| Original discovery list | `/home/johnny_fuentes/project-location-scan/candidates.tsv` |
| Discovery-input snapshot | `/home/johnny_fuentes/project-location-scan/inventory_input_snapshot.sha256` |

### 1.1 Snapshot verification — PASS

`sha256sum -c inventory_input_snapshot.sha256` was run before any inventory work began.
**All 6 entries verified OK; exit status 0.**

| Entry | Result |
| --- | --- |
| `source_roots.txt` | OK |
| `candidates.tsv` | OK |
| `downloads_top_level_files.txt` | OK |
| `project_extracted_inventory.tsv` | OK |
| `project_extracted_observed.sha256` | OK |
| `original_archives.sha256` | OK |

### 1.2 Finding F-01 — an earlier, non-authoritative digest file disagrees on `source_roots.txt`

**OBSERVED.** The scan directory also contains `discovery_manifest.sha256`, which is **not**
one of the four authoritative inputs. It records `source_roots.txt` as
`c4e46aa79ec454b93462507866fee6af5bf0ee9b1d112052793659e93bb66aed`, whereas the authoritative
snapshot records `1d19b161a8bbb08486e7a0fb47f0269e81d08822476c06ab0ae1cbdbf9bfe05f`, which is
the value observed now. File mtimes: `discovery_manifest.sha256` 04:46, `source_roots.txt`
05:09, `inventory_input_snapshot.sha256` 05:12.

**INTERPRETATION.** `source_roots.txt` was revised after `discovery_manifest.sha256` was
written and before the authoritative snapshot was taken. The authoritative snapshot governs
and verifies clean. This is recorded for completeness, not as a failure.

---

## 2. Source roots inspected

All seven roots in `source_roots.txt` were walked recursively. No eighth root was walked.

| # | Root | Files observed |
| --- | --- | --- |
| 1 | `/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29` | 62 (58 extracted top-level + 4 provenance ZIPs) |
| 2 | `/mnt/c/Users/fuent/Downloads/2nd Chat First File Dump` | 9 |
| 3 | `/mnt/c/Users/fuent/Downloads/7-28-26 8_38pm archive` | 23 |
| 4 | `/mnt/c/Users/fuent/Downloads/Artifacts from the First Chat` | 60 |
| 5 | `/mnt/c/Users/fuent/OneDrive/Documents/MR1a` | 28 |
| 6 | `/mnt/c/Users/fuent/OneDrive/Documents/MR1b` | 31 |
| 7 | `/mnt/c/Users/fuent/OneDrive/Documents/MR1c` | 300 |
| — | `/mnt/c/Users/fuent/Downloads` (**named files only**) | 41 |
| | **Total candidates inspected** | **554** |

---

## 3. Scope and exclusions

- **Downloads restriction honoured.** `/mnt/c/Users/fuent/Downloads` was **not** walked. Only
  the 41 named top-level files in `downloads_top_level_files.txt` were opened. All 41 were
  present and readable.
- **ZIP handling.** The four archives under `_original_archives` were treated as provenance
  packages: integrity-checked, hashed, and their membership listed from the archive central
  directory and streamed in memory. **No archive was extracted or re-extracted to disk.**
- **Other ZIPs.** ZIP files elsewhere (`MR1a_bundle.zip`, `Native_Load_*.zip`, `MR1b_batch*.zip`,
  `MR1c_batch*.zip`, `project-handoff-files.zip`, `files.zip (3).zip`) are ordinary candidate
  artifacts. They were hashed but **not opened and not enumerated**, because `NEXT_TASK.md`
  requires membership listing only for the four provenance archives and forbids extraction.
- **Hashing method.** Every SHA-256 was computed by streaming in 1 MiB blocks. No file was
  loaded into memory whole. The largest file hashed was 54,688,032 B.
- **Nothing written outside `docs/audit/`.**

---

## 4. Headline counts

| Measure | Value |
| --- | --- |
| Total candidates inspected | **554** |
| Unique content hashes | **476** |
| Duplicate groups (≥2 byte-identical copies) | **67** |
| Files that are members of a duplicate group | **145** |
| Redundant copies (copies beyond the first in each group) | **78** |
| Same-name / different-content filename conflicts | **9 filenames** |
| Same-content / different-name groups | **8 groups** |
| Prior-hash MATCH | **478** |
| Prior-hash MISMATCH | **6** (2 substantive, 4 name-collision artifacts — §11) |
| `FIRST_RECORDED_AT_MIGRATION` | **70** |
| Missing artifacts | **0** |
| Unreadable / permission-denied artifacts | **0** |
| Items classified `unknown` | **5** |
| 75-row manifest rows reconciled byte-exact | **57** |
| Manifest rows observed but without a byte-exact tie | **14** |
| Manifest rows with no observed file | **4** |

---

## 5. Artifact classification summary

Every one of the 554 candidates carries exactly one classification in
`PROPOSED_IMPORT_MANIFEST_001.csv`.

| Classification | Count |
| --- | --- |
| source data | 352 |
| duplicate | 78 |
| governing document | 37 |
| obsolete | 29 |
| manifest | 19 |
| derived data | 12 |
| source code | 11 |
| control artifact | 6 |
| unknown | 5 |
| provenance archive | 4 |
| result artifact | 1 |
| notebook | 0 |
| **Total** | **554** |

**Classification rules used** (recorded so the labels are auditable):

- *provenance archive* — the four ZIPs under `_original_archives`.
- *duplicate* — a byte-identical copy of content whose primary copy lives in a
  higher-precedence root. Precedence: migration root → OneDrive `MR1a`/`MR1b`/`MR1c` →
  `Artifacts from the First Chat` → `7-28-26 8_38pm archive` → `2nd Chat First File Dump` →
  Downloads top level.
- *obsolete* — the migration manifest records the content as `SUPERSEDED` or `HISTORICAL`.
- *governing document* — specification, decision records, freeze register, handoff, audit
  logs, mentor decision sheets, DRD packages, memoranda, correction record, quality report,
  findings table, project-context documents.
- *control artifact* — frozen inputs that constrain experimental scope: event inventories,
  zone weights, censoring windows and the censoring mapping rule.
- *derived data* — pipeline outputs: harmonized load, QC-filtered GHCNh, regional index,
  operational benchmark, ERCO extracts, censored-demand tables, coverage/QC tables.
- *source data* — raw retrieved files and retrieval bundles under `MR1a`/`MR1b`/`MR1c`.
- *manifest* — hash indices, retrieval manifests, provenance ledgers, migration manifests.
- *result artifact* — `gate_arithmetic.csv`.
- *source code* — `.py`.
- *unknown* — no corroborating manifest row and no naming rule applies. Left explicitly
  unknown, as required.

Per-root classification is in the CSV; the notable pattern is that `2nd Chat First File Dump`
resolves to **9 duplicates and nothing unique**, and Downloads top level resolves to
**38 duplicates, 1 unique document, 2 unknowns**.

### 5.1 Items classified `unknown` (5)

| Path | Basis |
| --- | --- |
| `7-28-26 8_38pm archive/Fuentes Jonathan SULI Bios and Project Description.docx` | No manifest row; binary not opened |
| `7-28-26 8_38pm archive/Fuentes, Jonathan_SULI_Final Presentation.pptx` | No manifest row; binary not opened |
| `7-28-26 8_38pm archive/files.zip (3).zip` | Undocumented archive; not extracted, membership not enumerated |
| `Downloads/project-handoff-files.zip` | Undocumented archive; not extracted, membership not enumerated |
| `Downloads/Class_4.drd` | See F-12 below |

**F-12 — OBSERVED.** `Class_4.drd` (106 B) is ASCII with CRLF terminators and contains
Excellon/NC drill-file commands (`M48`, `T01C0.0276`, `X17883Y5483`, `M30`).
**INTERPRETATION.** It is a PCB drill file with no observed relationship to this project. It
is retained as `unknown` rather than deleted or reclassified, because deletion is forbidden
and reclassification would be an inference.

---

## 6. Reconciliation against the 75-row migration manifest

`Project_Migration_Manifest_v1.csv` contains a header plus **exactly 75 data rows**. Every row
has a reconciliation status.

| Reconciliation status | Rows |
| --- | --- |
| `RECONCILED_BYTE_EXACT` — manifest digest observed in the corpus | **57** |
| `OBSERVED_NO_DECLARED_HASH_CORROBORATED` — file observed; manifest records no digest, but a contemporaneous index does and it matches | **7** |
| `OBSERVED_NO_DECLARED_HASH_UNCORROBORATED` — file observed; no digest anywhere | **7** |
| `NO_OBSERVED_FILE` | **4** |
| **Total** | **75** |

**No manifest row declares a digest that is observed nowhere.** Every 64-hex digest in the
manifest was located in the corpus.

### 6.1 The four rows with no observed file

| Manifest row | Manifest status | Note |
| --- | --- | --- |
| `Phase1_Audit_Log_Entry1-8` | HISTORICAL | Aggregate placeholder row. The **individual** Entry 1–8 files were all observed (§6.3). |
| `mr1b_ledger.json` | REFERENCED_BUT_NOT_AVAILABLE | See F-11. |
| `[Track A CNP-vs-AdaCNP materials]` | UNKNOWN | Expected absence — §9. |
| `[Track B frozen specifications and inputs]` | UNKNOWN | Expected absence under that literal name — §9. |

### 6.2 Finding F-02 — 16 of the 20 `REFERENCED_BUT_NOT_AVAILABLE` artifacts were located

**OBSERVED.** `Missing_or_Unrecoverable_Artifacts_v1.md` states that 20 of 75 catalogued
artifacts are `REFERENCED_BUT_NOT_AVAILABLE`. Sixteen of those 20 are present in the seven
roots — chiefly in `Downloads/Artifacts from the First Chat`, which the migration session
could not see.

| Recovery status | Count | Artifacts |
| --- | --- | --- |
| Recovered, byte-exact against the declared digest | 2 | `Milestone1_Decision_Record_DR1.md` (pre-ratification, `64e20f0c…`); `DRD_Input_Index_v1.md` (`9a4f15ee…`) |
| Recovered, byte-exact against a contemporaneous index (manifest itself declares no digest) | 7 | `ercot_load_adapter_v2.py` `953c5f8d…`; `ghcnh_stage0.py` `f56ab0c8…`; `audit_timestamp_lib.py` `17011dd6…`; `mr1a_inventory.csv` `c263df35…`; `mr1a_artifact_hashes_v2.txt` `a912c397…`; `mr1a_year_audit.csv` `0a4eeeb9…`; `ercot_hourly_load_harmonized_v2.csv.gz` `6410eb7f…` |
| Recovered, no prior digest exists anywhere (`FIRST_RECORDED_AT_MIGRATION`) | 7 | `event_inventory_S_QC1.csv`; `event_inventory_S_QC2.csv`; `mr1c_event_pipeline.py`; `mr1b_pi_hashes.csv`; `erco_raw_extract.csv`; `coverage_after_qc.csv`; `qc_excluded_by_code_station_year.csv` |
| Still not observed | 4 | the four rows in §6.1 |

**INTERPRETATION.** The migration report's recovery priority list is largely satisfiable from
material already on this machine. In particular all four "highest recovery priority" pipeline
sources — `ercot_load_adapter_v2.py`, `ghcnh_stage0.py`, `audit_timestamp_lib.py`,
`mr1c_event_pipeline.py` — are present, and the first three are byte-verified against
`DRD_Input_Index_v1.md` / `mr1a_artifact_hashes_v2.txt`. Re-derivation capability appears
recoverable. This is an observation about availability, not an import approval.

### 6.3 Finding F-03 — Audit Log Entries 1–8 are all present

**OBSERVED.** All eight entries exist:

| Entry | Copies | Content hash(es) |
| --- | --- | --- |
| 1 | 1 | `5835e6d9…` |
| 2 | 2 | `a5f314cd…` *and* `e5129550…` — **two different contents** |
| 3 | 2 | `11690ec0…` (identical) |
| 4 | 2 | `37b0a458…` (identical) |
| 5 | 1 | `d16ecefd…` |
| 6 | 1 | `df329b6f…` |
| 7 | 2 | `3b20f6d8…` (identical) |
| 8 | 2 | `1cb47a03…` (identical) |

**F-05 — OBSERVED.** `Phase1_Audit_Log_Entry2.md` exists in two conflicting versions
(8,609 B at `Artifacts from the First Chat`; 8,507 B at `7-28-26 8_38pm archive`). Neither has
a prior digest in any index. **The authoritative copy is NOT selected here**, per the
prohibition on adjudicating ambiguous evidence.

### 6.4 Finding F-04 — the DR-1 pre-ratification predecessor is present

**OBSERVED.** `Downloads/Artifacts from the First Chat/Milestone1_Decision_Record_DR1.md`
hashes to `64e20f0c9916a3665e8005cf58dccfef10943c6b6bd4dc3239b2752778ffc0fc`, exactly the
predecessor digest declared in the manifest and in the Missing-artifacts report. The active
`0780c4da…` copy is present at the migration root and in `7-28-26 8_38pm archive`.

**INTERPRETATION.** Both legitimate DR-1 versions are now held. The migration record's
standing instruction — the predecessor must be archived separately and must never replace the
active copy — is carried forward into the proposed manifest as a note, not acted upon.

### 6.5 Observed files with no manifest row

**OBSERVED.** 420 of 554 observed files match no manifest row by digest or by filename. Of
those, 300 are MR1c station-year parquet files, 29 are MR1b EIA-930 CSVs and batch ZIPs, and
28 are MR1a native-load files and bundles.

**INTERPRETATION.** This is expected and not a defect. The migration manifest catalogues
governance and derived artifacts held inside the migration session; it never catalogued the
PI-side raw retrieval corpus, which is why §3 of `Project_Migration_Manifest_v1.md` states no
Windows path could be recorded. The raw corpus carries its own provenance through
`MR1a/MR1b/MR1c` `hashes.csv` and `manifest.txt` (§11).

---

## 7. Migration-root results

### 7.1 Extracted top-level files

**OBSERVED.** 58 extracted top-level files, as expected. All 58 were readable and all 58
match `project_extracted_observed.sha256` byte-for-byte (58/58 MATCH, 0 mismatch).

### 7.2 ZIP integrity

**OBSERVED.** All four provenance ZIPs pass a full CRC integrity check
(`zipfile.testzip()` returned `None` for each) and match
`original_archives.sha256` (4/4 MATCH).

| Archive | Size (B) | SHA-256 | Integrity | Members |
| --- | --- | --- | --- | --- |
| `migration_shared_governance.zip` | 95,526 | `7acbdeda2fb4773a647d5819bb51a503f32bbbff8d1a006940a79c5bff55c906` | OK | 22 |
| `migration_runtime_data.zip` | 40,954,088 | `d227b97222b3ba5ed44e2425e0337fe857ea8d33884f68020c8a1d993642d1ca` | OK | 9 |
| `migration_source_code.zip` | 11,135 | `de48453557c78e436b5417f832c009ff10cb522c77cf993108bd6b59bb1a8aef` | OK | 3 |
| `migration_historical_archive.zip` | 134,330 | `88af8ca5200614fc1adab8cf53f4d84c24a4699c8843c489821f9bf1168ae1d4` | OK | 21 |
| | | | | **55** |

### 7.3 ZIP membership

**`migration_shared_governance.zip` (22)** — `Artifact_SHA256_Index_v7.md`,
`D11_Blocker_Memorandum_v1.md`, `DR1_Reconciliation_Memorandum_v1.md`,
`DRD_Package_Prepared_v5.md`, `ERCOT_Load_Quality_Report_v1.md`,
`Experiment_Freeze_Register_v1.md`, `MR1b_Findings_Table.md`,
`Mentor_Context___John_Brewer__NETL_.md`, `Mentor_Decision_Sheet_v5.md`,
`Milestone1_Decision_Record_DR1.md`, `Milestone1_Research_Specification_v0_1.md`,
`NETL_SULI_Internship_Project_Desc.md`, `Phase1_Audit_Log_Entry9.md` … `Entry15.md` (7 files),
`Phase1_to_DRD_Handoff_v1.md`, `V7_DL1_Correction_Record_v1.md`,
`v7_censoring_mapping_rule_v3.md`.

**`migration_runtime_data.zip` (9)** — `ercot_hourly_load_harmonized.csv`,
`event_inventory_headline.csv`, `gate_arithmetic.csv`,
`ghcnh_hourly_station_qcfiltered.parquet`, `operational_benchmark_erco.csv`,
`regional_index.parquet`, `v7_censoring_windows_v3.csv`, `v7_demand_censored_v3.csv`,
`zone_weights.json`.

**`migration_source_code.zip` (3)** — `noise_floor_simulation.py`, `v7_build_censoring_v3.py`,
`verify_e08.py`.

**`migration_historical_archive.zip` (21)** — `Artifact_SHA256_Index_v2.md` … `v6.md` (5),
`DRD_Package_Prepared_v1.md` … `v4.md` (4), `Mentor_Decision_Sheet_v1.md` … `v4.md` (4),
`v7_build_censoring_v1.py`, `v7_build_censoring_v2.py`, `v7_censoring_mapping_rule_v1.md`,
`v7_censoring_mapping_rule_v2.md`, `v7_censoring_windows_v1.csv`,
`v7_censoring_windows_v2.csv`, `v7_demand_censored_v1.csv`, `v7_demand_censored_v2.csv`.

### 7.4 Extracted-counterpart status — clean

**OBSERVED.** Each of the 55 ZIP members was hashed by streaming from the archive in memory
and compared with its extracted top-level counterpart.

- **55 / 55 MATCH.**
- **0 ZIP members without an extracted counterpart.**
- **0 ZIP members whose counterpart differs in content.**

ZIP members were **not** double-counted as separate candidates; the 4 archives are counted
once each as `provenance archive`, and their members are counted once each as the extracted
top-level files.

**OBSERVED.** 3 of the 58 extracted top-level files appear in no ZIP:
`Project_Migration_Manifest_v1.csv`, `Project_Migration_Manifest_v1.md`,
`Missing_or_Unrecoverable_Artifacts_v1.md`.
**INTERPRETATION.** These are the migration report itself, written after packaging. Their
mtimes (04:51) precede the archive mtimes (05:06) in the local copy but they are absent from
every archive's central directory, consistent with being companion documents rather than
packaged artifacts. Not a defect.

---

## 8. Candidate controlling documents and candidate authoritative inventories

### 8.1 Declared controlling set — all 13 verified byte-exact

**OBSERVED.** `Project_Migration_Manifest_v1.md` §5 declares a 13-item controlling set. Every
one was located at the migration root and every digest matches:

| Role | File | Declared | Observed | Copies in corpus |
| --- | --- | --- | --- | --- |
| Authority 1 | `Milestone1_Research_Specification_v0_1.md` | `7b6e2078…` | `7b6e2078…` | 2 |
| Authority 1 | `Milestone1_Decision_Record_DR1.md` | `0780c4da…` | `0780c4da…` | 2 (+1 predecessor) |
| Authority 2 | `Experiment_Freeze_Register_v1.md` | `9a7a35f2…` | `9a7a35f2…` | 3 |
| Authority 3 | `Phase1_Audit_Log_Entry15.md` | `a1391e33…` | `a1391e33…` | 2 |
| Authority 4 | `Phase1_to_DRD_Handoff_v1.md` | `f75803dc…` | `f75803dc…` | 3 |
| Authority 5 | `Artifact_SHA256_Index_v7.md` | `983452d3…` | `983452d3…` | 2 |
| Censoring data | `v7_demand_censored_v3.csv` | `3e7bd358…` | `3e7bd358…` | 2 |
| Censoring registry | `v7_censoring_windows_v3.csv` | `bc51b7c5…` | `bc51b7c5…` | 2 |
| Censoring rule | `v7_censoring_mapping_rule_v3.md` | `2984b799…` | `2984b799…` | 2 |
| Censoring builder | `v7_build_censoring_v3.py` | `c07898bc…` | `c07898bc…` | 2 |
| D11 analysis | `D11_Blocker_Memorandum_v1.md` | `be8aa526…` | `be8aa526…` | 2 |
| DRD package | `DRD_Package_Prepared_v5.md` | `b9641ad2…` | `b9641ad2…` | 2 |
| Mentor sheet | `Mentor_Decision_Sheet_v5.md` | `7b4a53b6…` | `7b4a53b6…` | 2 |

**13 / 13 byte-exact. Zero drift in the controlling set.**

### 8.2 Candidate authoritative event inventories

**OBSERVED.** Three candidate inventories exist, all with identical column headers
(`onset,recovery,peak,peak_val,hours,season,margin_C`) and 19 event rows:

| Candidate | SHA-256 | Copies | Manifest status | Prior hash |
| --- | --- | --- | --- | --- |
| `event_inventory_headline.csv` | `f119ba35…` (2,269 B) | 3 | `CONTROLLING`, artifact_type `frozen inventory` | MATCH |
| `event_inventory_S_QC1.csv` | `3c00b206…` (2,270 B) | 1 | `REFERENCED_BUT_NOT_AVAILABLE`, `sensitivity inventory` | `FIRST_RECORDED_AT_MIGRATION` |
| `event_inventory_S_QC2.csv` | `c5e52f67…` (2,271 B) | 1 | `REFERENCED_BUT_NOT_AVAILABLE`, `sensitivity inventory` | `FIRST_RECORDED_AT_MIGRATION` |

**OBSERVED.** S-QC1 differs from headline only in the `margin_C` column (uniform small shift).
S-QC2 differs in `margin_C` and additionally alters the 2023-01-31 event (`recovery`
`2023-02-02 17:00:00` → `18:00:00`, `hours` 60 → 61) and the `peak_val` of two events.
Event membership and onsets are otherwise identical across all three, matching the
description in `Missing_or_Unrecoverable_Artifacts_v1.md` §4.

**OBSERVED.** No column in any of the three inventories carries a timezone designator, and
no accompanying schema file states one.

**INTERPRETATION.** `event_inventory_headline.csv` is the strongest single candidate for the
authoritative inventory: it is the only one the migration manifest marks `CONTROLLING`, it is
the only one packaged in `migration_runtime_data.zip`, and its content is byte-stable across
three independent copies. **It is not certified authoritative here** — see IB-1 in §14, since
`Experiment_Freeze_Register_v1.md` lists the MR-1c event inventory as an item that closes only
at the Data Readiness Decision, which has not occurred.

### 8.3 Censoring evidence, issuance-time rules, partitions, feature registers

**OBSERVED**, located and hashed:

| Item | Artifact(s) |
| --- | --- |
| Censoring rule | `v7_censoring_mapping_rule_v1/v2/v3.md` (v3 CONTROLLING) |
| Censoring registry | `v7_censoring_windows_v1/v2/v3.csv` (v3 CONTROLLING) |
| Censoring data | `v7_demand_censored_v1/v2/v3.csv` (v3 CONTROLLING, 1,271 rows) |
| Censoring builder | `v7_build_censoring_v1/v2/v3.py` (v3 CONTROLLING) |
| Censoring correction record | `V7_DL1_Correction_Record_v1.md` |
| Issuance-time rule | `Milestone1_Decision_Record_DR1.md` AM-5 §3/§9; `Experiment_Freeze_Register_v1.md`; `D11_Blocker_Memorandum_v1.md` B3 |
| Event / buffer definitions | `Milestone1_Research_Specification_v0_1.md`; `DRD_Package_Prepared_v1.md` (LOEO, ±7-day buffers, max lag 168 h) |
| Feature register | `Experiment_Freeze_Register_v1.md` §3 (feature **classes** frozen) |
| Timestamp / DST evidence | `ERCOT_Load_Quality_Report_v1.md`; `audit_timestamp_lib.py`; `mr1a_year_audit.csv` |
| Prior pipeline code | `ercot_load_adapter_v2.py`, `ghcnh_stage0.py`, `audit_timestamp_lib.py`, `mr1c_event_pipeline.py`, `ingest_stage0_inventory.py`, `mr1b_*.py`, `noise_floor_simulation.py`, `verify_e08.py` |

**F-09 — OBSERVED, issuance time is provisional.** DR-1 AM-5 fixes the issuance cutoff at
09:00 local, day D−1, but the same record states the cutoff "is provisional and will be
finalized at the Data Readiness Decision." `Experiment_Freeze_Register_v1.md` lists it under
**OPEN**, and `D11_Blocker_Memorandum_v1.md` lists DP-5 as `[AWAITING RATIFICATION]`.

**F-10 — OBSERVED, timezone axis is proposed, not ratified.** `DRD_Package_Prepared_v1.md`
D5 records the proposed ruling "UTC is the single join axis for all three sources", with
GHCNh timestamps found unanimously UTC by the predeclared R3 diurnal test and EIA-930 aligned
at 100.00%. The DRD package carrying that ruling has migration status
`ACTIVE (PREPARED, PENDING RATIFICATION)`, and `Project_Migration_Manifest_v1.md` §5 records
that "no formal DRD has occurred · nothing self-ratified".

**INTERPRETATION.** Both the join timezone and the issuance cutoff are documented but
unratified. No timezone, schema, or issuance convention is inferred in this report.

### 8.4 Feature-register scope — exact tables do not exist

**OBSERVED.** `DRD_Package_Prepared_v1.md` states feature **classes** are frozen but "Exact
tables are not written." `Mentor_Decision_Sheet_v5.md` lists all seven D11 inputs — B1 Model A
feature table, B2 Model B feature table, B3 DP-5 issuance cutoff, B4 DP-6 lag semantics,
B5 DP-1 climatology base period, B6 W1 weighting vector, B7 CC-13 tuning protocol — as
unratified. `zone_weights.json` (the W1 vector) carries manifest status
`AWAITING RATIFICATION`.

---

## 9. Model A / Model B ↔ Track B naming correspondence

Per `NEXT_TASK.md`, historical Model A / Model B materials are treated as candidates for the
frozen benchmark now designated **Track B**, and the absence of CNP / AdaCNP material is
**not** an error.

**OBSERVED — definitions.** `Milestone1_Research_Specification_v0_1.md` §§ around lines
255–283 defines:

- **Model A — regime-agnostic probabilistic model**, one fixed quantile-model architecture and
  training procedure;
- **Model B — regime-aware probabilistic model**, identical to Model A except for the addition
  of predeclared regime features;
- line 494: "Quantile gradient boosting as the common Model A/Model B backbone."

**INTERPRETATION.** This matches the Track B definition in `PROJECT_CHARTER.md` — quantile-GBDT
Model A versus regime-aware quantile-GBDT Model B — with high confidence. The correspondence
is recorded; the frozen design is not altered.

**Proposed naming correspondence (recorded, not ratified):**

| Historical name | Current designation |
| --- | --- |
| Model A — regime-agnostic quantile GBDT | Track B, Model A |
| Model B — regime-aware quantile GBDT | Track B, Model B |
| Milestone 1 / MR-1a / MR-1b / MR-1c / Phase 1 / DRD corpus | SHARED foundation for Track A and Track B |
| *(no historical name)* | Track A — Standard CNP versus AdaCNP |

**OBSERVED — documents carrying Model A/B content** (candidate Track B controlling set):
`Milestone1_Research_Specification_v0_1.md`, `Milestone1_Decision_Record_DR1.md`,
`Experiment_Freeze_Register_v1.md`, `Phase1_to_DRD_Handoff_v1.md`,
`DRD_Package_Prepared_v1…v5.md`, `Mentor_Decision_Sheet_v1…v5.md`,
`D11_Blocker_Memorandum_v1.md`, `DR1_Reconciliation_Memorandum_v1.md`,
`V7_DL1_Correction_Record_v1.md`, `Phase1_Audit_Log_Entry1.md`, `Entry10.md`,
`Thursday_Execution_Briefing.md`.

**OBSERVED — Track A absence, as expected.** No historical artifact defines, implements, or
parameterises a Conditional Neural Process or AdaCNP. Both the migration manifest and
`Missing_or_Unrecoverable_Artifacts_v1.md` §1 record a zero-match content search. This is
**not** reported as an inventory failure.

### 9.1 Finding F-13 — governance conflict between ruling R-5 and the current Track A charter

**OBSERVED.** `Milestone1_Decision_Record_DR1.md` line 72 records:

> **R-5 — No neural architectures.** Reaffirmed. The contribution is the regime-aware
> uncertainty design and its evaluation, not model complexity.

R-5 is reaffirmed in `DR1_Reconciliation_Memorandum_v1.md`, restated in
`Experiment_Freeze_Register_v1.md`, and `Thursday_Execution_Briefing.md` line 140 states the
term AdaCNP "appears nowhere in the project record, and neural architectures are explicitly
excluded by mentor ruling R-5."

**OBSERVED.** `Missing_or_Unrecoverable_Artifacts_v1.md` §1 already raised this neutrally: if
Track A runs **inside** the NETL SULI project, R-5 governs and requires explicit mentor
amendment; if Track A is a **separate** project, R-5 does not reach it.

**OBSERVED.** `PROJECT_CHARTER.md` designates Track A (CNP versus AdaCNP) as the
primary active experiment, and requires both tracks to share the same frozen
scientific foundation — which is the foundation R-5 belongs to.

**INTERPRETATION and escalation.** This is a live conflict between the historical controlling
record and the current charter. It is **not** an inventory failure and does not stop this
inventory. It is not adjudicated here; only the decision authority can resolve it. It is
carried into §14 as import-blocking finding **IB-6**, because importing the SHARED foundation
without resolving it would silently import a prohibition against the primary active track.

---

## 10. Exact duplicates and name conflicts

### 10.1 Exact duplicates by SHA-256

**OBSERVED.** 67 duplicate groups: 56 groups of 2 copies, 11 groups of 3 copies. 145 files
participate; 78 are redundant copies. Full per-file detail, including which copy is the
primary and which are marked `DO_NOT_IMPORT_DUPLICATE`, is in
`PROPOSED_IMPORT_MANIFEST_001.csv` (`copies_of_this_content`, `is_primary_copy`).

**OBSERVED.** `Downloads/2nd Chat First File Dump` (9 files) contains **no unique content** —
all 9 are byte-identical to migration-root copies.

### 10.2 Same name, different content — 9 filenames

| Filename | Distinct contents | Copies | Detail |
| --- | --- | --- | --- |
| `ercot_hourly_load_harmonized.csv` | 2 | 3 | `272af17c…` (migration root, Downloads) vs `9f1817f7…` (8_38pm) — see F-06 |
| `ercot_hourly_load_harmonized.csv.gz` | 2 | 2 | `6410eb7f…` (First Chat) vs `e4d300b3…` (8_38pm) — see F-07 |
| `Milestone1_Decision_Record_DR1.md` | 2 | 3 | `0780c4da…` active vs `64e20f0c…` predecessor — F-04, both legitimate |
| `Phase1_Audit_Log_Entry2.md` | 2 | 2 | `a5f314cd…` vs `e5129550…` — F-05, unresolved |
| `Phase1_Data_Readiness_Audit_Plan.md` | 2 | 2 | `a96ecfe1…` (First Chat, 7,697 B) vs `3d5d709b…` (8_38pm, 7,625 B) — unresolved |
| `NETL_SULI_Research_Proposal_Regime_Aware_Forecasting.md` | 2 | 2 | `de72ce14…` (First Chat) vs `218afa12…` (8_38pm) — unresolved |
| `MR1a_Step_by_Step_Instructions.md` | 2 | 3 | `187e702b…` (7,630 B, two copies) vs `9ee4b5bb…` (7,648 B, Downloads) — unresolved |
| `hashes.csv` | 3 | 3 | Distinct per-milestone PowerShell hash snapshots in MR1a/MR1b/MR1c — not a conflict |
| `manifest.txt` | 3 | 3 | Distinct per-milestone retrieval manifests in MR1a/MR1b/MR1c — not a conflict |

**F-06 — OBSERVED and explained.** `8_38pm archive/ercot_hourly_load_harmonized.csv` hashes to
`9f1817f78d1bb56ad3c5ea08b95b83e235616bd90ff85809182841f36f09bb35`.
`mr1a_artifact_hashes_v2.txt` names this exact digest as "the stale attachment, pre-CC-8
content", produced by removing the `pre_apr2003_restated` column. The controlling content is
`272af17c…`, present at the migration root and in Downloads. **INTERPRETATION.** The 8_38pm
copy is a documented pre-CC-8 stale delivery. Flagged `HOLD_UNRESOLVED` pending PI direction;
it is not proposed for import.

**F-07 — OBSERVED and NOT explained.** `8_38pm archive/ercot_hourly_load_harmonized.csv.gz`
hashes to `e4d300b36fdbd56a8e86e660b9770ad5888e348e62a2ae136ddb5ad7ff55579e`. Both
`mr1a_artifact_hashes.txt` and `mr1a_artifact_hashes_v2.txt` declare the gzip digest as
`6410eb7f…`, which is the digest of the two `.gz` files in `Artifacts from the First Chat`.
**No document in the corpus explains `e4d300b3…`.** The gzip was **not** decompressed, so the
plausible reading that it is the gzip of the stale `9f1817f7…` CSV is **untested by design**.
Recorded as an unexplained mismatch; flagged `HOLD_UNRESOLVED` and carried into IB-2.

### 10.3 Same content, different name — 8 groups

**OBSERVED**, recorded because it affects filename-keyed reasoning:

| Content | Names |
| --- | --- |
| `7b6e2078…` | `Milestone1_Research_Specification_v0_1.md` / `Milestone1_Research_Specification_v0.1.md` |
| `8e48ab67…` | `Mentor_Decision_Sheet_v4.md` / `Mentor_Decision_Sheet_v4_1.md` |
| `7c8c5c72…` | `NETL_SULI_Research_Directions_Evaluation.md` / `…_1.md` |
| `de72ce14…` | `NETL_SULI_Research_Proposal_Regime_Aware_Forecasting.md` / `…_1.md` |
| `6410eb7f…` | `ercot_hourly_load_harmonized.csv.gz` / `ercot_hourly_load_harmonized_v2.csv.gz` |
| `953c5f8d…` | `ercot_load_adapter.py` / `ercot_load_adapter_v2.py` |
| `3b0de7c9…` | `mr1b_pi_hashes.csv` / `MR1b/hashes.csv` |
| `486094ca…` | `mr1b_pi_manifest.txt` / `MR1b/manifest.txt` |

**INTERPRETATION.** The last two are strong corroboration: the "not available" MR-1b
provenance files are byte-identical to the PI-side OneDrive snapshots. The `_v2` /`_1` pairs
are DL-1 delivery aliases and browser download-collision renames, consistent with the DL-1
rule recorded in `mr1a_artifact_hashes_v2.txt`.

---

## 11. Hash verification results

### 11.1 Prior-hash corpus assembled

**OBSERVED.** Prior digests were collected from every digest-bearing artifact found, not only
the discovery files. Path-keyed assertions take precedence over filename-keyed ones.

| Source | Digests | Keying |
| --- | --- | --- |
| `project_extracted_observed.sha256` | 58 | path |
| `original_archives.sha256` | 4 | path |
| `migration_documents.sha256` | 3 | path |
| `Project_Migration_Manifest_v1.csv` | 57 | name |
| `Artifact_SHA256_Index_v2…v7.md` | 25/29/26/23/7/7 | name |
| `DRD_Input_Index_v1.md` (2 copies) | 38 each | name |
| `MR1a/hashes.csv` | 25 | path |
| `MR1b/hashes.csv` | 23 | path |
| `MR1c/hashes.csv` | 288 | path |
| `mr1b_pi_hashes.csv` | 23 | path |
| `mr1a_artifact_hashes.txt` / `_v2.txt` | 7 each | name |
| `mr1a_inventory.csv` | 29 | name |

398 absolute paths and 437 filenames carry at least one asserted digest.

### 11.2 Results

| Status | Count |
| --- | --- |
| `PRIOR_HASH_MATCH` | **478** |
| `PRIOR_HASH_MISMATCH` | **6** |
| `FIRST_RECORDED_AT_MIGRATION` | **70** |
| **Total** | **554** |

Direct verification of the three discovery digest files was also run independently and is
clean: `project_extracted_observed.sha256` 58/58, `original_archives.sha256`
4/4, `migration_documents.sha256` 3/3. All **336** files covered by the PI-side
PowerShell snapshots match exactly: MR1a 25/25, MR1b 23/23, MR1c 288/288. Root totals:
MR1a 28/28 verified, MR1b 23 verified + 6 batch ZIPs first-recorded + 2 name-collision
(F-08), MR1c 288 verified + 10 first-recorded + 2 name-collision (F-08).

### 11.3 The 6 mismatches

**Substantive (2)** — carried into IB-2:

| Path | Observed | Asserted | Assessment |
| --- | --- | --- | --- |
| `8_38pm archive/ercot_hourly_load_harmonized.csv` | `9f1817f7…` | `272af17c…` | F-06 — documented stale pre-CC-8 delivery |
| `8_38pm archive/ercot_hourly_load_harmonized.csv.gz` | `e4d300b3…` | `6410eb7f…` | F-07 — **unexplained** |

**F-08 — Name-collision artifacts, not drift (4).**
**OBSERVED.** `MR1b/hashes.csv`, `MR1c/hashes.csv`, `MR1b/manifest.txt`, `MR1c/manifest.txt`
have no digest asserted for their own paths. The only assertions for those *basenames* come
from `mr1a_inventory.csv`, which records `6cc0e2ca…` for `hashes.csv` and `c6aeb44e…` for
`manifest.txt`. Both of those digests are observed exactly — at `MR1a/hashes.csv` and
`MR1a/manifest.txt`. **INTERPRETATION.** The mismatch is a consequence of filename-keyed
matching across three milestone directories that reuse the same two filenames. There is no
evidence of content drift. These four are labelled `AMBIGUOUS_BASENAME_ONLY_NOT_DRIFT` in the
CSV and are **not** treated as import blockers.

### 11.4 `FIRST_RECORDED_AT_MIGRATION` — 70 items

**OBSERVED.** 70 files have no prior digest in any available source and are recorded here for
the first time.

| Root | Count | Character of the items |
| --- | --- | --- |
| `Artifacts from the First Chat` | 34 | Audit Log Entries 1–8, MR1b/MR1c checklists, `ledger.json`, `mr1b_pi_*`, `erco_raw_extract.csv`, `coverage_after_qc.csv`, `qc_excluded_by_code_station_year.csv`, `event_inventory_S_QC1/2.csv`, `ghcnh_hourly_station.parquet`, `mr1c_event_pipeline.py`, `ingest_stage0_inventory.py`, `mr1b_*.py`, `mr1a_artifact_hashes.txt`, research proposals/evaluations |
| `7-28-26 8_38pm archive` | 14 | `.docx`, `.pptx`, `files.zip (3).zip`, MR1a checklists, Audit Log Entries 2/3/4/7, research proposals/evaluations |
| `OneDrive/MR1c` | 10 | 9 `MR1c_batch*.zip` retrieval bundles + `missing_files.txt` (0 B) |
| `OneDrive/MR1b` | 6 | 6 `MR1b_batch*.zip` retrieval bundles |
| `Downloads` (top level) | 6 | `Class_4.drd`, `MR1a_Step_by_Step_Instructions.md`, `Mentor_Decision_Sheet_v4_1.md`, `Milestone1_Research_Specification_v0.1.md`, `Phase1_Audit_Log_Entry8.md`, `project-handoff-files.zip` |

**INTERPRETATION.** Three of these are byte-identical to files that *do* carry prior digests
under a different name (§10.3), so their content is in fact corroborated:
`Mentor_Decision_Sheet_v4_1.md`, `Milestone1_Research_Specification_v0.1.md`, and
`mr1b_pi_hashes.csv`/`mr1b_pi_manifest.txt`. The rest are genuinely first recorded now.

**F-11 — OBSERVED.** `Artifacts from the First Chat/ledger.json` (53,494 B) is a JSON object
with keys `zips` (6 entries) and `files` (25 entries). All 23 digests in `mr1b_pi_hashes.csv`
appear in it, plus the 6 `MR1b_batch*.zip` digests. **INTERPRETATION.** It is a strong
candidate for the manifest row `mr1b_ledger.json`. The filename differs and no digest was ever
documented, so **the correspondence is NOT adjudicated here**.

---

## 12. Reconciliation against `candidates.tsv`

**OBSERVED.**

- `candidates.tsv` holds 454 rows.
- **0** `candidates.tsv` entries are missing from the filesystem.
- **0** size drift between `candidates.tsv` and observed sizes for the 454 common entries.
- **100** observed files appear in no `candidates.tsv` row: 62 under the migration root (which
  was created at 04:51, after `candidates.tsv` was written at 04:35) and **38 under the other
  six roots**.

**F-14 — OBSERVED.** The 38 under-enumerated files break down as: MR1a 14 (11 annual
native-load ZIPs, `native_load_2015.xls`, `hashes.csv`, `manifest.txt`), `Artifacts from the
First Chat` 10, `7-28-26 8_38pm archive` 8, MR1c 3, MR1b 2, `2nd Chat First File Dump` 1.
`candidates.tsv` does contain `.zip` (17), `.xls` (13) and `.txt` (3) rows, so a simple
extension filter does not explain the gap; it contains no `.docx` or `.pptx` rows.

**INTERPRETATION.** The cause is not determinable from the supplied inputs and is not
inferred. `candidates.tsv` is a strict subset of what is present. Because `NEXT_TASK.md`
scopes the inventory to a recursive walk of the seven roots and treats `candidates.tsv` as
"the original discovery list to reconcile against" rather than as the scope itself, the full
walk was used and the shortfall is reported here. This reduces confidence in
`candidates.tsv` as a completeness reference; it does not affect the inventory's coverage.

---

## 13. Missing, unreadable, ambiguous, and conflicting items

**Missing:** 0 files. All 41 named Downloads candidates and all 454 `candidates.tsv` entries
were present. The only "missing" entries are the 4 manifest rows in §6.1, three of which are
placeholder or aggregate rows rather than files.

**Unreadable / permission-denied:** 0. Every one of the 554 candidates was opened and hashed
successfully. No stat error, no read error, no non-regular file.

**Ambiguous (7):**

| Item | Why ambiguous |
| --- | --- |
| `Phase1_Audit_Log_Entry2.md` | Two contents, no prior digest for either (F-05) |
| `Phase1_Data_Readiness_Audit_Plan.md` | Two contents, no prior digest for either |
| `NETL_SULI_Research_Proposal_Regime_Aware_Forecasting.md` | Two contents, no prior digest for either |
| `MR1a_Step_by_Step_Instructions.md` | Two contents, no prior digest for either |
| `ledger.json` | Candidate `mr1b_ledger.json`, name differs, no documented digest (F-11) |
| `project-handoff-files.zip`, `files.zip (3).zip` | Undocumented archives; not opened |
| `Class_4.drd`, `.docx`, `.pptx` | No manifest row, purpose not verifiable without opening binaries (F-12) |

**Conflicting (2 substantive):** F-06 and F-07 in §10.2.

**Adverse conditions encountered and continued through, per `NEXT_TASK.md` §Inventory
behavior:** conflicting candidate copies (F-05, F-06, F-07), recorded hashes not matching
files (F-06, F-07), a discovery input revised after an earlier digest (F-01), a discovery list
that under-enumerates its own roots (F-14), absent prior hashes (70 items), unresolved
timezone and issuance conventions (F-09, F-10), and a governance conflict (F-13). None
terminated the inventory. Every one is recorded.

---

## 14. Import-blocking findings

The inventory completed. Separately, **no import may be approved** while the following stand.
These map to the conditions listed in `NEXT_TASK.md` §Import-blocking conditions.

| ID | Blocking condition | Evidence | Affects |
| --- | --- | --- | --- |
| **IB-1** | The authoritative event inventory is not uniquely *ratified*. `event_inventory_headline.csv` is manifest-`CONTROLLING`, but `Experiment_Freeze_Register_v1.md` places the MR-1c event inventory among the items that close only at the Data Readiness Decision, and no DRD has occurred. Two sensitivity variants exist with no recorded digests. | §8.2 | `event_inventory_headline.csv`, `event_inventory_S_QC1.csv`, `event_inventory_S_QC2.csv` |
| **IB-2** | A recorded hash does not match its file. `8_38pm archive/ercot_hourly_load_harmonized.csv.gz` = `e4d300b3…` versus declared `6410eb7f…`, unexplained by any document (F-07). The companion `.csv` mismatch (F-06) is explained but still requires a PI ruling on retention. | §10.2, §11.3 | 2 files, both `HOLD_UNRESOLVED` |
| **IB-3** | Schema and timezone conventions remain unresolved. The UTC join axis is *proposed* in a DRD package marked `PENDING RATIFICATION`; the 09:00 CT D−1 issuance cutoff is `[AWAITING RATIFICATION]` (DP-5). The event inventories carry no timezone designator in any column or schema file. | F-09, F-10, §8.2 | all shared time-indexed data |
| **IB-4** | Controlling-versus-descriptive status is unclear for artifacts marked `AWAITING RATIFICATION` or `PROVISIONAL`: `zone_weights.json` (W1 vector), `DRD_Package_Prepared_v5.md`, `noise_floor_simulation.py`, `verify_e08.py` (explicitly "not a governed artifact"). The seven D11 inputs B1–B7 are all unratified. | §8.4, migration manifest | 4+ artifacts |
| **IB-5** | Manifest rows that cannot be tied to an observed file, and observed files whose purpose is unresolved: 4 unreconciled manifest rows (§6.1) and 5 `unknown` artifacts (§5.1). | §5.1, §6.1 | 9 items |
| **IB-6** | **Candidate controlling artifacts materially disagree with the current charter.** Ruling R-5 ("No neural architectures. Reaffirmed.") is part of the SHARED controlling record that both tracks are required to inherit, and it prohibits the architecture family of the primary active track. Only the decision authority can resolve whether Track A sits inside or outside the NETL SULI project. | §9.1 | the entire SHARED foundation |
| **IB-7** | Four same-name/different-content pairs have no prior digest on either side, so neither copy can be certified: `Phase1_Audit_Log_Entry2.md`, `Phase1_Data_Readiness_Audit_Plan.md`, `NETL_SULI_Research_Proposal_Regime_Aware_Forecasting.md`, `MR1a_Step_by_Step_Instructions.md`. | §10.2 | 8 files |

**Conditions checked and NOT blocking:**

- ZIP integrity — all four archives pass CRC; 55/55 members have byte-exact extracted
  counterparts; 0 missing, 0 differing.
- The 13-item declared controlling set — 13/13 byte-exact, zero drift.
- Raw source-data provenance — all 336 files covered by the MR1a/MR1b/MR1c PI-side snapshots
  match exactly (25 + 23 + 288).
- The four name-collision "mismatches" in F-08 — no evidence of drift.

---

## 15. Unresolved questions for the decision authority

1. **IB-6 / R-5.** Does Track A run inside the NETL SULI project (in which case R-5 requires
   explicit mentor amendment before any CNP or AdaCNP work), or is it a separate project?
   Everything about the repository's shared-foundation layout depends on the answer.
2. Is `event_inventory_headline.csv` (`f119ba35…`) accepted as the frozen event inventory for
   both tracks ahead of a formal DRD, or does it remain provisional?
3. Is the UTC join axis and the 09:00 CT D−1 issuance cutoff adopted as-is for repository
   purposes, or does import wait on the Data Readiness Decision?
4. Which `Phase1_Audit_Log_Entry2.md` is authoritative — `a5f314cd…` or `e5129550…`? Same
   question for the three other unresolved pairs in IB-7.
5. Should the unexplained gzip `e4d300b3…` be investigated (which would require decompressing
   it — not authorized under this task), quarantined, or discarded?
6. Is `ledger.json` the artifact the manifest calls `mr1b_ledger.json`?
7. Should the 359-file raw source corpus under `MR1a`/`MR1b`/`MR1c` be referenced in place
   rather than copied? The proposed manifest assumes reference-in-place; the corpus is
   1,588,690,040 B (1.59 GB) and copying it would contradict "no large file is copied into
   the repository."
8. Should `ercot_hourly_load_harmonized.csv` be restored to the `_v2` name on import, as
   `Project_Migration_Manifest_v1.md` §6 suggests, so filename and content version cannot
   drift apart?
9. Are the SULI `.docx` / `.pptx` program materials in scope for the repository at all?

---

## 16. Proposed import manifest

`docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv` — 554 rows plus header, one row per candidate.

Columns: `sha256`, `source_root`, `relative_path`, `absolute_source_path`, `size_bytes`,
`mtime_utc`, `format`, `classification`, `classification_basis`, `track_assignment`,
`manifest_row`, `manifest_status`, `prior_hash_status`, `prior_hash_sources`,
`copies_of_this_content`, `is_primary_copy`, `import_recommendation`, `import_blocking`,
`notes`.

| `import_recommendation` | Rows | Meaning |
| --- | --- | --- |
| `REFERENCE_IN_PLACE_DO_NOT_COPY` | 352 | Raw source data; reference by hash, do not copy into the repository |
| `PROPOSE_IMPORT` | 84 | Primary copies of governing documents, control artifacts, derived data, source code, manifests, result artifact |
| `DO_NOT_IMPORT_DUPLICATE` | 78 | Byte-identical to a higher-precedence primary |
| `IMPORT_TO_ARCHIVE_ONLY` | 29 | Manifest-`SUPERSEDED` or `HISTORICAL`; retain for provenance, never as controlling |
| `HOLD_UNRESOLVED` | 7 | 5 `unknown` items + the 2 substantive hash mismatches |
| `IMPORT_AS_PROVENANCE_REFERENCE` | 4 | The four `_original_archives` ZIPs |

**These are proposals only. No import is authorized by this document, and IB-1 through IB-7
stand against all of them.**

---

## 17. Acceptance criteria

| Criterion | Status |
| --- | --- |
| No source artifact changed, extracted, or re-extracted | **MET** — read-only throughout; no archive extracted |
| Only the seven roots in `source_roots.txt` walked | **MET** |
| Only the 41 named top-level Downloads files inspected | **MET** — Downloads itself was not walked |
| Every listed artifact has a SHA-256 computed by streaming | **MET** — 554/554, 1 MiB blocks |
| Every listed artifact has a classification | **MET** — 554/554 |
| Unknown items remain explicitly classified `unknown` | **MET** — 5 items |
| Duplicates and conflicting copies reported | **MET** — 67 groups, 9 name conflicts, 8 same-content/different-name groups |
| Every one of the 75 manifest rows has a reconciliation status | **MET** — 57 + 7 + 7 + 4 = 75 |
| ZIP members not double-counted against extracted copies | **MET** |
| No large file copied into the repository | **MET** — nothing copied |
| Output distinguishes observed facts from interpretations | **MET** — OBSERVED / INTERPRETATION markers |
| `git diff` shows changes only under `docs/audit/` | **MET** — see §19 |

---

## 18. Recommended next bounded task

**Recommended: `TRACK-SCOPE-RULING-001` — resolve IB-6 before any import.**

Rationale: IB-6 is upstream of everything else. If R-5 governs Track A, the SHARED foundation
cannot be imported as-is without an explicit mentor amendment, and the repository's dual-track
layout needs to change. If Track A is a separate project, R-5 does not reach it and the SHARED
foundation imports cleanly. Every other blocker is narrower and can be worked in parallel or
afterwards. This task is a decision, not an implementation: it produces one entry in
`docs/project/DECISION_LOG.md` and requires no code, no data movement, and no modelling.

Suggested follow-on sequence, each separately authorized:

1. `TRACK-SCOPE-RULING-001` — resolve IB-6 (decision authority only).
2. `CONFLICT-ADJUDICATION-001` — rule on IB-7's four pairs, F-06/F-07 retention, and the
   `ledger.json` correspondence. Evidence is already in this report; no new scanning needed.
3. `CONTROLLING-SET-IMPORT-001` — import only the 13 byte-exact controlling artifacts plus
   the four provenance ZIP digests, under an explicit ruling on IB-3 and IB-4.
4. `SOURCE-DATA-REFERENCE-001` — establish hash-referenced, copy-free access to the 359-file
   raw corpus under `MR1a`/`MR1b`/`MR1c`.

---

## 19. Repository state at completion

```
$ git diff --check
(no output)

$ git status --short
?? docs/audit/ARTIFACT_INVENTORY_001.md
?? docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv
```

Two files were written, both new, both under `docs/audit/`:

1. `docs/audit/ARTIFACT_INVENTORY_001.md`
2. `docs/audit/PROPOSED_IMPORT_MANIFEST_001.csv`

Nothing was written to `data/`, `artifacts/`, `runs/`, `src/`, `configs/`, or `tests/`.
`.gitignore` and the `data/frozen` policy are unmodified. Nothing was committed.
This task stops here for approval.
