#!/usr/bin/env python3
"""Execute and freeze genuine four-message CHARM V1 repair trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from glm47_posttraining.aider_polyglot.harness import (
    _run_stage,
    capture_stage_receipts,
    run_shadow_weighted45_tests,
    stage_receipt_bundle,
)
from glm47_posttraining.aider_polyglot.parser import parse_whole_file_response
from glm47_posttraining.aider_polyglot.reward import compute_weighted45_aider_reward
from glm47_posttraining.aider_polyglot.validator.oracle.oracle_runner import render_reference_response
from scripts.charm_v1_negative_controls import task_descriptor, variants
from scripts.charm_v1_redacted_feedback import FAIL_MESSAGE, POLICY_ID, build_receipt
from scripts.charm_v1_certify_materialized import validate_source_manifest
from w8_biayn.aider_task_validator.projector_v3 import _user_prompt, whole_file


SCHEMA = "charm-v1-repair-trajectory-proof-v1"
SUMMARY_SCHEMA = "charm-v1-repair-trajectory-summary-v1"
OUTCOME_SCHEMA = "charm-v1-private-repair-outcome-v1"
EXPECTED_TYPES = {
    "compile_repair": 2,
    "linker_repair": 2,
    "api_repair": 2,
    "hidden_test_repair": 2,
    "runtime_repair": 2,
    "sanitizer_repair": 1,
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical(payload))
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def append_source(files: dict[str, str], editable: list[str], suffix: str) -> dict[str, str]:
    cpp = next((name for name in editable if Path(name).suffix in {".cpp", ".cc"}), editable[0])
    result = dict(files)
    result[cpp] = result[cpp].rstrip() + "\n\n" + suffix.strip() + "\n"
    return result


def mutate(
    repair_type: str,
    task_id: str,
    editable: list[str],
    reference: dict[str, str],
    negative: dict[str, Any],
) -> tuple[str, dict[str, str]]:
    first = editable[0]
    if repair_type == "compile_repair":
        candidate = dict(reference)
        candidate[first] = "#error CHARM_V1_INTENTIONAL_COMPILE_REPAIR\n" + candidate[first]
        return "intentional-preprocessor-error", candidate
    if repair_type == "linker_repair":
        suffix = """
namespace charm_v1_linker_probe {
int intentionally_missing_definition();
const int observed = intentionally_missing_definition();
}
"""
        return "intentional-undefined-symbol", append_source(reference, editable, suffix)
    if repair_type == "api_repair":
        signatures = {
            "cyclic-hamming-starts": (
                "cyclic_hamming_starts",
                "cyclic_hamming_starts_wrong_api",
            ),
            "turn-command-self-avoidance": (
                "replay_self_avoiding_turns",
                "replay_self_avoiding_turns_wrong_api",
            ),
            "rotating-slot-allocation": (
                "const std::vector<SlotOp>& operations",
                "std::vector<SlotOp>& operations",
            ),
            "concentric-ring-sums": (
                "const std::vector<std::vector<int>>& matrix",
                "std::vector<std::vector<int>>& matrix",
            ),
            "transactional-ring-batches": (
                "const std::vector<std::vector<int>>& batches",
                "std::vector<std::vector<int>>& batches",
            ),
            "value-fed-spiral-fill": (
                "const std::vector<int>& values",
                "std::vector<int>& values",
            ),
            "minimal-rotation-period": (
                "const std::vector<int>& values",
                "std::vector<int>& values",
            ),
            "coordinate-spiral-rank": (
                "std::size_t target_column",
                "int target_column",
            ),
            "minimal-rotation-period-budgeted": (
                "const std::vector<int>& values",
                "std::vector<int>& values",
            ),
            "coordinate-spiral-rank-budgeted": (
                "std::size_t target_column",
                "int target_column",
            ),
            "josephus-elimination-rounds": (
                "std::size_t step",
                "int step",
            ),
            "matrix-peel-layer-sums": (
                "const std::vector<std::vector<int>>& matrix",
                "std::vector<std::vector<int>>& matrix",
            ),
        }
        signature = next(
            (value for suffix, value in signatures.items() if task_id.endswith(suffix)),
            None,
        )
        if signature is None:
            raise RuntimeError(f"no authorized API mutation for {task_id}")
        before, after = signature
        candidate = dict(reference)
        count = candidate[first].count(before)
        candidate[first] = candidate[first].replace(before, after)
        if count < 2:
            raise RuntimeError(
                f"public API declaration/definition mutation did not apply twice for {task_id}"
            )
        mutation_id = (
            "rename-public-function"
            if task_id.endswith(("cyclic-hamming-starts", "turn-command-self-avoidance"))
            else "change-public-parameter-type"
            if task_id.endswith((
                "coordinate-spiral-rank",
                "coordinate-spiral-rank-budgeted",
            ))
            else "remove-const-from-public-input"
        )
        return mutation_id, candidate
    if repair_type == "hidden_test_repair":
        semantic = negative.get("semantic_mutation")
        if not isinstance(semantic, dict):
            raise RuntimeError(f"missing semantic mutation proof for {task_id}")
        mutation_id = semantic.get("mutation_id")
        for observed_id, candidate in variants(reference, task_id):
            if observed_id == mutation_id:
                if sha256_bytes(canonical(candidate)) != semantic.get("candidate_sha256"):
                    raise RuntimeError(f"semantic mutation hash mismatch for {task_id}")
                return f"replay-{observed_id}", candidate
        raise RuntimeError(f"semantic mutation cannot be reconstructed for {task_id}")
    if repair_type == "runtime_repair":
        suffix = """
