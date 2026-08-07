#!/usr/bin/env python3
"""Stage one CHARM V1 topic and certify it in a required pinned image."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from glm47_posttraining.aider_polyglot.dataset import _load_verified_rubric
from glm47_posttraining.aider_polyglot.harness import run_shadow_weighted45_tests
from glm47_posttraining.aider_polyglot.schema import AiderChatMessage, AiderPolyglotTask
from glm47_posttraining.aider_polyglot.validator.oracle.oracle_runner import (
    OracleValidationConfig,
    certify_task_oracle,
)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"charm_v1_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import owner module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_exclusive(root: Path, package: dict) -> Path:
    target = root / package["task_id"]
    target.mkdir(parents=True, exist_ok=False)
    for name, contents in package["files"].items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, type=Path)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    if "@sha256:" not in args.image:
        raise ValueError("oracle image must be digest-pinned")
    if args.staging_root.exists():
        raise FileExistsError(f"staging root must not already exist: {args.staging_root}")
    args.staging_root.mkdir(parents=True, exist_ok=False)

    packages = _load(args.module).tasks()
    if len(packages) != 3 or len({package["task_id"] for package in packages}) != 3:
        raise ValueError("one V1 topic module must define exactly three unique tasks")

    rows = []
    for package in packages:
        exercise = _write_exclusive(args.staging_root, package)
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

        def pinned_runner(exercise_path, files, standard, hidden_sha256):
            return run_shadow_weighted45_tests(
                exercise_path,
                files,
                image=args.image,
                expected_test_sha256=hidden_sha256,
                cpp_standard=standard,
                optimize=True,
                hidden_werror=True,
            )

        receipt = certify_task_oracle(
            task,
            exercise,
            rubric.hidden_test_file,
            config=OracleValidationConfig(),
            harness_runner=pinned_runner,
        )
        rows.append({
            "task_id": task.task_id,
            "status": receipt.status,
            "certification_sha256": receipt.certification_sha256,
            "runs": [run.model_dump(mode="json") for run in receipt.runs],
            "rules": [rule.model_dump(mode="json") for rule in receipt.rules],
        })

    result = {
        "schema_version": "charm-v1-topic-stage-receipt-v1",
        "owner_module": str(args.module),
        "pinned_image": args.image,
        "task_count": len(rows),
        "decision": "PASS" if all(row["status"] == "certified" for row in rows) else "FAIL",
        "tasks": rows,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "tasks": [(r["task_id"], r["status"]) for r in rows]}))
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
