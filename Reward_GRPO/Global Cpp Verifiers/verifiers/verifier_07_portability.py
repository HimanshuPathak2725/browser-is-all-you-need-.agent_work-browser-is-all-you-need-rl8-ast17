# Policy G07 verifier: execute applicable alternate-toolchain checks from the pinned manifest.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G07", Path(__file__)))
