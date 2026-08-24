from __future__ import annotations

import difflib
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
    / "benchmark-output-shard-1/cpp/exercises/practice/perfect-numbers"
)
VERIFIER_ROOT = PACKAGE_ROOT / "verifiers"
SOURCE_FILES = ("perfect_numbers.h", "perfect_numbers.cpp")
PINNED_INSTRUCTIONS = VALIDATION_ROOT / "fixed/instructions.md"
OFFICIAL_TEST_SHA256 = "fa206f8feaa1f8aa63986db34fc96458b30ab0325c0855fd6659ab7cbcb50be3"
TEST_UUIDS = (
    "163e8e86-7bfd-4ee2-bd68-d083dc3381a3",
    "169a7854-0431-4ae0-9815-c3b6d967436d",
    "ee3627c4-7b36-4245-ba7c-8727d585f402",
    "80ef7cf8-9ea8-49b9-8b2d-d9cb3db3ed7e",
    "3e300e0d-1a12-4f11-8c48-d1027165ab60",
    "ec7792e6-8786-449c-b005-ce6dd89a772b",
    "e610fdc7-2b6e-43c3-a51c-b70fb37413ba",
    "0beb7f66-753a-443f-8075-ad7fbd9018f3",
    "1c802e45-b4c6-4962-93d7-1cad245821ef",
    "47dd569f-9e5a-4a11-9a47-a4e91c8c28aa",
    "a696dec8-6147-4d68-afad-d38de5476a56",
    "72445cee-660c-4d75-8506-6c40089dc302",
    "2d72ce2c-6802-49ac-8ece-c790ba3dae13",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combined_source_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for name in SOURCE_FILES:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / name).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def verifier(number: int) -> Path:
    matches = sorted(VERIFIER_ROOT.glob(f"verifier_{number:02d}_*.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one E{number:02d} verifier, found {matches}")
    return matches[0]


def summarized_receipt(receipt: dict[str, Any], receipt_path: Path, process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
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


def run_source_verifier(number: int, exercise: Path, output: Path, compiler: str = "g++") -> dict[str, Any]:
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
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E{number:02d} did not write a receipt: rc={process.returncode}; "
            f"stdout={process.stdout[-1000:]}; stderr={process.stderr[-1000:]}"
        )
    return summarized_receipt(
        json.loads(receipt_path.read_text(encoding="utf-8")), receipt_path, process
    )


def run_trajectory_verifier(bundle: Path, output: Path) -> dict[str, Any]:
    process = subprocess.run(
        [
            "python3",
            str(verifier(4)),
            "--bundle-dir",
            str(bundle),
            "--output-dir",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(
            f"E04 did not write a receipt: rc={process.returncode}; "
            f"stdout={process.stdout[-1000:]}; stderr={process.stderr[-1000:]}"
        )
    return summarized_receipt(
        json.loads(receipt_path.read_text(encoding="utf-8")), receipt_path, process
    )


def saved_sources(case_id: str) -> dict[str, str]:
    root = VALIDATION_ROOT / "cases" / case_id
    return {name: (root / name).read_text(encoding="utf-8") for name in SOURCE_FILES}


def reference_sources() -> dict[str, str]:
    return {
        "perfect_numbers.h": (FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "perfect_numbers.cpp": (FIXTURE / ".meta/example.cpp").read_text(encoding="utf-8"),
    }


def prepare_exercise(root: Path, sources: dict[str, str]) -> Path:
    exercise = root / "exercise"
    shutil.copytree(FIXTURE, exercise, symlinks=False)
    shutil.copy2(PINNED_INSTRUCTIONS, exercise / ".docs/instructions.md")
    for name in SOURCE_FILES:
        (exercise / name).write_text(sources[name], encoding="utf-8")
    return exercise


def source_case(case_id: str, sources: dict[str, str], output_root: Path, compiler: str = "g++") -> dict[str, Any]:
    work = output_root / "work" / case_id
    work.mkdir(parents=True)
    exercise = prepare_exercise(work, sources)
    before = {name: sha256(exercise / name) for name in SOURCE_FILES}
    policies = {
        f"E{number:02d}": run_source_verifier(
            number, exercise, output_root / "candidate_cases" / case_id / f"E{number:02d}", compiler
        )
        for number in range(1, 4)
    }
    after = {name: sha256(exercise / name) for name in SOURCE_FILES}
    return {
        "case_id": case_id,
        "candidate_sha256": before,
        "source_unchanged": before == after,
        "policies": policies,
        "terminal_gate_status": "pass" if all(row["status"] == "pass" for row in policies.values()) else "fail"
        if all(row["status"] != "invalid" for row in policies.values())
        else "invalid",
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


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _evaluation_receipt(
    source_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    diagnostics: list[str],
    test_results: dict[str, str],
    stage: str,
    build_succeeded: bool,
) -> dict[str, Any]:
    passed = sum(value == "pass" for value in test_results.values())
    failed = sum(value == "fail" for value in test_results.values())
    return {
        "task_id": "perfect-numbers",
        "official_test_sha256": OFFICIAL_TEST_SHA256,
        "candidate_source_sha256": combined_source_sha256(source_dir),
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
        "diagnostics": diagnostics,
        "test_results": test_results,
        "passed_tests": passed,
        "failed_tests": failed,
        "selected_tests": passed + failed,
        "stage": stage,
        "build_succeeded": build_succeeded,
        "evaluation_completed": True,
        "timed_out": False,
    }


def build_trajectory(bundle: Path, trajectory: str) -> Path:
    if trajectory == "trial_1_repair":
        case_ids = ("midband_rl_v2_trial_1_turn_1", "midband_rl_v2_trial_1_final")
        feedback = "Compiler failure: classification and classify are missing from namespace perfect_numbers."
        logs = (
            ("", "error: ‘classification’ is not a member of ‘perfect_numbers’\n", ["PN-E01-API"]),
            ("test cases: 13 | 13 passed\nassertions: 13 | 13 passed\n", "", []),
        )
        outcomes = (
            ({uuid: "blocked" for uuid in TEST_UUIDS}, "compile", False),
            ({uuid: "pass" for uuid in TEST_UUIDS}, "complete", True),
        )
    elif trajectory == "trial_4_regression":
        case_ids = ("midband_rl_v2_trial_4_turn_1", "midband_rl_v2_trial_4_final")
        feedback = "Edge case classify(1) failed: expected deficient, observed perfect."
        first = {uuid: "pass" for uuid in TEST_UUIDS}
        first["a696dec8-6147-4d68-afad-d38de5476a56"] = "fail"
        second = {uuid: "pass" for uuid in TEST_UUIDS}
        for uuid in TEST_UUIDS[:3]:
            second[uuid] = "fail"
        logs = (
            ("Edge case classify(1) FAILED\ntest cases: 13 | 12 passed | 1 failed\n", "", ["PN-E02-ONE"]),
            ("Perfect cases FAILED\ntest cases: 13 | 10 passed | 3 failed\n", "", []),
        )
        outcomes = ((first, "test", True), (second, "test", True))
    else:
        raise RuntimeError(f"unknown trajectory: {trajectory}")

    bundle.mkdir(parents=True)
    (bundle / "generated_feedback.txt").write_text(feedback + "\n", encoding="utf-8")
    (bundle / "delivered_feedback.txt").write_text(feedback + "\n", encoding="utf-8")
    for index, turn in enumerate(("turn_1", "turn_2")):
        turn_dir = bundle / turn
        source_dir = turn_dir / "source"
        source_dir.mkdir(parents=True)
        for name, content in saved_sources(case_ids[index]).items():
            (source_dir / name).write_text(content, encoding="utf-8")
        response = f"Authenticated Midband-RL-v2 {case_ids[index]} response snapshot.\n"
        response_path = turn_dir / "response.txt"
        response_path.write_text(response, encoding="utf-8")
        _write_json(turn_dir / "response_receipt.json", {"status": "completed", "response_sha256": sha256(response_path)})
        stdout_path = turn_dir / "evaluation.stdout.log"
        stderr_path = turn_dir / "evaluation.stderr.log"
        stdout_path.write_text(logs[index][0], encoding="utf-8")
        stderr_path.write_text(logs[index][1], encoding="utf-8")
        tests, stage, build = outcomes[index]
        receipt = _evaluation_receipt(
            source_dir, stdout_path, stderr_path, logs[index][2], tests, stage, build
        )
        _write_json(turn_dir / "evaluation_receipt.json", receipt)

    diff: list[str] = []
    for name in SOURCE_FILES:
        before = (bundle / "turn_1/source" / name).read_text(encoding="utf-8")
        after = (bundle / "turn_2/source" / name).read_text(encoding="utf-8")
        diff.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"turn_1/{name}",
                tofile=f"turn_2/{name}",
            )
        )
    (bundle / "turn_2/turn_2.diff").write_text("".join(diff), encoding="utf-8")
    files = {
        path.relative_to(bundle).as_posix(): sha256(path)
        for path in sorted(bundle.rglob("*"))
        if path.is_file()
    }
    _write_json(
        bundle / "manifest.json",
        {
            "schema_version": 1,
            "task_id": "perfect-numbers",
            "official_test_sha256": OFFICIAL_TEST_SHA256,
            "authorized_files": list(SOURCE_FILES),
            "files": files,
        },
    )
    return bundle
