"""Track A — standard CNP versus AdaCNP.

Contains both the synthetic scaffold (freeze stages 1–2) and the real-data
pipeline (stages 3–4). Modules that read real artifacts do so only through the
paths adopted by decision, and only for artifacts hash-verified and recorded in
`docs/audit/TRACK_A_IMPORT_MANIFEST_001.csv`:

* `load_data` — the harmonized load artifact (D-009)
* `event_inventory`, `event_eligibility` — the controlling event inventory (D-006)
* `censoring` — the V7 censoring artifacts (D-010)
* `weather` — the regional temperature index (D-012)

This docstring previously said "synthetic scaffold only … must not load any real
artifact", which stopped being true at commit `d9fb1ac`.
"""
