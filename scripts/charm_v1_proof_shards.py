#!/usr/bin/env python3
"""Partition immutable V1 task proofs and combine their digest-bound summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical(value))


def partition(materialization_path: Path, output_dir: Path, shard_count: int) -> None:
    if shard_count < 2:
        raise ValueError("shard count must be at least two")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite shard directory: {output_dir}")
    materialization = load(materialization_path)
    tasks = materialization.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 51:
        raise RuntimeError("materialization receipt must contain exact-51 tasks")
    task_ids = [row["task_id"] for row in tasks]
    if len(set(task_ids)) != 51:
        raise RuntimeError("materialization task IDs are not unique")
    materialization_sha256 = sha256(materialization_path)
    output_dir.mkdir(parents=True)
    bindings = []
    for index in range(shard_count):
        selected = task_ids[index::shard_count]
        payload = {
            "schema_version": "charm-v1-proof-task-selection-v1",
            "materialization_receipt_sha256": materialization_sha256,
            "shard_count": shard_count,
            "shard_index": index,
            "task_ids": selected,
        }
        path = output_dir / f"shard-{index:02d}.json"
        write_new(path, payload)
        bindings.append({"path": str(path.resolve()), "sha256": sha256(path), "task_count": len(selected)})
    manifest = {
        "schema_version": "charm-v1-proof-shard-manifest-v1",
        "materialization_receipt_sha256": materialization_sha256,
        "shard_count": shard_count,
        "task_count": len(task_ids),
        "selections": bindings,
    }
    write_new(output_dir / "manifest.json", manifest)
    print(json.dumps({"decision": "PASS", "shard_count": shard_count, "task_count": len(task_ids)}))


def combine(kind: str, materialization_path: Path, summaries: list[Path], output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite combined summary: {output}")
    materialization = load(materialization_path)
    tasks = materialization.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 51:
        raise RuntimeError("materialization receipt must contain exact-51 tasks")
    materialized = {row["task_id"]: row for row in tasks}
    if len(materialized) != 51:
        raise RuntimeError("materialization task IDs are not unique")
    if kind == "oracle":
        schema = "charm-v1-materialized-oracle-summary-v1"
        common_fields = ("oracle_source_manifest_sha256", "certifier_source_sha256")
        proof_field = "status"
        proof_pass = "certified"
    else:
        schema = "charm-v1-negative-control-summary-v1"
        common_fields = (
            "generation_plan_sha256",
            "oracle_source_manifest_sha256",
            "negative_control_source_sha256",
        )
        proof_field = "decision"
        proof_pass = "PASS"
    common: dict[str, Any] | None = None
    combined: dict[str, dict[str, Any]] = {}
    source_summaries = []
    materialization_sha256 = sha256(materialization_path)
    for path in summaries:
        summary = load(path)
        if (
            summary.get("schema_version") != schema
            or summary.get("decision") != "PASS"
            or summary.get("authorized_task_count") != 51
            or summary.get("materialization_receipt_sha256") != materialization_sha256
        ):
            raise RuntimeError(f"invalid {kind} shard summary: {path}")
        observed_common = {field: summary.get(field) for field in common_fields}
        if common is None:
            common = observed_common
        elif observed_common != common:
            raise RuntimeError(f"{kind} shard source binding mismatch: {path}")
        rows = summary.get("tasks")
        selected_ids = summary.get("selected_task_ids")
        if (
            not isinstance(rows, list)
            or not isinstance(selected_ids, list)
            or [row.get("task_id") for row in rows] != selected_ids
            or summary.get("task_count") != len(rows)
        ):
            raise RuntimeError(f"malformed {kind} shard coverage: {path}")
        for row in rows:
            task_id = row.get("task_id")
            if task_id not in materialized or task_id in combined:
                raise RuntimeError(f"unknown or duplicate {kind} proof task: {task_id}")
            proof_path = Path(row["proof_path"])
            if sha256(proof_path) != row.get("proof_sha256"):
                raise RuntimeError(f"{kind} proof hash mismatch: {task_id}")
            proof = load(proof_path)
            if proof.get("task_id") != task_id or proof.get(proof_field) != proof_pass:
                raise RuntimeError(f"{kind} proof did not pass: {task_id}")
            if row.get(proof_field) != proof_pass:
                raise RuntimeError(f"{kind} summary row did not pass: {task_id}")
            if proof.get("tree_sha256") != materialized[task_id].get("tree_sha256"):
                raise RuntimeError(f"{kind} task tree binding mismatch: {task_id}")
            combined[task_id] = row
        source_summaries.append({"path": str(path.resolve()), "sha256": sha256(path)})
    if set(combined) != set(materialized):
        missing = sorted(set(materialized) - set(combined))
        raise RuntimeError(f"{kind} shards do not cover exact-51 tasks: {missing}")
    ordered_rows = [combined[row["task_id"]] for row in tasks]
    result = {
        "schema_version": schema,
        "decision": "PASS",
        "task_count": 51,
        "authorized_task_count": 51,
        "materialization_receipt_sha256": materialization_sha256,
        "task_selection_sha256": None,
        "selected_task_ids": [row["task_id"] for row in tasks],
        **(common or {}),
        "source_shard_summaries": source_summaries,
        "tasks": ordered_rows,
    }
    write_new(output, result)
    print(json.dumps({"decision": "PASS", "kind": kind, "task_count": 51, "sha256": sha256(output)}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("partition")
    create.add_argument("--materialization-receipt", required=True, type=Path)
    create.add_argument("--output-dir", required=True, type=Path)
    create.add_argument("--shard-count", required=True, type=int)
    merge = subparsers.add_parser("combine")
    merge.add_argument("--kind", choices=("oracle", "negative"), required=True)
    merge.add_argument("--materialization-receipt", required=True, type=Path)
    merge.add_argument("--summary", action="append", required=True, type=Path)
    merge.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "partition":
        partition(args.materialization_receipt, args.output_dir, args.shard_count)
    else:
        combine(args.kind, args.materialization_receipt, args.summary, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
