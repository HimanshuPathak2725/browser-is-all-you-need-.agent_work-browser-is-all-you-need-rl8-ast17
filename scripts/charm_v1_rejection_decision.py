#!/usr/bin/env python3
"""Issue a digest-bound PASS decision to tombstone one failed CHARM V1 batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


SCHEMA = "charm-v1-batch-rejection-decision-v1"
PLAN_SCHEMA = "charm-task-id-plan-v2"
IDENTITY_FIELDS = (
    "generation_batch_id",
    "generation_session_id",
    "generation_batch_code",
    "generation_batch_created_at_utc",
    "batch_code_reservation_receipt_sha256",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_matches(candidate: dict[str, Any], plan: dict[str, Any]) -> bool:
    return all(candidate.get(field) == plan.get(field) for field in IDENTITY_FIELDS)


def failure_binding(path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    receipt = load(path)
    failed_rules = sorted(
        str(row.get("rule_id"))
        for row in receipt.get("rules", [])
        if isinstance(row, dict) and row.get("passed") is False
    )
    hard_failures = sorted(str(value) for value in receipt.get("hard_failure_ids", []))
    if receipt.get("decision") not in {"FAIL", "not_completed"}:
        raise ValueError(f"rejection evidence is not a failing receipt: {path}")
    if not hard_failures and not failed_rules:
        raise ValueError(f"rejection evidence has no deterministic hard failure: {path}")

    direct_identity = (
        receipt.get("generation_batch_id") == plan.get("generation_batch_id")
        and receipt.get("generation_session_id") == plan.get("generation_session_id")
    )
    subject_path_value = receipt.get("subject_path")
    subject_binding: dict[str, str] | None = None
    subject_identity = False
    if isinstance(subject_path_value, str) and subject_path_value:
        subject_path = Path(subject_path_value)
        if not subject_path.is_absolute():
            subject_path = (Path.cwd() / subject_path).resolve()
        if not subject_path.is_file() or sha256(subject_path) != receipt.get("subject_sha256"):
            raise ValueError(f"rejection evidence subject binding drifted: {path}")
        subject = load(subject_path)
        reservation_plan = subject.get("task_id_reservation_plan")
        subject_identity = isinstance(reservation_plan, dict) and identity_matches(
            reservation_plan, plan
        )
        subject_binding = {"path": str(subject_path), "sha256": sha256(subject_path)}
    if not (direct_identity or subject_identity):
        raise ValueError(f"rejection evidence does not bind the exact batch: {path}")
    return {
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "decision": receipt.get("decision"),
        "hard_failure_ids": hard_failures,
        "failed_rule_ids": failed_rules,
        "subject": subject_binding,
    }


def decide(plan_path: Path, evidence_paths: list[Path]) -> dict[str, Any]:
    plan = load(plan_path)
    claims = plan.get("claims")
    code = plan.get("generation_batch_code")
    receipt_sha = plan.get("batch_code_reservation_receipt_sha256")
    if not (
        plan.get("schema_version") == PLAN_SCHEMA
        and plan.get("protocol_id") == "task-generation-v1"
        and isinstance(code, str)
        and len(code) == 5
        and code.isdigit()
        and isinstance(receipt_sha, str)
        and len(receipt_sha) == 64
        and isinstance(claims, list)
        and len(claims) == 51
        and len({row.get("task_id") for row in claims if isinstance(row, dict)}) == 51
        and evidence_paths
    ):
        raise ValueError("rejection requires one exact 51-claim V1 reservation plan")
    bindings = [failure_binding(path, plan) for path in evidence_paths]
    return {
        "schema_version": SCHEMA,
        "decision": "PASS",
        "action": "transition_to_rejected_tombstone",
        "protocol_id": "task-generation-v1",
        **{field: plan[field] for field in IDENTITY_FIELDS},
        "task_count": 51,
        "task_ids": sorted(str(row["task_id"]) for row in claims),
        "reservation_plan": {"path": str(plan_path.resolve()), "sha256": sha256(plan_path)},
        "failure_evidence": bindings,
        "failure_evidence_count": len(bindings),
        "all_failure_evidence_batch_bound": True,
        "reservation_claims_remain_permanent": True,
        "terminal_ids_reusable": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--failure-evidence", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite rejection decision: {args.output}")
    result = decide(args.plan, args.failure_evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical(result))
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"decision": "PASS", "action": result["action"], "task_count": 51}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
