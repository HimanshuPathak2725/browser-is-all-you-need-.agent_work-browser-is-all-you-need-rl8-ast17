# Policy G10 verifier: execute task-owned lifecycle, isolation, and repeatability probes.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G10", Path(__file__)))
