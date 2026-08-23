from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    REPO_ROOT
    / "local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z"
    / "benchmark-output-shard-0/cpp/exercises/practice/allergies"
)
VERIFIER_ROOT = REPO_ROOT / "Reward_GRPO/Allergies Verifiers/verifiers"
OFFICIAL_TEST_SHA256 = "1eb815ad37a6792bba827c994d0db4cc0edaa57c4428271bef002901e43da798"
SOURCE_FILES = ("allergies.h", "allergies.cpp")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy_script(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one verifier for policy {number}, found {matches}")
    return matches[0]


def run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def read_policy_receipt(path: Path, process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing verifier receipt: {path}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    return {
        "overall_status": receipt.get("overall_status", "INVALID"),
        "kernel_vector": [item.get("score") for item in receipt.get("kernels", [])],
        "kernel_verdicts": [item.get("verdict") for item in receipt.get("kernels", [])],
        "receipt_sha256": sha256(path),
        "process_returncode": process.returncode,
        "verifier_sha256": receipt.get("verifier_sha256"),
        "candidate_source_sha256": receipt.get("candidate_source_sha256"),
        "source_unchanged": receipt.get("source_unchanged"),
        "preflight_error": receipt.get("preflight_error"),
    }


def replay_case(row: dict[str, Any], output_root: Path) -> dict[str, Any]:
    stored = VALIDATION_ROOT / row["source_path"]
    for name in SOURCE_FILES:
        observed = sha256(stored / name)
        expected = row["candidate_sha256"][name]
        if observed != expected:
            raise RuntimeError(f"candidate digest mismatch for {row['case_id']}/{name}")

    with tempfile.TemporaryDirectory(prefix="allergies-gap-") as temporary:
        exercise = Path(temporary) / "exercise"
        shutil.copytree(FIXTURE, exercise, symlinks=False)
        for name in SOURCE_FILES:
            shutil.copy2(stored / name, exercise / name)
        before = {name: sha256(exercise / name) for name in SOURCE_FILES}

        policies: dict[str, dict[str, Any]] = {}
        for number in (1, 2, 3, 4, 6):
            destination = output_root / "cases" / row["case_id"] / f"policy_{number:02d}"
            process = run(
                [
                    "python3",
                    str(policy_script(number)),
                    "--exercise-dir",
                    str(exercise),
                    "--output-dir",
                    str(destination),
                ]
            )
            policies[f"E{number:02d}"] = read_policy_receipt(
                destination / "verification_receipt.json", process
            )

        after = {name: sha256(exercise / name) for name in SOURCE_FILES}
        diagnostic_pass = all(
            policies[f"E{number:02d}"]["overall_status"] == "PASS"
            for number in (1, 2, 3, 4)
        )
        official_pass = policies["E06"]["overall_status"] == "PASS"
        classification = {
            (True, True): "agreement_pass",
            (True, False): "missed_failure",
            (False, True): "restriction",
            (False, False): "agreement_fail",
        }[(diagnostic_pass, official_pass)]
        if classification != row["expected_classification"]:
            raise RuntimeError(
                f"classification drift for {row['case_id']}: expected "
                f"{row['expected_classification']}, observed {classification}"
            )
        return {
            "case_id": row["case_id"],
            "source_sample_id": row["source_sample_id"],
            "source_outcome": row["source_outcome"],
            "failure_class": row["failure_class"],
            "candidate_sha256": before,
            "source_unchanged": before == after,
            "policies": policies,
            "diagnostic_pack_pass": diagnostic_pass,
            "official_pass": official_pass,
            "classification": classification,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    if args.workers < 1 or args.workers > 8:
        raise SystemExit("--workers must be between 1 and 8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")

    compiler = subprocess.check_output(
        ["g++", "-dumpfullversion", "-dumpversion"], text=True
    ).strip()
    if compiler != "13.3.0":
        raise SystemExit(f"expected GCC 13.3.0, observed {compiler}")
    if sha256(FIXTURE / "allergies_test.cpp") != OFFICIAL_TEST_SHA256:
        raise SystemExit("official test digest mismatch")

    manifest_path = VALIDATION_ROOT / "failure_gap_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for policy_id, expected in manifest["baseline"]["verifier_sha256"].items():
        number = int(policy_id[1:])
        if sha256(policy_script(number)) != expected:
            raise SystemExit(f"unchanged baseline verifier digest mismatch: {policy_id}")
    if sha256(policy_script(6)) != manifest["official"]["verifier_sha256"]:
        raise SystemExit("official verifier digest mismatch")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        samples = list(
            executor.map(
                lambda row: replay_case(row, args.output_dir), manifest["cases"]
            )
        )
    samples.sort(key=lambda row: row["case_id"])
    if any(not row["source_unchanged"] for row in samples):
        raise RuntimeError("a verifier changed candidate source bytes")
    classifications = Counter(row["classification"] for row in samples)
    if classifications.get("missed_failure", 0) or classifications.get("restriction", 0):
        raise RuntimeError("unchanged diagnostic pack disagrees with the official suite")

    payload = {
        "schema_version": 1,
        "task_id": manifest["task_id"],
        "source_run_id": manifest["source_run_id"],
        "source_checkpoint": manifest["source_checkpoint"],
        "compiler": compiler,
        "fixture_sha256": {
            "allergies_test.cpp": sha256(FIXTURE / "allergies_test.cpp"),
            "test/catch.hpp": sha256(FIXTURE / "test/catch.hpp"),
            "test/tests-main.cpp": sha256(FIXTURE / "test/tests-main.cpp"),
            "CMakeLists.txt": sha256(FIXTURE / "CMakeLists.txt"),
        },
        "manifest_sha256": sha256(manifest_path),
        "sample_count": len(samples),
        "classification_counts": dict(sorted(classifications.items())),
        "samples": samples,
    }
    receipt_path = args.output_dir / "failure_gap_replay_receipt.json"
    receipt_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "receipt": str(receipt_path),
                "receipt_sha256": sha256(receipt_path),
                "classification_counts": payload["classification_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
