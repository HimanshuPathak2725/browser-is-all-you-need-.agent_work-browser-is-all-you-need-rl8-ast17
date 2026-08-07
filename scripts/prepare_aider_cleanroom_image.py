#!/usr/bin/env python3
"""Finalize and attest the pinned Aider clean-room evaluation image."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


BENCHMARK_GIT_BLOCK = """    repo = git.Repo(search_parent_directories=True)
    commit_hash = repo.head.object.hexsha[:7]
    if repo.is_dirty():
        commit_hash += "-dirty"
"""


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True
    ).strip()


def patch_benchmark_commit_lookup(benchmark_py: Path, aider_commit: str) -> None:
    text = benchmark_py.read_text(encoding="utf-8")
    if text.count(BENCHMARK_GIT_BLOCK) != 1:
        raise RuntimeError("pinned benchmark.py git lookup did not match exactly once")
    replacement = f'    commit_hash = "{aider_commit[:7]}-cleanroom"\n'
    benchmark_py.write_text(text.replace(BENCHMARK_GIT_BLOCK, replacement), encoding="utf-8")


def reject_historical_artifacts(*roots: Path) -> None:
    forbidden_names = {
        ".aider.results.json",
        "adapter_config.json",
        "adapter_model.bin",
        "grpo_training_gate.json",
        "run_receipt.json",
        "training_state_rank0.pt",
        "wandb-summary.json",
    }
    forbidden_dirs = {"rollout_dumps", "wandb"}
    violations: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.name in forbidden_names or (path.is_dir() and path.name in forbidden_dirs):
                violations.append(str(path))
    if violations:
        raise RuntimeError(f"historical artifacts found in clean-room image: {violations[:20]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aider-root", type=Path, default=Path("/aider"))
    parser.add_argument("--benchmark-root", type=Path, default=Path("/benchmark"))
    parser.add_argument("--cleanroom-root", type=Path, default=Path("/opt/cleanroom"))
    parser.add_argument("--aider-commit", required=True)
    parser.add_argument("--polyglot-commit", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    aider_root = args.aider_root.resolve()
    benchmark_root = args.benchmark_root.resolve()
    cleanroom_root = args.cleanroom_root.resolve()
    cleanroom_root.mkdir(parents=True, exist_ok=True)

    actual_aider = git_value(aider_root, "rev-parse", "HEAD")
    actual_polyglot = git_value(benchmark_root, "rev-parse", "HEAD")
    if actual_aider != args.aider_commit:
        raise RuntimeError(f"Aider commit mismatch: {actual_aider} != {args.aider_commit}")
    if actual_polyglot != args.polyglot_commit:
        raise RuntimeError(
            f"Polyglot commit mismatch: {actual_polyglot} != {args.polyglot_commit}"
        )

    aider_tree = git_value(aider_root, "rev-parse", "HEAD^{tree}")
    polyglot_tree = git_value(benchmark_root, "rev-parse", "HEAD^{tree}")
    benchmark_py = aider_root / "benchmark" / "benchmark.py"
    original_benchmark_sha256 = sha256_path(benchmark_py)
    original_cpp_test_sha256 = sha256_path(aider_root / "benchmark" / "cpp-test.sh")

    patch_benchmark_commit_lookup(benchmark_py, args.aider_commit)
    shutil.copy2(
        cleanroom_root / "aider_cleanroom_cpp_test.sh", aider_root / "benchmark/cpp-test.sh"
    )
    (aider_root / "benchmark/cpp-test.sh").chmod(0o755)

    pip_freeze = subprocess.check_output(
        ["/opt/aider-venv/bin/python", "-m", "pip", "freeze", "--all"], text=True
    )
    freeze_path = cleanroom_root / "aider-pip-freeze.txt"
    freeze_path.write_text(pip_freeze, encoding="utf-8")
    dpkg_versions = subprocess.check_output(
        ["dpkg-query", "-W", "-f=${binary:Package}=${Version}\\n"], text=True
    )
    dpkg_path = cleanroom_root / "dpkg-versions.txt"
    dpkg_path.write_text(dpkg_versions, encoding="utf-8")

    shutil.rmtree(aider_root / ".git")
    shutil.rmtree(benchmark_root / ".git")
    if (aider_root / ".git").exists() or (benchmark_root / ".git").exists():
        raise RuntimeError("git metadata survived clean-room image finalization")
    reject_historical_artifacts(aider_root, benchmark_root)

    task_root = benchmark_root / "cpp/exercises/practice"
    tasks = sorted(path.name for path in task_root.iterdir() if path.is_dir())
    if len(tasks) != 26:
        raise RuntimeError(f"fixed C++ task count mismatch: {len(tasks)} != 26")

    manifest = {
        "schema_version": 1,
        "kind": "aider-gpt56-luna-cleanroom-image",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "aider_commit": args.aider_commit,
        "aider_git_tree": aider_tree,
        "polyglot_commit": args.polyglot_commit,
        "polyglot_git_tree": polyglot_tree,
        "aider_requirements_sha256": sha256_path(aider_root / "requirements.txt"),
        "aider_pip_freeze_sha256": sha256_path(freeze_path),
        "dpkg_versions_sha256": sha256_path(dpkg_path),
        "original_benchmark_py_sha256": original_benchmark_sha256,
        "patched_benchmark_py_sha256": sha256_path(benchmark_py),
        "original_cpp_test_sha256": original_cpp_test_sha256,
        "cleanroom_cpp_test_sha256": sha256_path(aider_root / "benchmark/cpp-test.sh"),
        "cleanroom_no_network_exec_sha256": sha256_path(
            Path("/usr/local/bin/cleanroom-no-network-exec")
        ),
        "cleanroom_no_network_source_sha256": sha256_path(
            cleanroom_root / "aider_cleanroom_no_network_exec.c"
        ),
        "cleanroom_runtime_sha256": sha256_path(
            cleanroom_root / "aider_cleanroom_runtime.py"
        ),
        "cleanroom_image_preparer_sha256": sha256_path(
            cleanroom_root / "prepare_aider_cleanroom_image.py"
        ),
        "git_metadata_removed": True,
        "historical_artifact_scan_passed": True,
        "fixed_cpp_tasks": tasks,
    }
    (cleanroom_root / "image_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
