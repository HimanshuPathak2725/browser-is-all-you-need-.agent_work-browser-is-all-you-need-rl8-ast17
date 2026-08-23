# Policy G04 verifier: execute the task's authenticated official functional suite.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G04", Path(__file__)))
