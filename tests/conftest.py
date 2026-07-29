"""Shared pytest configuration.

TEMPORARY TEST-ONLY SOURCE-PATH BOOTSTRAP.

The repository package is not installed into the environment, so ``src`` is
placed on ``sys.path`` here. This is a deliberate stopgap for the synthetic
scaffold (TRACK-A-SCAFFOLD-001), retained by PI determination of 2026-07-29:

- it affects test collection only, and no runtime or packaging behaviour;
- ``pyproject.toml`` is not modified, no package is installed, and no
  dependency is added by that task;
- proper editable installation, and removal of this bootstrap, are deferred to
  a separate packaging task **before real-data execution**.

Do not build on this mechanism or extend it to non-test code.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
