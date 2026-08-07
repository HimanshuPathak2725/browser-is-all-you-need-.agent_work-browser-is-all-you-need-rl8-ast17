#!/usr/bin/env python3
"""Strictly compile and execute every reference package in a frozen V1 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SCHEMA = "charm-v1-manifest-reference-sweep-v1"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run(command: list[str], *, cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite sweep receipt: {args.output}")
    manifest = json.loads(args.materialization_manifest.read_text(encoding="utf-8"))
    tasks = manifest.get("tasks")
    if manifest.get("schema_version") != "charm-v1-materialization-manifest-v1" or not isinstance(tasks, list) or len(tasks) != 51:
        raise ValueError("manifest must be the exact 51-task CHARM V1 materialization manifest")
    compilers = [name for name in ("g++", "clang++") if shutil.which(name)]
    if set(compilers) != {"g++", "clang++"}:
        raise RuntimeError("both g++ and clang++ are required")
    compiler_identities = {}
    for compiler in compilers:
        version = subprocess.run([compiler, "--version"], text=True, capture_output=True, check=True)
        compiler_identities[compiler] = version.stdout.splitlines()[0]
    rows = []
    for index, task in enumerate(tasks):
        task_id = task.get("task_id")
        files = task.get("files")
        hashes = task.get("file_sha256s")
        if not isinstance(task_id, str) or not isinstance(files, dict) or not isinstance(hashes, dict) or set(files) != set(hashes):
            raise ValueError(f"invalid package record at index {index}")
        if any(hashlib.sha256(value.encode()).hexdigest() != hashes[name] for name, value in files.items()):
            raise ValueError(f"package hash mismatch: {task_id}")
        attempts = []
        with tempfile.TemporaryDirectory(prefix=f"charm-v1-sweep-{index:02d}-") as raw:
            root = Path(raw)
            for name, value in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value, encoding="utf-8")
            reference = root / ".reference"
            if not reference.is_dir():
                raise ValueError(f"reference directory missing: {task_id}")
            for source in reference.iterdir():
                if source.is_file():
                    shutil.copyfile(source, root / source.name)
            rubric = json.loads((root / ".rubric.json").read_text(encoding="utf-8"))
            editable = rubric.get("editable_files")
            hidden = rubric.get("hidden_test_file")
            if not isinstance(editable, list) or not isinstance(hidden, str):
                raise ValueError(f"invalid rubric: {task_id}")
            hidden_text = (root / hidden).read_text(encoding="utf-8")
            source_files = [
                name for name in editable
                if name.endswith((".cpp", ".cc")) and f'#include "{name}"' not in hidden_text
            ]
            header_attempts = []
            for header in (name for name in editable if name.endswith((".h", ".hpp"))):
                probe = root / f"header-probe-{len(header_attempts)}.cpp"
                probe.write_text(f'#include "{header}"\nint main() {{ return 0; }}\n', encoding="utf-8")
                for compiler in compilers:
                    result = run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", "-pthread", "-I", str(root), "-fsyntax-only", str(probe)], cwd=root)
                    header_attempts.append({"header": header, "compiler": compiler, "passed": result.returncode == 0, "stderr": result.stderr[-4000:]})
            for compiler in compilers:
                binary = root / f"task-{compiler.replace('+', 'p')}"
                command = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic", "-pthread", "-I", str(root), *[str(root / name) for name in source_files], str(root / hidden), "-o", str(binary)]
                compiled = run(command, cwd=root)
                executions = []
                if compiled.returncode == 0:
                    for _ in range(2):
                        executed = run([str(binary)], cwd=root, timeout=20)
                        executions.append({"returncode": executed.returncode, "stdout_sha256": hashlib.sha256(executed.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(executed.stderr.encode()).hexdigest()})
                passed = compiled.returncode == 0 and len(executions) == 2 and all(item["returncode"] == 0 for item in executions) and executions[0] == executions[1]
                attempts.append({"compiler": compiler, "passed": passed, "compile_returncode": compiled.returncode, "compile_stderr": compiled.stderr[-6000:], "executions": executions})
        row_passed = all(item["passed"] for item in attempts) and all(item["passed"] for item in header_attempts)
        rows.append({"task_id": task_id, "topic": task.get("topic"), "passed": row_passed, "compiler_attempts": attempts, "header_isolation_attempts": header_attempts})
        print(json.dumps({"task_id": task_id, "passed": row_passed}), flush=True)
    receipt = {
        "schema_version": SCHEMA,
        "decision": "PASS" if len(rows) == 51 and all(row["passed"] for row in rows) else "FAIL",
        "generation_batch_id": manifest.get("generation_batch_id"),
        "generation_session_id": manifest.get("generation_session_id"),
        "materialization_manifest_sha256": sha256(args.materialization_manifest),
        "owner_source_sha256": sha256(Path(__file__)),
        "compiler_identities": compiler_identities,
        "cpp_standard": "c++17",
        "strict_warnings_as_errors": True,
        "task_count": len(rows),
        "tasks_passed": sum(row["passed"] for row in rows),
        "all_tasks_probed_not_sampled": True,
        "deterministic_double_execution": True,
        "tasks": rows,
    }
    atomic_write(args.output, canonical(receipt))
    print(json.dumps({"decision": receipt["decision"], "tasks_passed": receipt["tasks_passed"]}), flush=True)
    return 0 if receipt["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
