# Project Charter

## Project

ERCOT Extreme-Load Forecasting

## Decision authority

Jonathan Fuentes is the final project decision authority.

## Primary active experiment

Track A compares:

- Standard Conditional Neural Process using uniform mean aggregation.
- Adaptive Conditional Neural Process using target-conditioned adaptive
  weighting of the same context representations.

The primary research question is whether learned target-aware weighting of
historical examples improves probabilistic forecasting during held-out ERCOT
extreme-cold events.

## Secondary frozen experiment

Track B compares:

- Quantile-gradient-boosting Model A.
- Regime-aware quantile-gradient-boosting Model B.

Track B retains its frozen scientific design and may be executed only when a
task explicitly states TRACK=B.

## Shared foundation

Both tracks must use the same:

- frozen ERCOT cold-event inventory;
- leave-one-event-out outer partitions;
- plus/minus-7-day event buffers;
- issuance-time conventions;
- source-data hashes;
- censoring evidence;
- leakage protections.

## Current priority

Repository and protocol preparation for Track A.

No held-out-event model prediction is authorized during repository setup.
