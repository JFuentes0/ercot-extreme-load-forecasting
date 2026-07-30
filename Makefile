.RECIPEPREFIX := >

# The `track-a-smoke` and `track-b-smoke` targets previously invoked
# `scripts.track_a.run` and `scripts.track_b.run`, neither of which exists --
# `scripts/track_a/` holds only a .gitkeep and `scripts/` has no __init__.py, so
# both targets could never resolve. They are replaced by targets that point at
# the scripts that actually exist.

.PHONY: \
	shared-verify \
	track-a-test \
	track-a-smoke \
	track-b-test \
	import \
	stage3 \
	stage4 \
	aggregate \
	check

shared-verify:
> uv run pytest tests/shared tests/leakage tests/reproducibility -q

track-a-test:
> uv run pytest tests/track_a -q

# Synthetic CPU smoke training only (freeze stages 1-2). Reads no real artifact.
track-a-smoke:
> uv run pytest tests/track_a/test_training_smoke.py tests/track_a/test_uniform_equivalence.py -q

track-b-test:
> uv run pytest tests/track_b -q

# --- real-data entry points (each states its own governing decision) ---------

# Hash-verified minimal import (D-008, D-009, D-012). Supports --dry-run.
import:
> uv run python scripts/import_track_a_minimal.py

# Stage 3, non-event periods only (D-008).
stage3:
> uv run python scripts/run_stage3.py

# Stage 4 exploratory held-out-event grid (D-011). Refuses to run unless the run
# plan authorizes stage 4 with no outstanding gates.
stage4:
> uv run python scripts/run_stage4.py

# Aggregate non-event comparison -- the paper-comparable setting (D-008 scope).
aggregate:
> uv run python scripts/run_aggregate_comparison.py

check:
> uv run ruff check .
> uv run ruff format --check .
> uv run pytest -q
