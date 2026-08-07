#!/usr/bin/env python3
"""Length-bounded exact-Jaccard entrypoint for task-aware CHARM scanning."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts/charm_v1_repository_uniqueness_v2.py"


def load_core():
    spec = importlib.util.spec_from_file_location("charm_task_aware_core_v3", CORE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task-aware scanner core: {CORE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--proposal-artifact", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--additional-root", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite receipt: {args.output}", file=sys.stderr)
        return 2
    core = load_core()

    def exact_near(left: str, right: str) -> float:
        a, b = core.token_set(left), core.token_set(right)
        if len(a) < 12 or len(b) < 12:
            return 0.0
        # Jaccard can never reach threshold if set sizes differ by more than
        # the threshold ratio. This exact bound avoids intersections against
        # multi-megabyte logs without changing one comparison outcome.
        if min(len(a), len(b)) / max(len(a), len(b)) < core.NEAR_THRESHOLD:
            return 0.0
        return len(a & b) / len(a | b)

    core.similarity = exact_near
    try:
        receipt = core.scan(
            args.proposal_plan, args.output, args.root, args.additional_root,
            args.proposal_artifact,
        )
    except core.ScanError as exc:
        receipt = {
            "schema_version": core.SCHEMA, "decision": "FAIL",
            "repository_scope_complete": False, "parse_failures": 1,
            "task_id_matches": 0, "exact_matches": 0, "near_matches": 0,
            "structural_matches": 0, "semantic_matches": 0,
            "ambiguous_matches": 0, "errors": [str(exc)],
        }
    receipt["near_match_acceleration"] = "exact_jaccard_cardinality_bound"
    receipt["scanner_entrypoint"] = str(Path(__file__).resolve())
    receipt["scanner_entrypoint_sha256"] = core.digest(Path(__file__).read_bytes())
    core.write(args.output, receipt)
    print(json.dumps({key: receipt.get(key) for key in (
        "decision", "files_visited", "task_records_parsed", "parse_failures",
        "task_id_matches", "exact_matches", "near_matches", "structural_matches",
        "semantic_matches", "ambiguous_matches",
    )}, sort_keys=True))
    return 0 if receipt.get("decision") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
