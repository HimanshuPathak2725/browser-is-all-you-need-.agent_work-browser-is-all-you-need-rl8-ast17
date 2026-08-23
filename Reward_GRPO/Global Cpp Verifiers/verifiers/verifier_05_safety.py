# Policy G05 verifier: execute applicable sanitizer or safety stress checks from the manifest.
from __future__ import annotations

from pathlib import Path

from _global_common import execute_commands


raise SystemExit(execute_commands("G05", Path(__file__)))
