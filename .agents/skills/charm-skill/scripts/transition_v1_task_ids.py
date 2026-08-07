#!/usr/bin/env python3
"""Atomically transition one exact 51-ID CHARM V1 reservation session."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ALLOWED = {
    ("reserved", "materialized"),
    ("materialized", "verified"),
    ("verified", "admitted"),
    ("admitted", "released"),
    ("reserved", "rejected_tombstone"),
    ("materialized", "rejected_tombstone"),
    ("verified", "rejected_tombstone"),
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def transition(
    *,
    registry_path: Path,
    plan_path: Path,
    from_state: str,
    to_state: str,
    evidence_path: Path,
) -> dict[str, Any]:
    if (from_state, to_state) not in ALLOWED:
        raise ValueError(f"unsupported lifecycle transition: {from_state}->{to_state}")
    plan = load(plan_path)
    claims = plan.get("claims")
    if (
        plan.get("schema_version") != "charm-task-id-plan-v2"
        or not isinstance(plan.get("generation_batch_code"), str)
        or len(plan["generation_batch_code"]) != 5
        or not plan["generation_batch_code"].isdigit()
        or not isinstance(plan.get("generation_batch_created_at_utc"), str)
        or not isinstance(plan.get("batch_code_reservation_receipt_sha256"), str)
        or len(plan["batch_code_reservation_receipt_sha256"]) != 64
        or not isinstance(claims, list)
        or len(claims) != 51
    ):
        raise ValueError("transition requires the exact 51-claim V1 reservation plan")
    evidence = load(evidence_path)
    if evidence.get("decision") != "PASS":
        raise ValueError("lifecycle transition evidence must be a passing receipt")
    task_ids = sorted(str(claim["task_id"]) for claim in claims)
    if len(set(task_ids)) != 51:
        raise ValueError("reservation plan task IDs are incomplete or duplicated")

    lock_path = registry_path.with_name(f"{registry_path.name}.lock")
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        registry = load(registry_path)
        if registry.get("schema_version") != "charm-task-id-reservation-registry-v1":
            raise ValueError("unsupported reservation registry")
        before = registry_path.read_bytes()
        updated = copy.deepcopy(registry)
        entries = updated.get("entries")
        if not isinstance(entries, dict):
            raise ValueError("reservation registry entries are invalid")
        transitioned: list[str] = []
        resumed: list[str] = []
        evidence_sha = sha256(evidence_path)
        for claim in claims:
            task_id = str(claim["task_id"])
            entry = entries.get(task_id)
            if (
                not isinstance(entry, dict)
                or entry.get("protocol_id") != plan.get("protocol_id")
                or entry.get("generation_batch_id") != plan.get("generation_batch_id")
                or entry.get("generation_session_id") != plan.get("generation_session_id")
                or entry.get("generation_batch_code") != plan.get("generation_batch_code")
                or entry.get("generation_batch_created_at_utc")
                != plan.get("generation_batch_created_at_utc")
                or entry.get("batch_code_reservation_receipt_sha256")
                != plan.get("batch_code_reservation_receipt_sha256")
                or entry.get("topic") != claim.get("topic")
                or entry.get("slot_id") != claim.get("slot_id")
                or entry.get("proposal_sha256") != claim.get("proposal_sha256")
            ):
                raise ValueError(f"reservation ownership/lineage mismatch: {task_id}")
            state = entry.get("state")
            if state == to_state:
                history = entry.get("transition_history", [])
                if not any(
                    item.get("from") == from_state
                    and item.get("to") == to_state
                    and item.get("evidence_sha256") == evidence_sha
                    for item in history
                    if isinstance(item, dict)
                ):
                    raise ValueError(f"same-state resume lacks matching evidence: {task_id}")
                resumed.append(task_id)
                continue
            if state != from_state:
                raise ValueError(
                    f"reservation state mismatch for {task_id}: expected {from_state}, got {state}"
                )
            entry["state"] = to_state
            history = entry.setdefault("transition_history", [])
            if not isinstance(history, list):
                raise ValueError(f"reservation transition history is invalid: {task_id}")
            history.append({
                "from": from_state,
                "to": to_state,
                "evidence_path": str(evidence_path.resolve()),
                "evidence_sha256": evidence_sha,
            })
            transitioned.append(task_id)
        if transitioned:
            updated["revision"] = int(updated["revision"]) + 1
            after = canonical(updated)
            atomic_write(registry_path, after)
        else:
            after = before
    return {
        "schema_version": "charm-task-id-transition-receipt-v1",
        "decision": "PASS",
        "protocol_id": plan["protocol_id"],
        "generation_batch_id": plan["generation_batch_id"],
        "generation_session_id": plan["generation_session_id"],
        "generation_batch_code": plan["generation_batch_code"],
        "generation_batch_created_at_utc": plan["generation_batch_created_at_utc"],
        "batch_code_reservation_receipt_sha256": plan[
            "batch_code_reservation_receipt_sha256"
        ],
        "from_state": from_state,
        "to_state": to_state,
        "task_count": len(task_ids),
        "transitioned_task_ids": transitioned,
        "resumed_task_ids": resumed,
        "evidence_path": str(evidence_path.resolve()),
        "evidence_sha256": sha256(evidence_path),
        "registry_before_sha256": hashlib.sha256(before).hexdigest(),
        "registry_after_sha256": hashlib.sha256(after).hexdigest(),
        "registry_revision": updated["revision"],
        "atomic_lock_acquired": True,
        "all_claims_owner_bound": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--from-state", required=True)
    parser.add_argument("--to-state", required=True)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite transition receipt: {args.output}")
    result = transition(
        registry_path=args.registry,
        plan_path=args.plan,
        from_state=args.from_state,
        to_state=args.to_state,
        evidence_path=args.evidence,
    )
    atomic_write(args.output, canonical(result))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
