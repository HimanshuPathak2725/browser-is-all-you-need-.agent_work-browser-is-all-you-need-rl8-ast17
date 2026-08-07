#!/usr/bin/env python3
"""V1 CLI owner for the core CHARM repository uniqueness scanner.

The current frozen proposal is represented by three co-produced documents
(proposal, curriculum, and dependency plans).  This wrapper records and omits
only those exact query artifacts, while the core scanner still inventories the
entire accessible repository and linked-worktree corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/charm-skill/scripts/scan_repository_uniqueness.py"


def load_core() -> ModuleType:
    spec = importlib.util.spec_from_file_location("charm_uniqueness_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load uniqueness core: {CORE_PATH}")
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
        print(f"refusing to overwrite uniqueness receipt: {args.output}", file=sys.stderr)
        return 2

    core = load_core()
    excluded = {
        args.proposal_plan.resolve(),
        args.output.resolve(),
        *(path.resolve() for path in args.proposal_artifact),
    }
    original_iter_files = core.iter_files

    def filtered_iter_files(root: Path, exclusions: list[dict[str, str]]) -> Iterator[Path]:
        for path in original_iter_files(root, exclusions):
            if path.resolve() in excluded:
                exclusions.append({
                    "path": str(path.resolve()),
                    "reason": "exact current frozen proposal-suite query artifact",
                })
                continue
            yield path

    core.iter_files = filtered_iter_files
    try:
        receipt = core.scan(args.proposal_plan, args.output, args.root, args.additional_root)
    except core.ScanError as exc:
        receipt = {
            "schema_version": core.SCHEMA_VERSION,
            "decision": "FAIL",
            "repository_scope_complete": False,
            "parse_failures": 1,
            "task_id_matches": 0,
            "exact_matches": 0,
            "near_matches": 0,
            "structural_matches": 0,
            "semantic_matches": 0,
            "ambiguous_matches": 0,
            "errors": [str(exc)],
        }
    receipt["v1_scanner_wrapper_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt["core_scanner_sha256"] = hashlib.sha256(CORE_PATH.read_bytes()).hexdigest()
    receipt["proposal_suite_exclusions"] = sorted(str(path) for path in excluded)
    core.atomic_write(args.output, core.canonical_bytes(receipt))
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("decision") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
