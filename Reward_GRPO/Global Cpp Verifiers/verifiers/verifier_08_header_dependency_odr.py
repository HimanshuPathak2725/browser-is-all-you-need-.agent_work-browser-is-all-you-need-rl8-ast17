# Policy G08 verifier: execute trusted header, dependency, and ODR integration probes.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G08", Path(__file__)))