namespace charm_v1_runtime_probe {
struct ThrowsBeforeMain {
    ThrowsBeforeMain() { throw 4745; }
};
const ThrowsBeforeMain observed{};
}
"""
        return "uncaught-global-constructor-exception", append_source(reference, editable, suffix)
    if repair_type == "sanitizer_repair":
        suffix = """
#include <cstdlib>
#include <vector>
namespace charm_v1_sanitizer_probe {
struct ReadsPastHeapBuffer {
    ReadsPastHeapBuffer() {
        const char* control = std::getenv("CHARM_V1_SANITIZER_INDEX");
        const std::size_t index = control == nullptr ? 1U : static_cast<std::size_t>(*control != '\\0');
        const std::vector<int> values(1, 7);
        const volatile int observed = values[index];
        (void)observed;
    }
};
const ReadsPastHeapBuffer observed{};
}
"""
        return "asan-heap-buffer-overread", append_source(reference, editable, suffix)
    raise RuntimeError(f"unsupported repair type: {repair_type}")


def mechanism_observed(repair_type: str, result: Any) -> bool:
    harness = result.harness
    if harness is None or result.infrastructure_error:
        return False
    checks = harness.weighted45_checks
    compile_all = all(checks.get(f"K{index}") is True for index in range(1, 6))
    if repair_type == "compile_repair":
        return harness.status == "compile_failed" and checks.get("K3") is False
    if repair_type == "linker_repair":
        return (
            harness.status == "compile_failed"
            and all(checks.get(name) is True for name in ("K2", "K3", "K4"))
            and checks.get("K1") is False
        )
    if repair_type == "api_repair":
        return (
            harness.status == "compile_failed"
            and checks.get("K3") is True
            and checks.get("K2") is False
        )
    if repair_type == "hidden_test_repair":
        return (
            compile_all
            and all(checks.get(name) is True for name in ("R1", "R2", "R3", "R4", "R5"))
            and any(checks.get(f"H{index}") is False for index in range(1, 6))
        )
    if repair_type == "runtime_repair":
        return (
            compile_all
            and harness.status == "tests_failed"
            and any(checks.get(name) is False for name in ("R2", "R3", "R5"))
        )
    if repair_type == "sanitizer_repair":
        return (
            compile_all
            and harness.status == "tests_failed"
            and checks.get("A1") is True
            and checks.get("A2") is False
            and all(checks.get(f"H{index}") is True for index in range(1, 6))
        )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-receipt", required=True, type=Path)
    parser.add_argument("--generation-plan", required=True, type=Path)
    parser.add_argument("--oracle-summary", required=True, type=Path)
    parser.add_argument("--negative-summary", required=True, type=Path)
    parser.add_argument("--feedback-policy", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gcc-image", required=True)
    parser.add_argument("--clang-tsan-image", required=True)
    parser.add_argument("--oracle-source-manifest", required=True, type=Path)
    args = parser.parse_args()

    if args.output_dir.exists() or args.summary.exists():
        raise FileExistsError("repair output paths are immutable and must not already exist")
    materialization = load(args.materialization_receipt)
    plan = load(args.generation_plan)
    oracle_summary = load(args.oracle_summary)
    negative_summary = load(args.negative_summary)
    source_manifest = validate_source_manifest(args.oracle_source_manifest)
    source_manifest_sha256 = sha256(args.oracle_source_manifest)
    repair_source_sha256 = sha256(Path(__file__))
    if oracle_summary.get("decision") != "PASS" or negative_summary.get("decision") != "PASS":
        raise RuntimeError("oracle and negative-control summaries must pass")
    proposals = {item["task_id"]: item for item in plan["proposals"]}
    materialized = {item["task_id"]: item for item in materialization["tasks"]}
    oracle_rows = {item["task_id"]: item for item in oracle_summary["tasks"]}
    negative_rows = {item["task_id"]: item for item in negative_summary["tasks"]}
    repairs = [item for item in plan["proposals"] if item["role"] == "repair_trajectory"]
    type_counts = Counter(item["repair_type"] for item in repairs)
    if len(repairs) != 11 or dict(type_counts) != EXPECTED_TYPES:
        raise RuntimeError(f"repair plan differs from frozen 11-row mechanism allocation: {type_counts}")
    if set(proposals) != set(materialized) or set(proposals) != set(oracle_rows) or set(proposals) != set(negative_rows):
        raise RuntimeError("proof inputs do not cover the same exact task IDs")

    args.output_dir.mkdir(parents=True)
    rows = []
    for proposal in repairs:
        task_id = proposal["task_id"]
        repair_type = proposal["repair_type"]
        item = materialized[task_id]
        root = Path(item["path"])
        rubric = load(root / ".rubric.json")
        editable = list(rubric["editable_files"])
        reference = {name: (root / ".reference" / name).read_text(encoding="utf-8") for name in editable}
        instructions = (root / ".docs" / "instructions.md").read_text(encoding="utf-8")

        negative_path = Path(negative_rows[task_id]["proof_path"])
        oracle_path = Path(oracle_rows[task_id]["proof_path"])
        if sha256(negative_path) != negative_rows[task_id]["proof_sha256"]:
            raise RuntimeError(f"negative proof hash mismatch: {task_id}")
        if sha256(oracle_path) != oracle_rows[task_id]["proof_sha256"]:
            raise RuntimeError(f"oracle proof hash mismatch: {task_id}")
        negative = load(negative_path)
        oracle = load(oracle_path)
        if oracle.get("status") != "certified" or any(run.get("reward") != 1.0 for run in oracle.get("runs", [])):
            raise RuntimeError(f"corrected oracle is not certified: {task_id}")

        mutation_id, candidate = mutate(repair_type, task_id, editable, reference, negative)
        candidate_response = whole_file([
            {"path": name, "content": candidate[name]} for name in editable
        ])
        corrected_response = whole_file([
            {"path": name, "content": reference[name]} for name in editable
        ])
        if parse_whole_file_response(candidate_response, editable).files != candidate:
            raise RuntimeError(f"failing candidate parser replay mismatch: {task_id}")
        if parse_whole_file_response(corrected_response, editable).files != reference:
            raise RuntimeError(f"corrected candidate parser replay mismatch: {task_id}")
        if candidate == reference:
            raise RuntimeError(f"repair mutation did not change candidate: {task_id}")

        task = task_descriptor(root, rubric)
        image = args.clang_tsan_image if rubric["family"] == "Parallel Letter Frequency" else args.gcc_image
        with capture_stage_receipts() as stage_receipts, tempfile.TemporaryDirectory(prefix=f"repair_{task_id}_") as raw:
            workspace = Path(raw)
            (workspace / ".grader").mkdir()
            for name in editable:
                shutil.copy2(root / name, workspace / name)
            shutil.copy2(root / str(rubric["hidden_test_file"]), workspace / ".grader/test.cpp")
            compiler = _run_stage(workspace, "c++ --version", image=image, timeout_s=15)

            def runner(path: Path, files: dict[str, str]):
                return run_shadow_weighted45_tests(
                    path,
                    files,
                    image=image,
                    expected_test_sha256=str(rubric["hidden_test_sha256"]),
                    cpp_standard="c++17",
                    optimize=True,
                    hidden_werror=True,
                )

            result = compute_weighted45_aider_reward(task, workspace, candidate_response, runner=runner)

        observed = mechanism_observed(repair_type, result)
        candidate_sha = sha256_bytes(canonical(candidate))
        outcome = {
            "schema": OUTCOME_SCHEMA,
            "task_id": task_id,
            "candidate_sha256": candidate_sha,
            "oracle_receipt_sha256": sha256(oracle_path),
            "passed": False,
        }
        outcome_path = args.output_dir / f"{task_id}.private-outcome.json"
        write_new(outcome_path, outcome)
        feedback = build_receipt(outcome, sha256(outcome_path))
        feedback_path = args.output_dir / f"{task_id}.public-feedback.json"
        write_new(feedback_path, feedback)

        checks = {} if result.harness is None else result.harness.weighted45_checks
        introduction_path = root / ".docs/introduction.md"
        introduction = (
            introduction_path.read_text(encoding="utf-8")
            if introduction_path.is_file()
            else str(rubric.get("category", "C++17 repository edit"))
        )
        starter_files = [
            {"path": name, "content": (root / name).read_text(encoding="utf-8")}
            for name in editable
        ]
        messages = [
            {"role": "user", "content": _user_prompt(instructions, starter_files, "repair_trajectory")},
            {"role": "assistant", "content": candidate_response},
            {"role": "user", "content": feedback["public_feedback"]},
            {"role": "assistant", "content": corrected_response},
        ]
        passed = (
            result.parsed is not None
            and result.parsed.files == candidate
            and result.reward != 1.0
            and result.infrastructure_error is False
            and observed
            and feedback["decision"] == "PASS"
            and feedback["policy_id"] == POLICY_ID
            and feedback["public_feedback"] == FAIL_MESSAGE
            and feedback["feedback_message_count"] == 1
        )
        proof = {
            "schema_version": SCHEMA,
            "task_id": task_id,
            "role": "repair_trajectory",
            "repair_type": repair_type,
            "mutation_id": mutation_id,
            "task_tree_sha256": item["tree_sha256"],
            "image": image,
            "compiler_identity": (compiler.stdout or compiler.stderr or "unknown").splitlines()[0],
            "oracle_source_manifest_path": str(args.oracle_source_manifest.resolve()),
            "oracle_source_manifest_sha256": source_manifest_sha256,
            "oracle_source_file_count": source_manifest["source_file_count"],
            "repair_trajectory_source_sha256": repair_source_sha256,
            "message_roles": [message["role"] for message in messages],
            "messages": messages,
            "four_message_sha256": sha256_bytes(canonical(messages)),
            "failing_candidate": {
                "files": candidate,
                "files_sha256": candidate_sha,
                "response_sha256": sha256_bytes(candidate_response.encode()),
                "parser_replay_exact": result.parsed is not None and result.parsed.files == candidate,
                "reward": result.reward,
                "reason": result.reason,
                "harness_status": None if result.harness is None else result.harness.status,
                "weighted45_checks": checks,
                "mechanism_observed": observed,
                "private_outcome_path": str(outcome_path.resolve()),
                "private_outcome_sha256": sha256(outcome_path),
            },
            "public_feedback": {
                "policy_id": POLICY_ID,
                "policy_sha256": sha256(args.feedback_policy),
                "receipt_path": str(feedback_path.resolve()),
                "receipt_sha256": sha256(feedback_path),
                "content": feedback["public_feedback"],
                "message_count": feedback["feedback_message_count"],
                "private_details_disclosed": False,
            },
            "corrected_candidate": {
                "files": reference,
                "files_sha256": sha256_bytes(canonical(reference)),
                "response_sha256": sha256_bytes(corrected_response.encode()),
                "parser_replay_exact": True,
                "oracle_proof_path": str(oracle_path.resolve()),
                "oracle_proof_sha256": sha256(oracle_path),
                "oracle_certified": True,
            },
            "private_test_output_disclosed": False,
            "private_execution_receipts": stage_receipt_bundle(stage_receipts),
            "decision": "PASS" if passed else "FAIL",
        }
        proof_path = args.output_dir / f"{task_id}.repair-proof.json"
        write_new(proof_path, proof)
        rows.append({
            "task_id": task_id,
            "repair_type": repair_type,
            "decision": proof["decision"],
            "proof_path": str(proof_path.resolve()),
            "proof_sha256": sha256(proof_path),
        })
        print(json.dumps({"task_id": task_id, "repair_type": repair_type, "decision": proof["decision"], "reason": result.reason}), flush=True)

    decision = "PASS" if len(rows) == 11 and all(row["decision"] == "PASS" for row in rows) else "FAIL"
    summary = {
        "schema_version": SUMMARY_SCHEMA,
        "decision": decision,
        "task_count": len(rows),
        "repair_type_counts": dict(sorted(type_counts.items())),
        "generation_plan_sha256": sha256(args.generation_plan),
        "materialization_receipt_sha256": sha256(args.materialization_receipt),
        "oracle_summary_sha256": sha256(args.oracle_summary),
        "negative_summary_sha256": sha256(args.negative_summary),
        "feedback_policy_sha256": sha256(args.feedback_policy),
        "oracle_source_manifest_sha256": source_manifest_sha256,
        "repair_trajectory_source_sha256": repair_source_sha256,
        "tasks": rows,
    }
    write_new(args.summary, summary)
    print(json.dumps({"decision": decision, "task_count": len(rows)}, sort_keys=True), flush=True)
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
