#!/usr/bin/env python3
"""Oracle-certify every exact task root in a CHARM V1 materialization receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from glm47_posttraining.aider_polyglot.dataset import _load_verified_rubric
from glm47_posttraining.aider_polyglot.harness import (
    _run_stage,
    capture_stage_receipts,
    run_shadow_weighted45_tests,
    stage_receipt_bundle,
)
from glm47_posttraining.aider_polyglot.schema import AiderChatMessage, AiderPolyglotTask
from glm47_posttraining.aider_polyglot.validator.oracle.oracle_runner import (
    OracleValidationConfig,
    certify_task_oracle,
)


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def tree_sha256(root: Path) -> str:
    files = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return hashlib.sha256(canonical_bytes(files)).hexdigest()


def validate_source_manifest(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "charm-verifier-source-manifest-v1":
        raise ValueError("unsupported verifier source manifest")
    repository = Path(__file__).resolve().parents[1]
    for row in manifest.get("files", []):
        source = repository / row["path"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"verifier source drift: {row['path']}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-receipt", required=True, type=Path)
    parser.add_argument("--task-selection", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gcc-image", required=True)
    parser.add_argument("--clang-tsan-image", required=True)
    parser.add_argument("--oracle-source-manifest", required=True, type=Path)
    args = parser.parse_args()
    if args.summary.exists():
        raise FileExistsError(f"refusing to overwrite summary: {args.summary}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    materialization = json.loads(args.materialization_receipt.read_text(encoding="utf-8"))
    records = list(materialization["tasks"])
    selection_sha256 = None
    if args.task_selection is not None:
        selection = json.loads(args.task_selection.read_text(encoding="utf-8"))
        materialization_sha256 = hashlib.sha256(
            args.materialization_receipt.read_bytes()
        ).hexdigest()
        if (
            selection.get("schema_version") != "charm-v1-proof-task-selection-v1"
            or selection.get("materialization_receipt_sha256") != materialization_sha256
        ):
            raise ValueError("task selection is not bound to the materialization receipt")
        task_ids = selection.get("task_ids")
        if not isinstance(task_ids, list) or len(task_ids) != len(set(task_ids)):
            raise ValueError("task selection IDs must be a unique list")
        by_id = {record["task_id"]: record for record in records}
        if not task_ids or any(task_id not in by_id for task_id in task_ids):
            raise ValueError("task selection contains no tasks or unknown task IDs")
        records = [by_id[task_id] for task_id in task_ids]
        selection_sha256 = hashlib.sha256(args.task_selection.read_bytes()).hexdigest()
    source_manifest = validate_source_manifest(args.oracle_source_manifest)
    source_manifest_sha256 = hashlib.sha256(args.oracle_source_manifest.read_bytes()).hexdigest()
    certifier_source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    rows = []
    for record in records:
        exercise = Path(record["path"])
        observed_tree = tree_sha256(exercise)
        if observed_tree != record["tree_sha256"]:
            raise ValueError(f"materialized tree hash drift: {record['task_id']}")
        rubric = _load_verified_rubric(exercise)
        instructions = (exercise / ".docs" / "instructions.md").read_text(encoding="utf-8")
        task = AiderPolyglotTask(
            task_id=rubric.task_id,
            exercise=rubric.task_id,
            split="train",
            harness_kind="shadow_cpp17",
            exercise_dir=exercise.name,
            editable_files=list(rubric.editable_files),
            prompt=[AiderChatMessage(role="user", content=instructions)],
            family=rubric.family,
            category=rubric.category,
            tags=list(rubric.tags),
            hidden_test_sha256=rubric.hidden_test_sha256,
            source_prompt_sha256=rubric.source_prompt_sha256,
            verification_gate=rubric.verification_gate,
        )
        image = args.clang_tsan_image if rubric.family == "Parallel Letter Frequency" else args.gcc_image

        def pinned_runner(exercise_path, files, standard, hidden_sha256):
            return run_shadow_weighted45_tests(
                exercise_path,
                files,
                image=image,
                expected_test_sha256=hidden_sha256,
                cpp_standard=standard,
                optimize=True,
                hidden_werror=True,
            )

        with capture_stage_receipts() as stage_receipts:
            compiler = _run_stage(exercise, "c++ --version", image=image, timeout_s=15)
            receipt = certify_task_oracle(
                task,
                exercise,
                rubric.hidden_test_file,
                config=OracleValidationConfig(),
                harness_runner=pinned_runner,
            )
        hidden_text = (exercise / rubric.hidden_test_file).read_text(encoding="utf-8")
        hidden_assertion_count = len(
            re.findall(r"\b(?:assert|CHECK|REQUIRE)\s*\(", hidden_text)
        )
        payload = {
            "schema_version": "charm-v1-materialized-task-proof-v1",
            "task_id": task.task_id,
            "topic": rubric.family,
            "tree_sha256": observed_tree,
            "image": image,
            "compiler_identity": (compiler.stdout or compiler.stderr or "unknown").splitlines()[0],
            "oracle_source_manifest_path": str(args.oracle_source_manifest.resolve()),
            "oracle_source_manifest_sha256": source_manifest_sha256,
            "oracle_source_file_count": source_manifest["source_file_count"],
            "certifier_source_sha256": certifier_source_sha256,
            "status": receipt.status,
            "certification_sha256": receipt.certification_sha256,
            "runs": [run.model_dump(mode="json") for run in receipt.runs],
            "rules": [rule.model_dump(mode="json") for rule in receipt.rules],
            "private_execution_receipts": stage_receipt_bundle(stage_receipts),
            "test_provenance": {
                "clean_room_new_test_files": 1,
                "inherited_test_files": 0,
                "hidden_assertion_count": hidden_assertion_count,
                "five_partition_reachability_passed": all(
                    run.tests_total == 5
                    and all(run.checks.get(f"H{index}") is True for index in range(1, 6))
                    for run in receipt.runs
                ),
            },
        }
        output = args.output_dir / f"{task.task_id}.json"
        if output.exists():
            raise FileExistsError(f"refusing to overwrite task proof: {output}")
        output.write_bytes(canonical_bytes(payload))
        rows.append(
            {
                "task_id": task.task_id,
                "topic": rubric.family,
                "status": receipt.status,
                "tree_sha256": observed_tree,
                "proof_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "proof_path": str(output.resolve()),
            }
        )
        print(json.dumps({"task_id": task.task_id, "status": receipt.status}), flush=True)

    summary = {
        "schema_version": "charm-v1-materialized-oracle-summary-v1",
        "decision": "PASS" if len(rows) == len(records) and all(row["status"] == "certified" for row in rows) else "FAIL",
        "task_count": len(rows),
        "authorized_task_count": len(materialization["tasks"]),
        "materialization_receipt_sha256": hashlib.sha256(
            args.materialization_receipt.read_bytes()
        ).hexdigest(),
        "oracle_source_manifest_sha256": source_manifest_sha256,
        "task_selection_sha256": selection_sha256,
        "selected_task_ids": [record["task_id"] for record in records],
        "certifier_source_sha256": certifier_source_sha256,
        "tasks": rows,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_bytes(canonical_bytes(summary))
    print(json.dumps({"decision": summary["decision"], "task_count": len(rows)}), flush=True)
    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
