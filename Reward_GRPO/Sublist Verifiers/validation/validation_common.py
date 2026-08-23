from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = VALIDATION_ROOT.parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-1/cpp/exercises/practice/sublist"
)
MANIFEST = REPO_ROOT / ".glm47-posttraining/imported_aider_data/tasks/train/sublist.json"
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
PINNED_INSTRUCTIONS = VALIDATION_ROOT / "fixed/instructions.md"
SOURCE_FILES = ("sublist.cpp", "sublist.h")
CANDIDATE_POLICIES = (1, 2, 3, 4, 5, 6, 9)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one E{number:02d} verifier, found {matches}")
    return matches[0]


def run_verifier(
    number: int,
    exercise: Path,
    output: Path,
    *,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    environment = os.environ.copy()
    if extra_env:
        environment.update(extra_env)
    process = subprocess.run(
        [
            "python3",
            str(verifier(number)),
            "--candidate-dir",
            str(exercise),
            "--manifest",
            str(MANIFEST),
            "--output-dir",
            str(output),
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=1200,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E{number:02d} did not write receipt: rc={process.returncode}; "
            f"stdout={process.stdout[-1000:]}; stderr={process.stderr[-1000:]}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    kernels = receipt.get("kernels", [])
    return {
        "status": receipt["status"],
        "kernel_ids": [item.get("kernel_id") for item in kernels],
        "kernel_scores": [item.get("kernel") for item in kernels],
        "kernel_statuses": [item.get("verdict") for item in kernels],
        "kernel_summaries": [item.get("summary") for item in kernels],
        "candidate_source_sha256": receipt.get("candidate_source_sha256_before"),
        "preflight_error": receipt.get("preflight_error"),
        "integrity_error": receipt.get("integrity_error"),
        "process_returncode": process.returncode,
        "receipt_sha256": sha256(receipt_path),
    }


def prepare_exercise(root: Path, sources: dict[str, str]) -> Path:
    exercise = root / "sublist"
    shutil.copytree(FIXTURE, exercise, symlinks=False)
    shutil.copy2(PINNED_INSTRUCTIONS, exercise / ".docs/instructions.md")
    for name in SOURCE_FILES:
        (exercise / name).write_text(sources[name], encoding="utf-8")
    return exercise


def temporary_exercise(prefix: str, sources: dict[str, str]):
    temporary = tempfile.TemporaryDirectory(prefix=prefix)
    exercise = prepare_exercise(Path(temporary.name), sources)
    return temporary, exercise
