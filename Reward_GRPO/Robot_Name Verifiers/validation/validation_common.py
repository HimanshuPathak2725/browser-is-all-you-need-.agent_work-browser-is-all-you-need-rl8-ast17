from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = VALIDATION_ROOT.parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-1/cpp/exercises/practice/robot-name"
)
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
SOURCE_FILES = ("robot_name.h", "robot_name.cpp")
PINNED_INSTRUCTIONS = VALIDATION_ROOT / "fixed/instructions.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verifier(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one E{number:02d} verifier, found {matches}")
    return matches[0]


def run_verifier(
    number: int, exercise: Path, output: Path, compiler: str = "g++"
) -> dict[str, Any]:
    process = subprocess.run(
        [
            "python3",
            str(verifier(number)),
            "--exercise-dir",
            str(exercise),
            "--output-dir",
            str(output),
            "--compiler",
            compiler,
            "--expected-gcc",
            "13.3",
            "--compile-timeout-s",
            "180",
            "--run-timeout-s",
            "180",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=600,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E{number:02d} did not write receipt: rc={process.returncode}; "
            f"stdout={process.stdout[-1000:]}; stderr={process.stderr[-1000:]}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "status": receipt["status"],
        "kernel_vector": [item.get("kernel") for item in receipt["kernel_results"]],
        "kernel_statuses": [item.get("status") for item in receipt["kernel_results"]],
        "kernel_summaries": [item.get("summary") for item in receipt["kernel_results"]],
        "candidate_source_sha256": receipt.get("candidate_source_sha256"),
        "preflight_error": receipt.get("preflight_error"),
        "process_returncode": process.returncode,
        "receipt_sha256": sha256(receipt_path),
    }


def saved_sources(path: str) -> dict[str, str]:
    root = VALIDATION_ROOT / path
    return {name: (root / name).read_text(encoding="utf-8") for name in SOURCE_FILES}


def reference_sources() -> dict[str, str]:
    return {
        "robot_name.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "robot_name.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }


def prepare_exercise(root: Path, sources: dict[str, str]) -> Path:
    exercise = root / "exercise"
    shutil.copytree(FIXTURE, exercise, symlinks=False)
    shutil.copy2(PINNED_INSTRUCTIONS, exercise / ".docs/instructions.md")
    for name in SOURCE_FILES:
        (exercise / name).write_text(sources[name], encoding="utf-8")
    return exercise


def candidate_case(
    case_id: str,
    sources: dict[str, str],
    output_root: Path,
    compiler: str = "g++",
) -> dict[str, Any]:
    work = output_root / "work" / case_id
    work.mkdir(parents=True)
    exercise = prepare_exercise(work, sources)
    before = {name: sha256(exercise / name) for name in SOURCE_FILES}
    policies = {
        f"E{number:02d}": run_verifier(
            number,
            exercise,
            output_root / "candidate_cases" / case_id / f"E{number:02d}",
            compiler,
        )
        for number in range(1, 6)
    }
    after = {name: sha256(exercise / name) for name in SOURCE_FILES}
    statuses = [policy["status"] for policy in policies.values()]
    pack_status = (
        "invalid" if "invalid" in statuses else "fail" if "fail" in statuses else "pass"
    )
    return {
        "case_id": case_id,
        "candidate_sha256": before,
        "source_unchanged": before == after,
        "policies": policies,
        "terminal_gate_status": policies["E03"]["status"],
        "pack_status": pack_status,
    }


def classify(source_outcome: str, gate_status: str) -> str:
    source_pass = source_outcome == "pass"
    gate_pass = gate_status == "pass"
    return {
        (True, True): "agreement_pass",
        (True, False): "restriction",
        (False, True): "missed_failure",
        (False, False): "agreement_fail",
    }[(source_pass, gate_pass)]
