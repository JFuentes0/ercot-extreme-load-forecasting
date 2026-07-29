.RECIPEPREFIX := >

.PHONY: \
	shared-verify \
	track-a-test \
	track-a-smoke \
	track-b-test \
	track-b-smoke \
	check

shared-verify:
> uv run pytest tests/shared tests/leakage -q

track-a-test:
> uv run pytest tests/track_a -q

track-a-smoke:
> uv run python -m scripts.track_a.run --stage smoke

track-b-test:
> uv run pytest tests/track_b -q

track-b-smoke:
> uv run python -m scripts.track_b.run --stage smoke

check:
> uv run ruff check .
> uv run ruff format --check .
> uv run pytest -q
