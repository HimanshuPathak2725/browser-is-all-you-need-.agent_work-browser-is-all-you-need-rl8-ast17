# Policy G03 verifier: execute trusted API caller and link checks from the pinned manifest.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G03", Path(__file__)))
