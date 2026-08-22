#!/usr/bin/env python3
"""Run the Clock Version 2 verifier pack over the frozen comparison corpus."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
COMPARISON = Path(__file__).resolve().parent
MANIFEST_PATH = COMPARISON / "manifest.json"
FIXTURE = Path("/tmp/clock-verifier-audit.AjXhUg/practice/clock")
WORK_ROOT = Path("/tmp/clock-v2-agent-comparison-work")
RECEIPT_ROOT = Path("/tmp/clock-v2-agent-comparison-receipts")
RESULT_PATH = COMPARISON / "results" / "v2_results.json"
RUNNER = REPO / "Reward_GRPO/clock_verifiers_v2/verifiers/run_all.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_candidate(candidate_id: str, kind: str, source: Path, expected: dict[str, str]) -> dict[str, object]:
    actual = {name: sha256(source / name) for name in ("clock.h", "clock.cpp")}
    if actual != expected:
        raise SystemExit(f"hash mismatch for {candidate_id}: expected={expected}, actual={actual}")
    return {
        "candidate_id": candidate_id,
        "kind": kind,
        "source": source,
        "candidate_sha256": actual,
    }


def load_candidates(manifest: dict[str, object]) -> list[dict[str, object]]:
    candidates = [
        checked_candidate(
            "canonical_baseline",
            "baseline",
            COMPARISON / "baseline/canonical",
            manifest["baseline"]["candidate_sha256"],
        ),
        checked_candidate(
            manifest["dataset_control"]["sample_id"],
            "dataset_control",
            COMPARISON / "controls/dataset_official_pass",
            manifest["dataset_control"]["candidate_sha256"],
        ),
    ]
    for item in manifest["samples"]:
        candidates.append(
            checked_candidate(
                item["sample_id"],
                "faulty_sample",
                COMPARISON / "samples" / item["sample_id"],
                item["candidate_sha256"],
            )
        )
    if len(candidates) != manifest["sample_count"] + 2:
        raise SystemExit("candidate count does not match manifest")
    return candidates


def main() -> int:
    if WORK_ROOT.exists() or RECEIPT_ROOT.exists():
        raise SystemExit("isolated work or receipt root already exists")
    required_fixture_files = (
        ".meta/config.json",
        ".meta/example.cpp",
        ".meta/example.h",
        ".meta/tests.toml",
        "CMakeLists.txt",
        "clock_test.cpp",
        "test/catch.hpp",
        "test/tests-main.cpp",
    )
    missing = [name for name in required_fixture_files if not (FIXTURE / name).is_file()]
    if missing:
        raise SystemExit(f"pinned fixture is incomplete: {missing}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    candidates = load_candidates(manifest)
    compiler_version = subprocess.run(
        ["g++", "--version"], check=True, capture_output=True, text=True
    ).stdout.splitlines()[0]
    WORK_ROOT.mkdir(parents=True)
    RECEIPT_ROOT.mkdir(parents=True)
    results: list[dict[str, object]] = []

    for index, candidate in enumerate(candidates, start=1):
        candidate_id = candidate["candidate_id"]
        print(f"[{index}/{len(candidates)}] {candidate_id}", flush=True)
        exercise_dir = WORK_ROOT / candidate_id
        output_dir = RECEIPT_ROOT / candidate_id
        shutil.copytree(FIXTURE, exercise_dir)
        for name in ("clock.h", "clock.cpp"):
            shutil.copy2(candidate["source"] / name, exercise_dir / name)
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--exercise-dir",
                str(exercise_dir),
                "--output-dir",
                str(output_dir),
                "--compiler",
                "g++",
                "--expected-gcc",
                "13.3",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        (output_dir / "agent_runner.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (output_dir / "agent_runner.stderr.log").write_text(completed.stderr, encoding="utf-8")
        aggregate_path = output_dir / "aggregate_receipt.json"
        if not aggregate_path.is_file():
            raise SystemExit(f"missing aggregate receipt for {candidate_id}")
        aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
        policies = []
        for policy in aggregate["category_results"]:
            status = str(policy["status"]).upper()
            policies.append(
                {
                    "policy_id": policy["policy_id"],
                    "status": status,
                    "kernel_sum": policy["kernel_sum"],
                    "maximum_kernel_sum": policy["maximum_kernel_sum"],
                    "return_code": policy["return_code"],
                    "output_directory": str(output_dir / Path(policy["filename"]).stem),
                    "receipt": policy["receipt"],
                    "receipt_sha256": policy["receipt_sha256"],
                }
            )
        invalid = any(policy["status"] == "INVALID" for policy in policies)
        failed = [policy["policy_id"] for policy in policies if policy["status"] == "FAIL"]
        terminal = next(policy for policy in policies if policy["policy_id"] == "CL2-C08")
        results.append(
            {
                "candidate_id": candidate_id,
                "kind": candidate["kind"],
                "candidate_sha256": candidate["candidate_sha256"],
                "runner_return_code": completed.returncode,
                "aggregate_status": str(aggregate["status"]).upper(),
                "suite_detected": bool(failed),
                "suite_pass": all(policy["status"] == "PASS" for policy in policies),
                "shaping_detected": any(
                    policy["status"] == "FAIL" and policy["policy_id"] != "CL2-C08"
                    for policy in policies
                ),
                "terminal_status": terminal["status"],
                "invalid": invalid,
                "failed_policy_ids": failed,
                "aggregate_receipt": str(aggregate_path),
                "aggregate_receipt_sha256": sha256(aggregate_path),
                "policies": policies,
            }
        )

    faulty = [item for item in results if item["kind"] == "faulty_sample"]
    document = {
        "schema_version": 1,
        "agent_role": "custom_version_2_verifier_tester",
        "task_id": manifest["task_id"],
        "manifest": str(MANIFEST_PATH),
        "manifest_sha256": sha256(MANIFEST_PATH),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "compiler": "g++",
        "compiler_version": compiler_version,
        "expected_gcc": "13.3",
        "verifier_runner": str(RUNNER),
        "fixture": str(FIXTURE),
        "work_root": str(WORK_ROOT),
        "receipt_root": str(RECEIPT_ROOT),
        "candidate_count": len(results),
        "faulty_sample_count": len(faulty),
        "faults_detected": sum(bool(item["suite_detected"]) for item in faulty),
        "faults_terminal_detected": sum(item["terminal_status"] == "FAIL" for item in faulty),
        "faults_shaping_detected": sum(bool(item["shaping_detected"]) for item in faulty),
        "invalid_candidate_count": sum(bool(item["invalid"]) for item in results),
        "results": results,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: document[key] for key in (
        "candidate_count", "faulty_sample_count", "faults_detected",
        "faults_terminal_detected", "faults_shaping_detected", "invalid_candidate_count",
    )}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
