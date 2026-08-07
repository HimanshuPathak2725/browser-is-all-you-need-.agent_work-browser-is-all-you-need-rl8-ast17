#!/usr/bin/env python3
"""Export the expanded CHARM V1 task-level certification score CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


PROOF_COLUMNS = (
    "target_passed", "starter_rejected", "failure_mutation_rejected",
    "semantic_mutation_rejected", "protected_artifacts_unchanged",
    "api_probe_passed", "header_isolation_passed", "strict_cpp17_werror_passed",
    "grader_determinism_passed", "grader_portability_passed", "sanitizer_passed",
    "anti_cheat_passed", "dynamic_nonce_passed", "application_replay_passed",
    "required_companion_files_complete",
)


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-plan", required=True, type=Path)
    parser.add_argument("--task-receipts", required=True, type=Path)
    parser.add_argument("--post-generation-admission", required=True, type=Path)
    parser.add_argument("--post-generation-uniqueness", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite score CSV: {args.output}")
    plan = load(args.generation_plan)
    collection = load(args.task_receipts)
    admission = load(args.post_generation_admission)
    uniqueness = load(args.post_generation_uniqueness)
    proposals = {item["task_id"]: item for item in plan["proposals"]}
    receipts = {item["task_id"]: item for item in collection["task_receipts"]}
    if set(proposals) != set(receipts) or len(receipts) != 51:
        raise RuntimeError("score inputs do not contain the exact frozen 51-task set")
    admission_passed = admission.get("decision") == "PASS"
    uniqueness_passed = uniqueness.get("decision") == "PASS"
    fieldnames = [
        "task_id", "topic", "slot_id", "role", "starter_type", "header_mode",
        "editable_layout", "action_topology", "weighted45", *PROOF_COLUMNS,
        "post_generation_uniqueness_passed", "post_generation_v4_1_passed",
        "critical_checks_passed", "critical_checks_total", "final_task_score",
        "claim_status", "sft_ready",
        "task_tree_sha256", "oracle_receipt_sha256", "negative_control_receipt_sha256",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for task_id in sorted(receipts):
            receipt = receipts[task_id]
            proposal = proposals[task_id]
            proof_passes = sum(receipt.get(field) is True for field in PROOF_COLUMNS)
            total = len(PROOF_COLUMNS) + 2
            passed = proof_passes + int(uniqueness_passed) + int(admission_passed)
            score = round(100.0 * passed / total, 4)
            writer.writerow({
                "task_id": task_id,
                "topic": proposal["topic"],
                "slot_id": proposal["slot_id"],
                "role": receipt["role"],
                "starter_type": receipt["starter_type"],
                "header_mode": receipt["header_mode"],
                "editable_layout": receipt["editable_layout"],
                "action_topology": receipt["action_topology"],
                "weighted45": receipt["weighted45"],
                **{field: receipt.get(field) for field in PROOF_COLUMNS},
                "post_generation_uniqueness_passed": uniqueness_passed,
                "post_generation_v4_1_passed": admission_passed,
                "critical_checks_passed": passed,
                "critical_checks_total": total,
                "final_task_score": score,
                "claim_status": "generated_task_v4_verified" if score == 100.0 else "candidate_generated",
                # Consumer-ready requires independent audit, official projection,
                # Baseline 3, V2, pre-training admission, and consumer replay.
                "sft_ready": False,
                "task_tree_sha256": receipt["task_tree_sha256"],
                "oracle_receipt_sha256": receipt["oracle_receipt_sha256"],
                "negative_control_receipt_sha256": receipt["negative_control_receipt_sha256"],
            })
    print(json.dumps({"rows": len(receipts), "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
