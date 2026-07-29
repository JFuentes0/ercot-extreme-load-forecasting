"""Minimal verified import for TRACK-A-REAL-DATA-READINESS-001 workstream 2.

Imports only artifacts whose governing status can be established from an adopted
decision or from the declared controlling set in ARTIFACT_INVENTORY_001.md.

Every row is hash-verified at source before copying and at destination after
copying. A row whose eight manifest fields cannot all be completed is not
importable; the contract requires reporting it and continuing with the rest.

Artifacts deliberately NOT imported by this script are recorded in
DEFERRED_ROLES with the reason, so the omission is visible rather than silent.

Usage:
    python scripts/import_track_a_minimal.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIGRATION_ROOT = Path("/mnt/c/Users/fuent/Documents/ERCOT_Project_Migration_2026-07-29")
MANIFEST_OUT = REPO / "docs" / "audit" / "TRACK_A_IMPORT_MANIFEST_001.csv"


@dataclass(frozen=True)
class ImportRow:
    """One importable artifact, with all eight contract-required fields."""

    source_path: Path
    expected_sha256: str
    destination: Path
    purpose: str
    governing_status: str
    governing_decision: str
    blocker_check: str
    source_sha256: str = ""
    destination_sha256: str = ""


@dataclass(frozen=True)
class DeferredRole:
    """A required role that could not be identified; reported, not imported."""

    role: str
    reason: str
    candidates: tuple[str, ...] = field(default=())


#: D-009 adopts the load artifact by content, not filename. Both the complete
#: digest and this exact byte size must match before the file may be copied.
ADOPTED_LOAD_SHA256 = "272af17cd1b2df14b921756738c6625b22c7702a6d14139886c3ff32728689eb"
ADOPTED_LOAD_BYTES = 54_688_032

IMPORTS: tuple[ImportRow, ...] = (
    ImportRow(
        source_path=MIGRATION_ROOT / "ercot_hourly_load_harmonized.csv",
        expected_sha256=ADOPTED_LOAD_SHA256,
        destination=(
            REPO / "data" / "frozen" / "track_a" / "ercot_hourly_load_harmonized.csv"
        ),
        purpose=(
            "Controlling harmonized ERCOT load artifact; Track A target series "
            "and the axis from which the load-eligibility span is derived."
        ),
        governing_status="CONTROLLING",
        governing_decision="D-009",
        blocker_check=(
            "IB-2 bounded disposition under D-009: this content is adopted; the "
            "stale 9f1817f7 content is excluded; the unexplained e4d300b3 gzip "
            "is governance-quarantined and is not read, decompressed, or "
            "compared here. IB-2 remains open as a provenance issue and no "
            "longer blocks the stage-3 path. Not IB-4 (not AWAITING "
            "RATIFICATION), not IB-5 (reconciled), not IB-7 (whose four pairs "
            "are documentation files, not this artifact). Selection is by "
            "complete digest and exact byte size, never by filename."
        ),
    ),
    ImportRow(
        source_path=MIGRATION_ROOT / "event_inventory_headline.csv",
        expected_sha256=(
            "f119ba35f2c4fc1c931c21c03a82f7fd198384fc32fac2f665071fc0883dfe5a"
        ),
        destination=REPO / "data" / "shared" / "event_inventory_headline.csv",
        purpose="Controlling headline event inventory; LOEO fold definition",
        governing_status="CONTROLLING",
        governing_decision="D-006",
        blocker_check=(
            "Clear. The proposed manifest flags IB-1 and IB-3 on this row, but both "
            "are RESOLVED: D-006 adopts this exact file as the controlling headline "
            "inventory and D-007 adopts the UTC/America-Chicago conventions. The "
            "flag predates those decisions and is stale. Not IB-2 (prior hash "
            "MATCH), not IB-4 (not AWAITING RATIFICATION), not IB-5 (reconciled), "
            "not IB-7 (single content hash across all three copies)."
        ),
    ),
    ImportRow(
        source_path=MIGRATION_ROOT / "v7_demand_censored_v3.csv",
        expected_sha256=(
            "3e7bd358d7bb39527c367f1070b958fe2715397abd54b8275cfca30474077406"
        ),
        destination=REPO / "data" / "frozen" / "track_a" / "v7_demand_censored_v3.csv",
        purpose=(
            "Censoring-status artifact. Stage-4 gating evidence only; NOT applied "
            "to stage-3 scoring (freeze 11.1, D-008)."
        ),
        governing_status="CONTROLLING",
        governing_decision=(
            "D-008 + NEXT_TASK.md workstream-2 artifact class 5 (censoring-status "
            "artifact). Corroborating evidence, not authority: "
            "ARTIFACT_INVENTORY_001.md 8.1 declared controlling set, 13/13 "
            "byte-exact. That document authorizes no import on its own."
        ),
        blocker_check=(
            "Clear of IB-2/4/5/7. Member of the 13-item declared controlling set, "
            "13/13 byte-exact, zero drift. No import_blocking flag."
        ),
    ),
    ImportRow(
        source_path=MIGRATION_ROOT / "v7_censoring_windows_v3.csv",
        expected_sha256=(
            "bc51b7c53b58a7a7a7aff2fb4c1a572307dcc03aa4e692571363ad6f44f99af7"
        ),
        destination=(
            REPO / "data" / "frozen" / "track_a" / "v7_censoring_windows_v3.csv"
        ),
        purpose="Censoring window registry; interprets the censoring-status artifact",
        governing_status="CONTROLLING",
        governing_decision=(
            "D-008 + NEXT_TASK.md workstream-2 artifact class 5 (censoring-status "
            "artifact). Corroborating evidence, not authority: "
            "ARTIFACT_INVENTORY_001.md 8.1 declared controlling set, 13/13 "
            "byte-exact. That document authorizes no import on its own."
        ),
        blocker_check=(
            "Clear of IB-2/4/5/7. Member of the 13-item declared controlling set. "
            "No import_blocking flag."
        ),
    ),
    ImportRow(
        source_path=MIGRATION_ROOT / "v7_censoring_mapping_rule_v3.md",
        expected_sha256=(
            "2984b7993c3903c789dc8035d404b6133ca3e5a7d8e9f9e22ca9981478712f9a"
        ),
        destination=(
            REPO / "data" / "frozen" / "track_a" / "v7_censoring_mapping_rule_v3.md"
        ),
        purpose="Censoring mapping rule; required to interpret the censoring states",
        governing_status="CONTROLLING",
        governing_decision=(
            "D-008 + NEXT_TASK.md workstream-2 artifact class 5 (censoring-status "
            "artifact). Corroborating evidence, not authority: "
            "ARTIFACT_INVENTORY_001.md 8.1 declared controlling set, 13/13 "
            "byte-exact. That document authorizes no import on its own."
        ),
        blocker_check=(
            "Clear of IB-2/4/5/7. Member of the 13-item declared controlling set. "
            "No import_blocking flag."
        ),
    ),
)


DEFERRED_ROLES: tuple[DeferredRole, ...] = (
    DeferredRole(
        role="Weather input required by the frozen Track A feature design",
        reason=(
            "Two plausible CONTROLLING candidates and no frozen feature table to "
            "choose between them. EXPERIMENT_FREEZE_v1.md does not name a weather "
            "artifact, and ARTIFACT_INVENTORY_001.md 8.4 records that exact feature "
            "tables do not exist. Contract requires stop-and-report rather than "
            "choosing between plausible candidates."
        ),
        candidates=(
            "ghcnh_hourly_station_qcfiltered.parquet (CONTROLLING)",
            "regional_index.parquet (CONTROLLING)",
        ),
    ),
    DeferredRole(
        role="Zone weights (schema/interpretation support)",
        reason=(
            "zone_weights.json carries manifest status AWAITING RATIFICATION and is "
            "flagged IB-4. The contract prohibits importing AWAITING RATIFICATION "
            "artifacts without separate approval. Whether the frozen Track A "
            "feature design requires zone weighting at all is undetermined."
        ),
        candidates=("zone_weights.json dee723a7... (AWAITING RATIFICATION, IB-4)",),
    ),
    DeferredRole(
        role="Load-eligibility information — RETIRED, no import needed",
        reason=(
            "No standalone eligibility artifact is required. The pre-existing rule "
            "was located in executable form in the hash-verified controlling "
            "builder v7_build_censoring_v3.py (c07898bc, lines 223-241): an event "
            "is load-eligible iff onset >= lo and recovery <= hi, where lo/hi are "
            "the min/max ts_utc of the D-009 load artifact after dropping "
            "dup_anomaly rows and asserting UTC-axis uniqueness. It is therefore "
            "derivable from the D-006 inventory and the D-009 load artifact "
            "alone, and is implemented in track_a.event_eligibility. Counts are "
            "derived at run time and are deliberately not restated here: freeze "
            "10.1 forbids an event or fold count as a literal in code, "
            "configuration, tests, or reports."
        ),
    ),
)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    completed: list[ImportRow] = []
    failures: list[str] = []

    print("=== SOURCE VERIFICATION (before copying) ===")
    for row in IMPORTS:
        if not row.source_path.is_file():
            failures.append(f"MISSING SOURCE: {row.source_path}")
            print(f"  MISSING  {row.source_path}")
            continue
        actual = sha256_of(row.source_path)
        ok = actual == row.expected_sha256

        # D-009 adopts the load artifact by content AND size. Both must match.
        if row.expected_sha256 == ADOPTED_LOAD_SHA256:
            observed_bytes = row.source_path.stat().st_size
            if observed_bytes != ADOPTED_LOAD_BYTES:
                ok = False
                failures.append(
                    f"SIZE MISMATCH (D-009): {row.source_path}\n"
                    f"  expected {ADOPTED_LOAD_BYTES} bytes\n"
                    f"  actual   {observed_bytes} bytes"
                )
            else:
                print(f"  OK    size {observed_bytes} bytes matches D-009")

        print(f"  {'OK  ' if ok else 'FAIL'}  {row.source_path.name}  {actual[:16]}")
        if not ok:
            failures.append(
                f"SOURCE HASH MISMATCH: {row.source_path}\n"
                f"  expected {row.expected_sha256}\n  actual   {actual}"
            )
            continue
        completed.append(
            ImportRow(
                **{
                    **row.__dict__,
                    "source_sha256": actual,
                }
            )
        )

    if failures:
        print("\n=== ABORTING: source verification failed ===")
        for f in failures:
            print(f"  {f}")
        return 1

    if args.dry_run:
        print("\n--dry-run: no files copied")
        return 0

    print("\n=== COPY + DESTINATION VERIFICATION (after copying) ===")
    finalized: list[ImportRow] = []
    for row in completed:
        row.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row.source_path, row.destination)
        dest_hash = sha256_of(row.destination)
        if dest_hash != row.source_sha256:
            failures.append(
                f"DESTINATION HASH MISMATCH: {row.destination}\n"
                f"  source {row.source_sha256}\n  dest   {dest_hash}"
            )
            print(f"  FAIL  {row.destination.relative_to(REPO)}")
            continue
        print(
            f"  OK    {row.destination.relative_to(REPO)}  "
            f"{dest_hash[:16]}  (equals source)"
        )
        finalized.append(ImportRow(**{**row.__dict__, "destination_sha256": dest_hash}))

    if failures:
        print("\n=== ABORTING: destination verification failed ===")
        for f in failures:
            print(f"  {f}")
        return 1

    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_OUT, "w", newline="", encoding="utf-8") as handle:
        # csv.writer defaults to CRLF; force LF so the committed manifest does
        # not carry a stray \r on every line.
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "source_path",
                "source_sha256",
                "source_bytes",
                "destination_path",
                "destination_sha256",
                "destination_bytes",
                "hashes_equal",
                "sizes_equal",
                "purpose",
                "governing_status",
                "governing_decision",
                "blocker_check",
            ]
        )
        for row in finalized:
            source_bytes = row.source_path.stat().st_size
            destination_bytes = row.destination.stat().st_size
            writer.writerow(
                [
                    str(row.source_path),
                    row.source_sha256,
                    source_bytes,
                    str(row.destination.relative_to(REPO)),
                    row.destination_sha256,
                    destination_bytes,
                    "TRUE" if row.source_sha256 == row.destination_sha256 else "FALSE",
                    "TRUE" if source_bytes == destination_bytes else "FALSE",
                    row.purpose,
                    row.governing_status,
                    row.governing_decision,
                    row.blocker_check,
                ]
            )

    print(f"\n=== MANIFEST WRITTEN: {MANIFEST_OUT.relative_to(REPO)} ===")
    print(f"  rows imported: {len(finalized)}")

    print("\n=== ROLES DEFERRED (reported, not imported) ===")
    for deferred in DEFERRED_ROLES:
        print(f"  ROLE: {deferred.role}")
        print(f"    reason: {deferred.reason}")
        for candidate in deferred.candidates:
            print(f"    candidate: {candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
