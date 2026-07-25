#!/usr/bin/env python3
"""Audit that every Aider shadow grader supports five isolated hidden suites."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from glm47_posttraining.aider_polyglot.harness import _instrument_weighted45_grader
from glm47_posttraining.aider_polyglot.schema import AiderShadowRubric


STRICT_FLAGS = (
    "-std=c++17",
    "-Wall",
    "-Wextra",
    "-pedantic",
    "-pthread",
)


def _practice_root(root: Path) -> Path:
    candidates = (
        root / "cpp" / "exercises" / "practice",
        root / "exercises" / "practice",
        root,
    )
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*/.rubric.json")):
            return candidate
    raise ValueError(f"cannot locate shadow exercises beneath {root}")


def _audit_one(exercise: Path, *, compile_check: bool) -> dict[str, object]:
    rubric = AiderShadowRubric.read_json(exercise / ".rubric.json")
    grader = exercise / rubric.hidden_test_file
    grader_bytes = grader.read_bytes()
    observed_sha256 = hashlib.sha256(grader_bytes).hexdigest()
    if observed_sha256 != rubric.hidden_test_sha256:
        raise ValueError(f"hidden grader hash mismatch: {exercise.name}")
    instrumented, check_count = _instrument_weighted45_grader(
        grader_bytes.decode("utf-8", errors="strict")
    )
    compile_returncode: int | None = None
    compile_log = ""
    if compile_check:
        with TemporaryDirectory(prefix=f"weighted45_audit_{exercise.name}_") as value:
            scratch = Path(value)
            for item in exercise.iterdir():
                if item.is_file() and item.name != rubric.hidden_test_file:
                    shutil.copy2(item, scratch / item.name)
            transformed = scratch / rubric.hidden_test_file
            transformed.write_text(instrumented, encoding="utf-8")
            completed = subprocess.run(
                [
                    "c++",
                    *STRICT_FLAGS,
                    "-I.",
                    "-Dmain=glm47_hidden_main",
                    "-c",
                    transformed.name,
                    "-o",
                    "test.o",
                ],
                cwd=scratch,
                check=False,
                capture_output=True,
                text=True,
            )
            compile_returncode = completed.returncode
            compile_log = (completed.stdout or "") + (completed.stderr or "")
            if completed.returncode != 0:
                raise ValueError(
                    f"instrumented grader does not compile: {exercise.name}: {compile_log}"
                )
    return {
        "task_id": rubric.task_id,
        "hidden_test_sha256": observed_sha256,
        "grader_checks": check_count,
        "suite_partitions": 5,
        "compile_returncode": compile_returncode,
        "compile_log": compile_log,
    }


def audit(root: Path, *, compile_check: bool) -> dict[str, object]:
    practice = _practice_root(root.resolve())
    exercises = sorted(path for path in practice.iterdir() if path.is_dir())
    records = [_audit_one(exercise, compile_check=compile_check) for exercise in exercises]
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "kind": "glm47-aider-weighted45-grader-audit",
        "status": "passed",
        "task_count": len(records),
        "minimum_grader_checks": min(int(record["grader_checks"]) for record in records),
        "maximum_grader_checks": max(int(record["grader_checks"]) for record in records),
        "compile_checked": compile_check,
        "records_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-dir", required=True, type=Path)
    parser.add_argument("--compile", action="store_true", dest="compile_check")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = audit(args.tasks_dir, compile_check=args.compile_check)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        summary = {key: value for key, value in receipt.items() if key != "records"}
        summary["output"] = str(args.output)
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
