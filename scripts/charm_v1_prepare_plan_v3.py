#!/usr/bin/env python3
"""Final V1 plan owner: preserve exact header-mode counts after calibration."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "scripts/charm_v1_prepare_plan_v2.py"


def load_v2():
    spec = importlib.util.spec_from_file_location("charm_v1_plan_v2_core", V2)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load V1 plan V2: {V2}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build():
    v2 = load_v2()
    plan, curriculum, dependencies = v2.build()
    by_id = {item["task_id"]: item for item in plan["proposals"]}
    by_id["charm-v1-dose-policy-table"]["header_mode"] = "repaired"
    by_id["charm-v1-idempotent-cent-ledger"]["header_mode"] = "editable"
    for item in plan["proposals"]:
        unsigned = {key: value for key, value in item.items() if key != "proposal_sha256"}
        item["proposal_sha256"] = hashlib.sha256(
            (json.dumps(unsigned, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ).hexdigest()
    counts = {}
    for item in plan["proposals"]:
        mode = item["header_mode"]
        counts[mode] = counts.get(mode, 0) + 1
    curriculum["header_mode_counts"] = counts
    return plan, curriculum, dependencies


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    values = build()
    names = ("v1-proposal-plan.json", "v1-curriculum-plan.json", "v1-dependency-manifest.json")
    for name, value in zip(names, values, strict=True):
        path = args.output_dir / name
        if path.exists():
            raise SystemExit(f"refusing to overwrite final V1 plan: {path}")
        write(path, value)
    print(json.dumps({name: hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest()
                      for name in names}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
