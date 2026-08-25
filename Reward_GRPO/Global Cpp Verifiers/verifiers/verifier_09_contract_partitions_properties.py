# Policy G09 verifier: execute task-owned contract-partition and property probes.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G09", Path(__file__)))
