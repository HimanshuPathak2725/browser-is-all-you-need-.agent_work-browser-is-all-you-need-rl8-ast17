#!/usr/bin/env python3
"""Derive V4.1 per-task receipts from immutable CHARM V1 proof artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from glm47_posttraining.aider_polyglot.parser import parse_whole_file_response
from scripts.charm_v1_redacted_feedback import FAIL_MESSAGE, POLICY_ID
from w8_biayn.aider_task_validator.projector_v3 import _user_prompt


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def tree_sha256(root: Path) -> str:
    files = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return sha256_bytes(canonical(files))


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_repair(
    *,
    task_id: str,
    proposal: dict[str, Any],
    root: Path,
    oracle_path: Path,
    repair_row: dict[str, Any],
    feedback_policy_sha256: str,
) -> tuple[dict[str, Any], Path]:
    proof_path = Path(repair_row["proof_path"])
    require(sha256(proof_path) == repair_row.get("proof_sha256"), f"repair proof hash mismatch: {task_id}")
    proof = load(proof_path)
    require(proof.get("schema_version") == "charm-v1-repair-trajectory-proof-v1", f"repair proof schema mismatch: {task_id}")
    require(proof.get("task_id") == task_id and proof.get("decision") == "PASS", f"repair proof did not pass: {task_id}")
    require(proof.get("role") == "repair_trajectory", f"repair role mismatch: {task_id}")
    require(proof.get("repair_type") == proposal.get("repair_type"), f"repair type mismatch: {task_id}")
    roles = ["user", "assistant", "user", "assistant"]
    messages = proof.get("messages")
    require(proof.get("message_roles") == roles, f"repair message roles mismatch: {task_id}")
    require(isinstance(messages, list) and [item.get("role") for item in messages] == roles, f"repair messages malformed: {task_id}")
    instructions = (root / ".docs/instructions.md").read_text(encoding="utf-8")
    introduction_path = root / ".docs/introduction.md"
    introduction = (
        introduction_path.read_text(encoding="utf-8")
        if introduction_path.is_file()
        else str(load(root / ".rubric.json").get("category", "C++17 repository edit"))
    )
    starter_files = [
        {"path": name, "content": (root / name).read_text(encoding="utf-8")}
        for name in proposal["editable_files"]
    ]
    require(
        messages[0].get("content") == _user_prompt(instructions, starter_files, "repair_trajectory"),
        f"repair prompt bytes mismatch: {task_id}",
    )
    require(
        proof.get("four_message_sha256") == sha256_bytes(canonical(messages)),
        f"repair four-message hash mismatch: {task_id}",
    )

    failing = proof.get("failing_candidate")
    corrected = proof.get("corrected_candidate")
    feedback = proof.get("public_feedback")
    require(isinstance(failing, dict) and isinstance(corrected, dict) and isinstance(feedback, dict), f"repair evidence sections missing: {task_id}")
    editable = list(proposal["editable_files"])
    failing_files = failing.get("files")
    corrected_files = corrected.get("files")
    require(isinstance(failing_files, dict) and set(failing_files) == set(editable), f"failing candidate file set mismatch: {task_id}")
    require(isinstance(corrected_files, dict) and set(corrected_files) == set(editable), f"corrected candidate file set mismatch: {task_id}")
    require(failing_files != corrected_files, f"repair candidates are identical: {task_id}")
    require(sha256_bytes(canonical(failing_files)) == failing.get("files_sha256"), f"failing candidate byte hash mismatch: {task_id}")
    require(sha256_bytes(canonical(corrected_files)) == corrected.get("files_sha256"), f"corrected candidate byte hash mismatch: {task_id}")
    require(parse_whole_file_response(messages[1]["content"], editable).files == failing_files, f"failing candidate parser replay mismatch: {task_id}")
    require(parse_whole_file_response(messages[3]["content"], editable).files == corrected_files, f"corrected candidate parser replay mismatch: {task_id}")
    require(failing.get("parser_replay_exact") is True and failing.get("reward") != 1.0, f"failing candidate was not genuinely rejected: {task_id}")
    require(failing.get("mechanism_observed") is True, f"declared repair mechanism was not observed: {task_id}")
    require(corrected.get("parser_replay_exact") is True and corrected.get("oracle_certified") is True, f"corrected candidate is not certified: {task_id}")
    require(Path(corrected["oracle_proof_path"]).resolve() == oracle_path.resolve(), f"repair oracle path mismatch: {task_id}")
    require(corrected.get("oracle_proof_sha256") == sha256(oracle_path), f"repair oracle hash mismatch: {task_id}")
    reference = {name: (root / ".reference" / name).read_text(encoding="utf-8") for name in editable}
    require(corrected_files == reference, f"corrected candidate differs from reference oracle bytes: {task_id}")

    require(messages[2].get("content") == FAIL_MESSAGE, f"public repair feedback content mismatch: {task_id}")
    require(feedback.get("content") == FAIL_MESSAGE and feedback.get("message_count") == 1, f"public feedback policy mismatch: {task_id}")
    require(feedback.get("policy_id") == POLICY_ID and feedback.get("policy_sha256") == feedback_policy_sha256, f"feedback policy binding mismatch: {task_id}")
    require(feedback.get("private_details_disclosed") is False, f"private feedback leaked: {task_id}")
    feedback_path = Path(feedback["receipt_path"])
    require(sha256(feedback_path) == feedback.get("receipt_sha256"), f"feedback receipt hash mismatch: {task_id}")
    feedback_receipt = load(feedback_path)
    require(
        feedback_receipt.get("decision") == "PASS"
        and feedback_receipt.get("passed") is False
        and feedback_receipt.get("public_feedback") == FAIL_MESSAGE
        and feedback_receipt.get("feedback_message_count") == 1,
        f"feedback receipt did not enforce redaction: {task_id}",
    )
    outcome_path = Path(failing["private_outcome_path"])
    require(sha256(outcome_path) == failing.get("private_outcome_sha256"), f"private outcome hash mismatch: {task_id}")
    outcome = load(outcome_path)
    require(
        outcome.get("schema") == "charm-v1-private-repair-outcome-v1"
        and outcome.get("task_id") == task_id
        and outcome.get("candidate_sha256") == failing.get("files_sha256")
        and outcome.get("passed") is False,
        f"private failing outcome mismatch: {task_id}",
    )
    require(proof.get("private_test_output_disclosed") is False, f"repair proof leaks private output: {task_id}")
    return proof, proof_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-plan", required=True, type=Path)
    parser.add_argument("--materialization-receipt", required=True, type=Path)
    parser.add_argument("--oracle-summary", required=True, type=Path)
    parser.add_argument("--negative-summary", required=True, type=Path)
    parser.add_argument("--repair-summary", required=True, type=Path)
    parser.add_argument("--feedback-policy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite receipt collection: {args.output}")

    plan = load(args.generation_plan)
    materialization = load(args.materialization_receipt)
    oracle_summary = load(args.oracle_summary)
    negative_summary = load(args.negative_summary)
    repair_summary = load(args.repair_summary)
    require(oracle_summary.get("decision") == "PASS", "oracle summary did not pass")
    require(negative_summary.get("decision") == "PASS", "negative-control summary did not pass")
    require(repair_summary.get("decision") == "PASS", "repair-trajectory summary did not pass")
    feedback_policy_sha256 = sha256(args.feedback_policy)
    require(repair_summary.get("feedback_policy_sha256") == feedback_policy_sha256, "repair summary feedback policy hash mismatch")

    proposals = {item["task_id"]: item for item in plan["proposals"]}
    oracle_rows = {item["task_id"]: item for item in oracle_summary["tasks"]}
    negative_rows = {item["task_id"]: item for item in negative_summary["tasks"]}
    materialized = {item["task_id"]: item for item in materialization["tasks"]}
    repair_rows = {item["task_id"]: item for item in repair_summary["tasks"]}
    require(set(proposals) == set(oracle_rows) == set(negative_rows) == set(materialized), "plan, materialization, oracle, and negative-control IDs differ")
    expected_repairs = {task_id for task_id, item in proposals.items() if item["role"] == "repair_trajectory"}
    require(set(repair_rows) == expected_repairs and len(repair_rows) == 11, "repair proof IDs differ from the exact frozen repair set")

    receipts = []
    for task_id in sorted(proposals):
        proposal = proposals[task_id]
        item = materialized[task_id]
        root = Path(item["path"])
        require(tree_sha256(root) == item["tree_sha256"], f"canonical task tree drift: {task_id}")
        oracle_path = Path(oracle_rows[task_id]["proof_path"])
        negative_path = Path(negative_rows[task_id]["proof_path"])
        require(sha256(oracle_path) == oracle_rows[task_id]["proof_sha256"], f"oracle proof hash mismatch: {task_id}")
        require(sha256(negative_path) == negative_rows[task_id]["proof_sha256"], f"negative proof hash mismatch: {task_id}")
        oracle = load(oracle_path)
        negative = load(negative_path)
        runs = oracle["runs"]
        rules = {rule["rule_id"]: rule for rule in oracle["rules"]}
        all_checks = [run["checks"] for run in runs]
        role = proposal["role"]
        layout = proposal["editable_layout"]
        action = (
            "calibration_no_change" if role == "calibration"
            else "header_only_or_template" if layout == "header_only"
            else "source_only" if layout == "cpp_only"
            else "header_and_source"
        )
        headers = [name for name in proposal["editable_files"] if Path(name).suffix in {".h", ".hpp"}]
        existing_header_changed = any((root / name).read_bytes() != (root / ".reference" / name).read_bytes() for name in headers)
        target_passed = oracle["status"] == "certified" and all(run["reward"] == 1.0 for run in runs)
        receipt = {
            "task_id": task_id,
            "role": role,
            "action_topology": action,
            "starter_type": proposal["starter_type"],
            "header_mode": proposal["header_mode"],
            "editable_layout": layout,
            "multi_file_gt2": proposal["multi_file_gt2"],
            "api_capabilities": proposal["api_capabilities"],
            "repair_types": [] if proposal["repair_type"] is None else [proposal["repair_type"]],
            "requires_public_api_change": existing_header_changed,
            "existing_header_changed": existing_header_changed,
            "target_passed": target_passed,
            "weighted45": 1.0 if target_passed else 0.0,
            "starter_rejected": negative["starter_behavior_verified"] is True,
            "failure_mutation_rejected": negative["failure_mutation_rejected"] is True,
            "semantic_mutation_rejected": negative["semantic_mutation"] is not None,
            "protected_artifacts_unchanged": tree_sha256(root) == item["tree_sha256"],
            "api_probe_passed": all(checks.get("K2") is True for checks in all_checks),
            "header_isolation_passed": negative["header_isolation_passed"] is True,
            "strict_cpp17_werror_passed": all(all(run["checks"].get(name) is True for name in ("K1", "K2", "K3", "K4", "K5")) for run in runs if run["standard"] == "c++17"),
            "grader_determinism_passed": rules["ORC-015"]["passed"] is True,
            "grader_portability_passed": negative["grader_portability_passed"] is True,
            "sanitizer_passed": all(checks.get("A2") is True and checks.get("A4") is True for checks in all_checks),
            "anti_cheat_passed": all(all(checks.get(name) is True for name in ("F1", "F2", "F3", "F4", "F5")) for checks in all_checks),
            "dynamic_nonce_passed": all(checks.get("R5") is True for checks in all_checks),
            "application_replay_passed": rules["ORC-004"]["passed"] is True,
            "required_companion_files_complete": rules["ORC-002"]["passed"] is True,
            "private_test_output_disclosed": False,
            "oracle_receipt_sha256": sha256(oracle_path),
            "oracle_proof_path": str(oracle_path.resolve()),
            "negative_control_receipt_sha256": sha256(negative_path),
            "negative_control_proof_path": str(negative_path.resolve()),
            "task_tree_sha256": item["tree_sha256"],
        }
        if role == "repair_trajectory":
            repair_proof, repair_path = validate_repair(
                task_id=task_id,
                proposal=proposal,
                root=root,
                oracle_path=oracle_path,
                repair_row=repair_rows[task_id],
                feedback_policy_sha256=feedback_policy_sha256,
            )
            receipt.update({
                "genuine_four_turn_structure_passed": repair_proof["message_roles"] == ["user", "assistant", "user", "assistant"],
                "failing_candidate_receipt_bound": repair_proof["failing_candidate"]["reward"] != 1.0,
                "corrected_candidate_receipt_bound": repair_proof["corrected_candidate"]["oracle_certified"] is True,
                "feedback_policy_match_passed": repair_proof["public_feedback"]["policy_sha256"] == feedback_policy_sha256,
                "feedback_policy_sha256": feedback_policy_sha256,
                "repair_trajectory_receipt_path": str(repair_path.resolve()),
                "repair_trajectory_receipt_sha256": sha256(repair_path),
                "public_feedback_sha256": sha256_bytes(FAIL_MESSAGE.encode()),
            })
        if role == "calibration":
            receipt["task_type"] = "calibration"
            receipt["calibration_no_change_oracle_passed"] = negative["starter_matches_reference"] is True and negative["starter_reward"] == 1.0
        receipts.append(receipt)

    require(len(receipts) == 51, "task receipt collection is not exact-51")
    output = {
        "schema_version": "charm-v1-task-receipt-collection-v2",
        "decision": "PASS",
        "task_count": len(receipts),
        "generation_plan_sha256": sha256(args.generation_plan),
        "materialization_receipt_sha256": sha256(args.materialization_receipt),
        "oracle_summary_sha256": sha256(args.oracle_summary),
        "negative_summary_sha256": sha256(args.negative_summary),
        "repair_summary_sha256": sha256(args.repair_summary),
        "feedback_policy_sha256": feedback_policy_sha256,
        "task_receipts": receipts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(output))
    print(json.dumps({"decision": output["decision"], "task_count": len(receipts)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
