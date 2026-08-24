# Policy G02 verifier: execute trusted strict-build checks without task semantic assumptions.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G02", Path(__file__)))
