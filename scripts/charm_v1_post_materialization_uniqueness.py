#!/usr/bin/env python3
"""Recheck CHARM V1 uniqueness after immutable task materialization.

The repository scanner treats the exact bytes created by this generation
lineage as the query, not as an external collision.  This wrapper separately
proves that those 51 canonical roots are internally distinct and then scans
every other task-bearing artifact in all linked worktrees.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts/charm_v1_repository_uniqueness_v5.py"
CORE = ROOT / "scripts/charm_v1_repository_uniqueness_v2.py"
NEAR_THRESHOLD = 0.92


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tree_sha256(root: Path) -> str:
    files = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return hashlib.sha256(canonical(files)).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--materialization-receipt", required=True, type=Path)
    parser.add_argument("--lineage-root", required=True, type=Path)
    parser.add_argument(
        "--lineage-file",
        action="append",
        default=[],
        type=Path,
        help="Exact current-lineage artifact to exclude as query provenance; repeatable.",
    )
    parser.add_argument(
        "--lineage-task-root",
        action="append",
        default=[],
        type=Path,
        help=(
            "Preserved failed/remediated task root from this exact batch and "
            "session; provenance is verified before its files are excluded."
        ),
    )
    parser.add_argument("--reservation-registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite receipt: {args.output}")

    plan = json.loads(args.proposal_plan.read_text(encoding="utf-8"))
    materialization = json.loads(args.materialization_receipt.read_text(encoding="utf-8"))
    proposals = {item["task_id"]: item for item in plan["proposals"]}
    rows = materialization["tasks"]
    if len(rows) != 51 or set(proposals) != {item["task_id"] for item in rows}:
        raise RuntimeError("materialized IDs do not equal the frozen 51-task plan")

    current_files: set[Path] = {
        args.proposal_plan.resolve(),
        args.materialization_receipt.resolve(),
        args.reservation_registry.resolve(),
    }
    if args.lineage_root.is_dir():
        current_files.update(path.resolve() for path in args.lineage_root.rglob("*") if path.is_file())
    for path in args.lineage_file:
        if not path.is_file():
            raise RuntimeError(f"current-lineage artifact is missing: {path}")
        current_files.add(path.resolve())

    generation_batch_id = materialization.get("generation_batch_id")
    generation_session_id = materialization.get("generation_session_id")
    lineage_task_roots: list[dict[str, str]] = []
    canonical_paths = {Path(row["path"]).resolve() for row in rows}
    for task_root_value in args.lineage_task_root:
        task_root = task_root_value.resolve()
        if not task_root.is_dir() or task_root.is_symlink():
            raise RuntimeError(f"lineage task root is not a real directory: {task_root}")
        if task_root in canonical_paths:
            raise RuntimeError(
                f"canonical task root must not be repeated as lineage history: {task_root}"
            )
        provenance_path = task_root / ".provenance.json"
        if not provenance_path.is_file():
            raise RuntimeError(f"lineage task provenance is missing: {task_root}")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        task_id = provenance.get("task_id")
        if (
            provenance.get("generation_batch_id") != generation_batch_id
            or provenance.get("generation_session_id") != generation_session_id
            or task_id not in proposals
            or task_root.name != task_id
        ):
            raise RuntimeError(f"foreign or inconsistent lineage task root: {task_root}")
        lineage_task_roots.append({
            "path": str(task_root),
            "task_id": str(task_id),
            "tree_sha256": tree_sha256(task_root),
        })
        current_files.update(
            path.resolve() for path in task_root.rglob("*") if path.is_file()
        )

    internal: list[dict[str, Any]] = []
    task_texts: dict[str, str] = {}
    tree_hashes: dict[str, str] = {}
    prompt_hashes: dict[str, str] = {}
    hidden_hashes: dict[str, str] = {}
    generated_queries: list[dict[str, Any]] = []
    for row in rows:
        task_id = row["task_id"]
        task_root = Path(row["path"]).resolve()
        observed_tree = tree_sha256(task_root)
        if observed_tree != row["tree_sha256"]:
            raise RuntimeError(f"canonical task tree drift: {task_id}")
        rubric = json.loads((task_root / ".rubric.json").read_text(encoding="utf-8"))
        prompt = (task_root / ".docs/instructions.md").read_text(encoding="utf-8")
        reference = "\n".join(
            (task_root / ".reference" / name).read_text(encoding="utf-8")
            for name in rubric["editable_files"]
        )
        task_texts[task_id] = prompt + "\n" + reference
        tree_hashes[task_id] = observed_tree
        prompt_hashes[task_id] = rubric["source_prompt_sha256"]
        hidden_hashes[task_id] = rubric["hidden_test_sha256"]
        components = [
            {"kind": "prompt", "text": prompt},
            {
                "kind": "hidden_test",
                "text": (task_root / rubric["hidden_test_file"]).read_text(encoding="utf-8"),
            },
            {"kind": "public_api", "text": "\n".join(proposals[task_id]["public_api"])},
            {"kind": "target_combined", "text": reference},
        ]
        components.extend(
            {
                "kind": "target_source",
                "text": (task_root / ".reference" / name).read_text(encoding="utf-8"),
            }
            for name in rubric["editable_files"]
        )
        generated_queries.append({"task_id": task_id, "components": components})
        current_files.update(path.resolve() for path in task_root.rglob("*") if path.is_file())

    core = load_module("charm_v1_uniqueness_core_post", CORE)
    task_ids = sorted(task_texts)
    for index, left in enumerate(task_ids):
        for right in task_ids[index + 1 :]:
            score = core.similarity(task_texts[left], task_texts[right])
            if (
                tree_hashes[left] == tree_hashes[right]
                or prompt_hashes[left] == prompt_hashes[right]
                or hidden_hashes[left] == hidden_hashes[right]
                or score >= NEAR_THRESHOLD
            ):
                internal.append({
                    "task_ids": [left, right],
                    "same_tree": tree_hashes[left] == tree_hashes[right],
                    "same_prompt": prompt_hashes[left] == prompt_hashes[right],
                    "same_hidden_test": hidden_hashes[left] == hidden_hashes[right],
                    "similarity": score,
                })

    scanner = load_module("charm_v1_uniqueness_post", SCANNER)
    core_v4 = scanner.load_core()

    def exact_near(left: str, right: str) -> float:
        a, b = core_v4.token_set(left), core_v4.token_set(right)
        if len(a) < 12 or len(b) < 12:
            return 0.0
        if min(len(a), len(b)) / max(len(a), len(b)) < core_v4.NEAR_THRESHOLD:
            return 0.0
        return len(a & b) / len(a | b)

    core_v4.similarity = exact_near
    receipt = core_v4.scan(
        args.proposal_plan,
        args.output,
        args.root,
        [],
        sorted(current_files),
        generated_queries,
    )
    receipt.update({
        "schema_version": "charm-post-materialization-uniqueness-v1",
        "scanner_entrypoint": str(Path(__file__).resolve()),
        "scanner_entrypoint_sha256": sha256(Path(__file__)),
        "materialization_receipt_sha256": sha256(args.materialization_receipt),
        "canonical_task_count": len(rows),
        "canonical_internal_collision_count": len(internal),
        "canonical_internal_collision_details": internal,
        "canonical_roots_excluded_only_as_current_query_lineage": True,
        "preserved_lineage_task_roots": sorted(
            lineage_task_roots, key=lambda item: (item["task_id"], item["path"])
        ),
        "preserved_lineage_task_root_count": len(lineage_task_roots),
        "preserved_lineage_provenance_verified": True,
        "exact_generated_prompts_targets_tests_apis_and_sources_queried": True,
    })
    if internal:
        receipt["semantic_matches"] = int(receipt.get("semantic_matches", 0)) + len(internal)
        receipt["semantic_match_details"] = [
            *receipt.get("semantic_match_details", []), *internal
        ]
    zero_fields = (
        "task_id_matches", "exact_matches", "near_matches", "structural_matches",
        "semantic_matches", "ambiguous_matches", "parse_failures",
    )
    receipt["decision"] = "PASS" if (
        receipt.get("repository_scope_complete") is True
        and all(int(receipt.get(field, -1)) == 0 for field in zero_fields)
    ) else "FAIL"
    receipt.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(receipt))
    print(json.dumps({field: receipt.get(field) for field in (
        "decision", "files_visited", "task_records_parsed", "parse_failures",
        "task_id_matches", "exact_matches", "near_matches", "structural_matches",
        "semantic_matches", "ambiguous_matches", "canonical_internal_collision_count",
    )}, sort_keys=True))
    return 0 if receipt["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
