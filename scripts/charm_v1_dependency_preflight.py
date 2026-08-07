#!/usr/bin/env python3
"""Compile and execute every exact frozen CHARM V1 task package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "charm-v1-dependency-preflight-receipt-v1"


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-manifest", required=True, type=Path)
    parser.add_argument("--materialization-manifest", required=True, type=Path)
    parser.add_argument("--environment-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite preflight receipt: {args.output}")
    dependencies = load(args.dependency_manifest)
    materialization = load(args.materialization_manifest)
    environment = load(args.environment_manifest)
    tasks = dependencies.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 51:
        raise SystemExit("dependency manifest must contain exactly 51 tasks")
    task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    if len(task_ids) != 51 or len(set(task_ids)) != 51 or not all(isinstance(value, str) for value in task_ids):
        raise SystemExit("dependency manifest task IDs must be 51 unique strings")
    packages = materialization.get("tasks")
    if not isinstance(packages, list) or len(packages) != 51:
        raise SystemExit("materialization manifest must contain exactly 51 task packages")
    package_by_id = {row.get("task_id"): row for row in packages if isinstance(row, dict)}
    if len(package_by_id) != 51 or set(package_by_id) != set(task_ids):
        raise SystemExit("dependency and materialization task identities disagree")
    if materialization.get("generation_batch_id") != dependencies.get("generation_batch_id"):
        raise SystemExit("dependency and materialization batch identities disagree")
    if dependencies.get("external_packages") != []:
        raise SystemExit("this V1 preflight permits only the declared C++17 standard library")
    image = environment.get("image_reference")
    if not isinstance(image, str) or "@sha256:" not in image:
        raise SystemExit("environment image must be digest-pinned")
    flags = environment.get("candidate_flags")
    if not isinstance(flags, list) or "-std=c++17" not in flags or "-Werror" not in flags:
        raise SystemExit("locked strict C++17 flags are incomplete")
    sanitizer_flags = environment.get("sanitizer_flags")
    if sanitizer_flags != ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]:
        raise SystemExit("locked ASan/UBSan flags are incomplete")

    with tempfile.TemporaryDirectory(prefix="charm_v1_dependency_") as temporary_value:
        temporary = Path(temporary_value)
        names: dict[str, str] = {}
        package_hashes: dict[str, str] = {}
        for index, task_id in enumerate(task_ids):
            name = f"task_{index:02d}"
            task_root = temporary / name
            task_root.mkdir()
            package = package_by_id[task_id]
            files = package.get("files")
            declared_hashes = package.get("file_sha256s")
            if not isinstance(files, dict) or not isinstance(declared_hashes, dict):
                raise SystemExit(f"task package files missing: {task_id}")
            if set(files) != set(declared_hashes) or not all(isinstance(path, str) and isinstance(data, str) for path, data in files.items()):
                raise SystemExit(f"task package file inventory invalid: {task_id}")
            for relative, data in files.items():
                if Path(relative).is_absolute() or ".." in Path(relative).parts:
                    raise SystemExit(f"unsafe task package path: {task_id}: {relative}")
                actual = hashlib.sha256(data.encode()).hexdigest()
                if actual != declared_hashes[relative]:
                    raise SystemExit(f"task package file digest mismatch: {task_id}: {relative}")
                if not relative.startswith(".reference/"):
                    destination = task_root / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(data, encoding="utf-8")
            rubric = json.loads(files[".rubric.json"])
            editable = rubric.get("editable_files")
            if not isinstance(editable, list) or not editable:
                raise SystemExit(f"editable file inventory invalid: {task_id}")
            for relative in editable:
                reference = f".reference/{relative}"
                if reference not in files:
                    raise SystemExit(f"reference file missing: {task_id}: {relative}")
                destination = task_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(files[reference], encoding="utf-8")
            names[name] = task_id
            package_hashes[task_id] = hashlib.sha256(
                json.dumps(package, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        shell = """set -eu
for task in /work/task_*; do
  name=${task##*/}
  build=/tmp/charm-v1-build
  cmake -S "$task" -B "$build" -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" >/tmp/cmake-configure.log
  cmake --build "$build" --parallel 1 >/tmp/cmake-build.log
  "$build/task_test"
  printf 'PASS %s\\n' "$name"
  rm -rf "$build"
done
"""
        completed = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "-v", f"{temporary}:/work:ro",
             "--entrypoint", "/bin/sh", image, "-c", shell],
            check=False, capture_output=True, text=True, timeout=300,
        )
    passed_files = {
        line.removeprefix("PASS ").strip()
        for line in completed.stdout.splitlines()
        if line.startswith("PASS ")
    }
    task_receipts = [{
        "task_id": names[name], "package_directory": name,
        "package_sha256": package_hashes[names[name]],
        "compile_and_run_passed": name in passed_files,
        "exact_task_package_probed": True,
        "dependencies": ["c++17-standard-library"],
    } for name in sorted(names)]
    decision = "PASS" if completed.returncode == 0 and len(passed_files) == 51 else "FAIL"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "dependency_manifest_sha256": sha256_path(args.dependency_manifest),
        "materialization_manifest_sha256": sha256_path(args.materialization_manifest),
        "environment_manifest_sha256": sha256_path(args.environment_manifest),
        "image_reference": image,
        "network_mode": "none",
        "cpp_standard": "c++17",
        "task_count": 51,
        "tasks_passed": sum(item["compile_and_run_passed"] for item in task_receipts),
        "all_tasks_probed_not_sampled": True,
        "exact_task_packages_probed": True,
        "external_packages": [],
        "sanitizers": ["address", "undefined"],
        "container_returncode": completed.returncode,
        "stderr": completed.stderr[-4000:],
        "tasks": task_receipts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, args.output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    print(json.dumps({"decision": decision, "tasks_passed": receipt["tasks_passed"]}, sort_keys=True))
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
