from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER = (
    REPO_ROOT
    / "Reward_GRPO/Allergies Verifiers/verifiers/verifier_05_feedback_repair_closure.py"
)
BASELINE_COMMIT = "56edd9767fc8426776fe3f5379c5815a18383e59"
BASELINE_PATH = "Reward_GRPO/Allergies Verifiers/verifiers/verifier_05_feedback_repair_closure.py"
BASELINE_SHA256 = "96bb2af9825ca6c18b9e317d27d33d09eff3aa6d766528f5d75f9e598f50150f"
SOURCE_CASE_1 = VALIDATION_ROOT / "cases/midband_rl_v2_trial_1_turn_1"
SOURCE_CASE_2 = VALIDATION_ROOT / "cases/midband_rl_v2_trial_1_turn_2"
SOURCE_CHAT_SHA256 = "640cd0447e37b98c32bfa291325386f068cfe2f887acb42f537c016ca3ba041b"
SOURCE_RESULTS_SHA256 = "13445fc267e0251859006d3ea5160860e3fe6d1e4194b6fd385f1249d4615ef6"
LEGACY_REQUEST = (
    REPO_ROOT
    / "results/luna-fixed26-20260805/raw/trial-2/allergies/turn-2/request.json"
)
LEGACY_REQUEST_SHA256 = "9603b0f84646d5c4e9b16b20356e757e81ba987c76e939678c0f504ab2d62581"
LEGACY_DIAGNOSTIC_SHA256 = "c569e8a37dd365792629349033e80785bcfb0558415249aa2da367dfa52130d9"
TURN_1_OUTPUT = """CMake configured with GNU 13.3.0.
In file included from /aider/allergies/allergies_test.cpp:1:
/aider/allergies/allergies.h:16:17: error: ‘unordered_map’ in namespace ‘std’ does not name a template type
/aider/allergies/allergies.h:5:1: note: ‘std::unordered_map’ is defined in header ‘<unordered_map>’; did you forget to ‘#include <unordered_map>’?
make[2]: *** [CMakeFiles/allergies.dir/build.make:79: CMakeFiles/allergies.dir/allergies_test.cpp.o] Error 1
make[1]: *** [CMakeFiles/Makefile2:90: CMakeFiles/allergies.dir/all] Error 2
make: *** [Makefile:91: all] Error 2
"""
TURN_2_OUTPUT = """CMake configured with GNU 13.3.0.
[100%] Built target allergies
===============================================================================
All tests passed (50 assertions in 50 test cases)
[100%] Built target test_allergies
"""
FEEDBACK = """In allergies.h, std::unordered_map is used but <unordered_map> is not included. The tests are correct; add the required standard-library include without changing the API.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def candidate_files(source: Path) -> list[dict[str, str]]:
    return [
        {"path": name, "sha256": sha256(source / name)}
        for name in ("allergies.h", "allergies.cpp")
    ]


def score_receipt(source: Path, output: str, status: str, returncode: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": "local-aider-cpp/allergies",
        "source_run_id": "execution-bank-RL-v2-think-r2/fixed26-mt2-4x-20260818",
        "source_trial": 1,
        "candidate_files": candidate_files(source),
        "output": output,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "status": status,
        "returncode": returncode,
        "source_chat_sha256": SOURCE_CHAT_SHA256,
        "source_results_sha256": SOURCE_RESULTS_SHA256,
    }


def build_bundle(root: Path) -> Path:
    bundle = root / "bundle"
    turn_1 = bundle / "turn_1"
    turn_2 = bundle / "turn_2"
    for turn, source in ((turn_1, SOURCE_CASE_1), (turn_2, SOURCE_CASE_2)):
        write_text(turn / "source/allergies.h", (source / "allergies.h").read_text(encoding="utf-8"))
        write_text(turn / "source/allergies.cpp", (source / "allergies.cpp").read_text(encoding="utf-8"))
    write_text(turn_1 / "response.txt", "Exact turn-one source snapshot is hash-bound in turn_1/source.\n")
    write_text(turn_2 / "response.txt", "Exact turn-two source snapshot is hash-bound in turn_2/source.\n")
    write_text(turn_1 / "generated_feedback.txt", FEEDBACK)
    write_text(turn_2 / "delivered_feedback.txt", FEEDBACK)
    write_text(
        turn_1 / "score_receipt.json",
        json.dumps(score_receipt(SOURCE_CASE_1, TURN_1_OUTPUT, "failed", 2), indent=2, sort_keys=True) + "\n",
    )
    write_text(
        turn_2 / "score_receipt.json",
        json.dumps(score_receipt(SOURCE_CASE_2, TURN_2_OUTPUT, "passed", 0), indent=2, sort_keys=True) + "\n",
    )
    before = (SOURCE_CASE_1 / "allergies.h").read_text(encoding="utf-8").splitlines(keepends=True)
    after = (SOURCE_CASE_2 / "allergies.h").read_text(encoding="utf-8").splitlines(keepends=True)
    write_text(
        turn_2 / "source.diff",
        "".join(difflib.unified_diff(before, after, fromfile="turn_1/allergies.h", tofile="turn_2/allergies.h")),
    )
    required = {
        "turn_1_response": "turn_1/response.txt",
        "turn_1_allergies_h": "turn_1/source/allergies.h",
        "turn_1_allergies_cpp": "turn_1/source/allergies.cpp",
        "turn_1_score_receipt": "turn_1/score_receipt.json",
        "generated_feedback": "turn_1/generated_feedback.txt",
        "delivered_feedback": "turn_2/delivered_feedback.txt",
        "turn_2_response": "turn_2/response.txt",
        "turn_2_allergies_h": "turn_2/source/allergies.h",
        "turn_2_allergies_cpp": "turn_2/source/allergies.cpp",
        "turn_2_score_receipt": "turn_2/score_receipt.json",
        "turn_2_source_diff": "turn_2/source.diff",
    }
    manifest = {
        "schema_version": 1,
        "task_id": "local-aider-cpp/allergies",
        "trajectory_kind": "two_turn",
        "repair_class": "build.missing_unordered_map_include",
        "source_sample_id": "execution-bank-RL-v2-think-r2/fixed26-mt2-4x-20260818/trial-1/allergies",
        "source_chat_sha256": SOURCE_CHAT_SHA256,
        "source_results_sha256": SOURCE_RESULTS_SHA256,
        "artifacts": {
            key: {"path": relative, "sha256": sha256(bundle / relative)}
            for key, relative in required.items()
        },
    }
    write_text(bundle / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return bundle


def run_verifier(script: Path, bundle: Path, output: Path) -> dict[str, Any]:
    process = subprocess.run(
        [
            "python3",
            str(script),
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
        raise RuntimeError(f"missing trajectory receipt: {process.stderr}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "process_returncode": process.returncode,
        "overall_status": receipt["overall_status"],
        "counts": receipt["counts"],
        "kernel_sum": receipt["kernel_sum"],
        "kernels": [
            {
                "kernel": item["kernel"],
                "result": item["result"],
                "score": item["score"],
                "reason": item["reason"],
                "evidence": item["evidence"],
            }
            for item in receipt["kernels"]
        ],
        "verifier_sha256": receipt["verifier_sha256"],
        "receipt_sha256": sha256(receipt_path),
    }


def refresh_manifest_artifact_hashes(bundle: Path) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("artifacts", {}).values():
        entry["sha256"] = sha256(bundle / entry["path"])
    write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def control_bundles(root: Path, source_bundle: Path, output_root: Path) -> dict[str, Any]:
    single = root / "single_turn_bundle"
    single.mkdir()
    write_text(
        single / "manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "local-aider-cpp/allergies",
                "trajectory_kind": "single_turn",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    tampered = root / "tampered_feedback_bundle"
    shutil.copytree(source_bundle, tampered)
    write_text(
        tampered / "turn_2/delivered_feedback.txt",
        FEEDBACK + "This line was not generated by the evaluator.\n",
    )
    refresh_manifest_artifact_hashes(tampered)

    unknown = root / "unknown_repair_class_bundle"
    shutil.copytree(source_bundle, unknown)
    unknown_manifest_path = unknown / "manifest.json"
    unknown_manifest = json.loads(unknown_manifest_path.read_text(encoding="utf-8"))
    unknown_manifest["repair_class"] = "build.unsupported_arbitrary_diagnostic"
    write_text(
        unknown_manifest_path,
        json.dumps(unknown_manifest, indent=2, sort_keys=True) + "\n",
    )

    persistent = root / "persistent_diagnostic_bundle"
    shutil.copytree(source_bundle, persistent)
    turn_2_receipt_path = persistent / "turn_2/score_receipt.json"
    turn_2_receipt = json.loads(turn_2_receipt_path.read_text(encoding="utf-8"))
    turn_2_receipt.update(
        {
            "output": TURN_1_OUTPUT,
            "output_sha256": hashlib.sha256(TURN_1_OUTPUT.encode()).hexdigest(),
            "status": "failed",
            "returncode": 2,
        }
    )
    write_text(
        turn_2_receipt_path,
        json.dumps(turn_2_receipt, indent=2, sort_keys=True) + "\n",
    )
    refresh_manifest_artifact_hashes(persistent)

    controls = {
        "single_turn": run_verifier(VERIFIER, single, output_root / "single_turn"),
        "tampered_feedback": run_verifier(
            VERIFIER, tampered, output_root / "tampered_feedback"
        ),
        "unknown_repair_class": run_verifier(
            VERIFIER, unknown, output_root / "unknown_repair_class"
        ),
        "persistent_diagnostic": run_verifier(
            VERIFIER, persistent, output_root / "persistent_diagnostic"
        ),
    }
    expected = {
        "single_turn": "NOT_APPLICABLE",
        "tampered_feedback": "INVALID",
        "unknown_repair_class": "INVALID",
        "persistent_diagnostic": "FAIL",
    }
    for name, status in expected.items():
        if controls[name]["overall_status"] != status:
            raise RuntimeError(
                f"E05 control drift for {name}: expected {status}, "
                f"observed {controls[name]['overall_status']}"
            )
    return controls


def legacy_repair_class_control() -> dict[str, Any]:
    if sha256(LEGACY_REQUEST) != LEGACY_REQUEST_SHA256:
        raise RuntimeError("legacy Luna Allergies request digest mismatch")
    request = json.loads(LEGACY_REQUEST.read_text(encoding="utf-8"))
    diagnostic = request["messages"][-1]["content"]
    if hashlib.sha256(diagnostic.encode()).hexdigest() != LEGACY_DIAGNOSTIC_SHA256:
        raise RuntimeError("legacy Luna Allergies diagnostic digest mismatch")
    namespace = runpy.run_path(str(VERIFIER))
    observed = namespace["_diagnostic_class"](diagnostic)
    expected = "api.is_allergic_to.parameter_type"
    if observed != expected:
        raise RuntimeError(
            f"legacy E05 repair class drift: expected {expected}, observed {observed}"
        )
    return {
        "source_sample_id": "luna-fixed26-20260805/trial-2/allergies/turn-1-feedback",
        "source_request_sha256": LEGACY_REQUEST_SHA256,
        "diagnostic_sha256": LEGACY_DIAGNOSTIC_SHA256,
        "expected_repair_class": expected,
        "observed_repair_class": observed,
        "status": "PASS",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise SystemExit("STRANGE_ISOLATED_REPLAY=1 is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise SystemExit("--output-dir must be empty")

    with tempfile.TemporaryDirectory(prefix="allergies-trajectory-") as temporary:
        root = Path(temporary)
        bundle = build_bundle(root)
        baseline_text = subprocess.check_output(
            ["git", "-c", f"safe.directory={REPO_ROOT}", "show", f"{BASELINE_COMMIT}:{BASELINE_PATH}"],
            cwd=REPO_ROOT,
        )
        baseline_script = root / "baseline_verifier_05.py"
        baseline_script.write_bytes(baseline_text)
        if sha256(baseline_script) != BASELINE_SHA256:
            raise RuntimeError("baseline E05 verifier digest mismatch")
        baseline = run_verifier(baseline_script, bundle, args.output_dir / "baseline")
        current = run_verifier(VERIFIER, bundle, args.output_dir / "current")
        controls = control_bundles(
            root, bundle, args.output_dir / "evidence_controls"
        )
        legacy = legacy_repair_class_control()
        if baseline["overall_status"] != "INVALID":
            raise RuntimeError("baseline E05 unexpectedly recognized the new repair class")
        if current["overall_status"] != "PASS" or current["kernel_sum"] != 5:
            raise RuntimeError("current E05 did not fully pass the real Midband repair")
        payload = {
            "schema_version": 1,
            "task_id": "local-aider-cpp/allergies",
            "source_run_id": "execution-bank-RL-v2-think-r2/fixed26-mt2-4x-20260818",
            "source_sample_id": "trial-1/allergies/turn-1-to-turn-2",
            "repair_class": "build.missing_unordered_map_include",
            "source_chat_sha256": SOURCE_CHAT_SHA256,
            "source_results_sha256": SOURCE_RESULTS_SHA256,
            "bundle_manifest_sha256": sha256(bundle / "manifest.json"),
            "baseline_commit": BASELINE_COMMIT,
            "baseline": baseline,
            "current": current,
            "evidence_controls": controls,
            "legacy_repair_class_control": legacy,
        }
        receipt = args.output_dir / "trajectory_validation_receipt.json"
        receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "receipt": str(receipt),
                    "receipt_sha256": sha256(receipt),
                    "baseline_status": baseline["overall_status"],
                    "current_status": current["overall_status"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
