# Shared Partition Specification

Status: Pending import and verification from the existing project record.

The authoritative partition implementation must preserve:

- the frozen ERCOT cold-event inventory;
- load-eligible event IDs;
- exact UTC event boundaries;
- plus/minus-7-day event buffers;
- leave-one-event-out outer folds;
- exclusion of each held-out event and its buffer from training;
- source inventory and partition hashes.

Neither Track A nor Track B may independently redefine event membership.

No partition code may be implemented until the authoritative event artifact
has been imported and hash-verified.
