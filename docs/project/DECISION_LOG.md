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
