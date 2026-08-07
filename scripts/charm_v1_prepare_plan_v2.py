#!/usr/bin/env python3
"""Correct and freeze the content-derived CHARM V1 curriculum plan."""

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
CORE = ROOT / ".agents/skills/charm-skill/scripts/prepare_v1_plan.py"


def load_core():
    spec = importlib.util.spec_from_file_location("charm_v1_plan_core", CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load V1 plan core: {CORE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def atomic_write(path: Path, value: object) -> None:
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


def build():
    core = load_core()
    plan, curriculum, dependencies = core.build()
    proposals = plan["proposals"]
    by_id = {item["task_id"]: item for item in proposals}

    # Calibration must be an oracle-backed no-change target, never a compile,
    # semantic, reconstruction, or repair target. Reassign roles without
    # changing the frozen 27/10/11/3 counts.
    old_calibration = [
        "charm-v1-duplicate-side-traversal",
        "charm-v1-complex-polynomial",
        "charm-v1-moving-roster",
    ]
    calibration = [
        "charm-v1-keyed-square-transposition",
        "charm-v1-layer-view-repair",
        "charm-v1-scorecard-assignment",
    ]
    inherited_roles = [by_id[task_id]["role"] for task_id in calibration]
    for task_id, role in zip(old_calibration, inherited_roles, strict=True):
        by_id[task_id]["role"] = role
    for task_id in calibration:
        item = by_id[task_id]
        item["role"] = "calibration"
        item["starter_type"] = "near_correct"
        item["target_design"] = (
            "The supplied implementation is already correct. Return no file listings and preserve "
            "all bytes; the oracle proves that an edit is unnecessary."
        )
        item["starter_design"] = "near_correct oracle-backed no-change calibration starter"

    # Every calibration header is frozen. Transfer the two displaced header
    # modes to non-calibration tasks so the exact 11/10/10/10/10 totals remain.
    by_id["charm-v1-exposure-window-ledger"]["header_mode"] = "repaired"
    by_id["charm-v1-dose-policy-table"]["header_mode"] = "repaired"
    by_id["charm-v1-idempotent-cent-ledger"]["header_mode"] = "editable"
    for task_id in ("charm-v1-layer-view-repair", "charm-v1-scorecard-assignment"):
        by_id[task_id]["header_mode"] = "frozen"

    # The Clock family is explicitly conditioned on the observed organic Luna
    # wrong-historical-API failure, while its new contract/API remain novel.
    for item in proposals:
        item["source_kind"] = "synthetic"
    by_id["charm-v1-offset-civil-clock"]["source_kind"] = "organic_failure_derived"
    by_id["charm-v1-offset-civil-clock"]["source_evidence"] = {
        "failure_family": "clock-wrong-historical-public-api",
        "artifact": "artifacts/luna-cleanroom-evals/campaign-pass2-8x-20260801T100237Z/task-frequency.json",
        "artifact_sha256": "8d5d1a9c867e3da7ae31ae4cb359b668437d4830c4fb809de5fc7f8fac297243",
        "copying_forbidden": True,
    }

    for item in proposals:
        unsigned = {key: value for key, value in item.items() if key != "proposal_sha256"}
        item["proposal_sha256"] = hashlib.sha256(core.canonical_bytes(unsigned)).hexdigest()

    def counts(field: str):
        result = {}
        for item in proposals:
            value = item[field]
            result[value] = result.get(value, 0) + 1
        return result

    curriculum["role_counts"] = counts("role")
    curriculum["starter_type_counts"] = counts("starter_type")
    curriculum["header_mode_counts"] = counts("header_mode")
    curriculum["non_synthetic_direct_success_count"] = sum(
        item["source_kind"] != "synthetic" and item["role"] == "direct_verified_success"
        for item in proposals
    )
    curriculum["calibration_task_ids"] = calibration
    curriculum["calibration_content_proof"] = {
        task_id: {"starter_type": by_id[task_id]["starter_type"],
                  "header_mode": by_id[task_id]["header_mode"],
                  "required_action": "no_change"}
        for task_id in calibration
    }
    curriculum["organic_failure_anchor_task_ids"] = ["charm-v1-offset-civil-clock"]
    return plan, curriculum, dependencies


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    plan, curriculum, dependencies = build()
    outputs = {
        "v1-proposal-plan.json": plan,
        "v1-curriculum-plan.json": curriculum,
        "v1-dependency-manifest.json": dependencies,
    }
    for name, value in outputs.items():
        path = args.output_dir / name
        if path.exists():
            raise SystemExit(f"refusing to overwrite corrected V1 plan: {path}")
        atomic_write(path, value)
    print(json.dumps({name: hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest()
                      for name in outputs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
