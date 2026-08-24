# Policy G01 verifier: authenticate the generic candidate and protected-asset boundary.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_integrity


raise SystemExit(execute_integrity("G01", Path(__file__)))
