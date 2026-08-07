#!/usr/bin/env python3
"""Atomically reserve CHARM V1 task IDs before task materialization.

The repository-wide uniqueness scan proves that a frozen proposal was clear at
scan time. This utility closes the subsequent read-then-write race between V1
generation sessions by serializing claims through one append-only registry.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


PLAN_SCHEMA = "charm-task-id-plan-v2"
REGISTRY_SCHEMA = "charm-task-id-reservation-registry-v1"
RECEIPT_SCHEMA = "charm-task-id-reservation-receipt-v2"
BATCH_CODE_RECEIPT_SCHEMA = "charm-batch-code-reservation-receipt-v1"
BATCH_CODE_DERIVATION = "unix-seconds-mod-100000-linear-probe-v1"
V1_TOPICS = (
    "Allergies",
    "Bank Account",
    "Binary Search Tree",
    "Circular Buffer",
    "Clock",
    "Complex Numbers",
    "Crypto Square",
    "Diamond",
    "Grade School",
    "Kindergarten Garden",
    "Linked List",
    "Parallel Letter Frequency",
    "Phone Number",
    "Spiral Matrix",
    "Sublist",
    "Yacht",
    "Zebra Puzzle",
)
V1_SLOT_IDS = {"1", "2", "3"}
V1_TASK_COUNT = len(V1_TOPICS) * len(V1_SLOT_IDS)
V1_COMPONENTS_PER_QUERY = 12
ZERO_MATCH_FIELDS = (
    "parse_failures",
    "task_id_matches",
    "exact_matches",
    "near_matches",
    "structural_matches",
    "semantic_matches",
    "ambiguous_matches",
)
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BATCH_CODE_RE = re.compile(r"^[0-9]{5}$")
RESERVATION_STATES = {
    "reserved",
    "materialized",
    "verified",
    "admitted",
    "released",
    "rejected_tombstone",
    "abandoned_tombstone",
}


class ReservationError(ValueError):
    """Raised when a reservation input or claim fails closed."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReservationError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReservationError(f"{label} must be a JSON object: {path}")
    return value


def _require_token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ReservationError(f"{label} must match {TOKEN_RE.pattern}")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ReservationError(f"{label} must be a lowercase SHA-256")
    return value


def _validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ReservationError(f"plan schema_version must be {PLAN_SCHEMA}")
    protocol_id = _require_token(plan.get("protocol_id"), "protocol_id")
    batch_id = _require_token(plan.get("generation_batch_id"), "generation_batch_id")
    session_id = _require_token(plan.get("generation_session_id"), "generation_session_id")
    batch_code = plan.get("generation_batch_code")
    if not isinstance(batch_code, str) or not BATCH_CODE_RE.fullmatch(batch_code):
        raise ReservationError("generation_batch_code must be exactly five decimal digits")
    batch_created_at = plan.get("generation_batch_created_at_utc")
    if not isinstance(batch_created_at, str) or not batch_created_at:
        raise ReservationError("generation_batch_created_at_utc must be present")
    batch_code_receipt_sha256 = _require_sha256(
        plan.get("batch_code_reservation_receipt_sha256"),
        "batch_code_reservation_receipt_sha256",
    )
    _require_sha256(plan.get("proposal_plan_sha256"), "proposal_plan_sha256")
    _require_sha256(plan.get("corpus_index_sha256"), "corpus_index_sha256")
    raw_claims = plan.get("claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise ReservationError("claims must be a non-empty list")

    claims: list[dict[str, Any]] = []
    task_ids: set[str] = set()
    slot_keys: set[str] = set()
    for index, raw in enumerate(raw_claims):
        if not isinstance(raw, dict):
            raise ReservationError(f"claims[{index}] must be an object")
        task_id = _require_token(raw.get("task_id"), f"claims[{index}].task_id")
        topic = raw.get("topic")
        if (
            not isinstance(topic, str)
            or not topic.strip()
            or len(topic) > 128
            or "|" in topic
        ):
            raise ReservationError(f"claims[{index}].topic is invalid")
        slot_id = _require_token(raw.get("slot_id"), f"claims[{index}].slot_id")
        proposal_sha256 = _require_sha256(
            raw.get("proposal_sha256"), f"claims[{index}].proposal_sha256"
        )
        slot_key = f"{batch_id}|{topic.strip()}|{slot_id}"
        if task_id in task_ids:
            raise ReservationError(f"duplicate task_id inside plan: {task_id}")
        if slot_key in slot_keys:
            raise ReservationError(f"duplicate topic slot inside plan: {slot_key}")
        task_ids.add(task_id)
        slot_keys.add(slot_key)
        claims.append(
            {
                "task_id": task_id,
                "topic": topic.strip(),
                "slot_id": slot_id,
                "slot_key": slot_key,
                "proposal_sha256": proposal_sha256,
                "protocol_id": protocol_id,
                "generation_batch_id": batch_id,
                "generation_session_id": session_id,
                "generation_batch_code": batch_code,
                "generation_batch_created_at_utc": batch_created_at,
                "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
            }
        )
    if protocol_id == "task-generation-v1":
        _require_sha256(
            plan.get("materialization_manifest_sha256"),
            "materialization_manifest_sha256",
        )
        slots_by_topic: dict[str, set[str]] = {}
        for claim in claims:
            slots_by_topic.setdefault(claim["topic"], set()).add(claim["slot_id"])
        v1_shape_valid = (
            len(claims) == V1_TASK_COUNT
            and set(slots_by_topic) == set(V1_TOPICS)
            and all(slots == V1_SLOT_IDS for slots in slots_by_topic.values())
        )
        if not v1_shape_valid:
            raise ReservationError(
                "task-generation-v1 requires exactly the frozen 17 topics with "
                "slots 1, 2, and 3 (51 claims)"
            )
    return claims


def _validate_batch_code_receipt(path: Path, plan: dict[str, Any]) -> str:
    receipt = _load_json(path, "batch-code reservation receipt")
    receipt_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if receipt_sha256 != plan.get("batch_code_reservation_receipt_sha256"):
        raise ReservationError("plan does not bind the supplied batch-code receipt")
    if not (
        receipt.get("schema_version") == BATCH_CODE_RECEIPT_SCHEMA
        and receipt.get("decision") == "PASS"
        and receipt.get("operation") == "reserve_batch_code"
        and receipt.get("atomic_lock_acquired") is True
        and receipt.get("registry_reconciled") is True
        and receipt.get("reservation_state") == "permanent"
        and receipt.get("generation_batch_id") == plan.get("generation_batch_id")
        and receipt.get("generation_session_id") == plan.get("generation_session_id")
        and receipt.get("generation_batch_created_at_utc")
        == plan.get("generation_batch_created_at_utc")
        and receipt.get("generation_batch_code") == plan.get("generation_batch_code")
        and receipt.get("batch_code_derivation") == BATCH_CODE_DERIVATION
        and receipt.get("historical_alias_only") is False
        and receipt.get("codes_reusable") is False
    ):
        raise ReservationError(
            "batch-code receipt must be a permanent, current-generation reservation "
            "owned by this batch and session"
        )
    return receipt_sha256


def _validate_uniqueness_receipt(
    path: Path, plan: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    receipt = _load_json(path, "uniqueness receipt")
    failures = [field for field in ZERO_MATCH_FIELDS if receipt.get(field) != 0]
    if (
        receipt.get("decision") != "PASS"
        or receipt.get("repository_scope_complete") is not True
        or failures
    ):
        raise ReservationError(
            "uniqueness receipt must PASS a complete scan with every match count at zero"
        )
    if receipt.get("proposal_plan_sha256") != plan.get("proposal_plan_sha256"):
        raise ReservationError("uniqueness receipt does not bind this proposal plan")
    if receipt.get("corpus_index_sha256") != plan.get("corpus_index_sha256"):
        raise ReservationError("uniqueness receipt corpus index does not match the plan")
    if plan.get("protocol_id") == "task-generation-v1" and not (
        receipt.get("proposal_count") == V1_TASK_COUNT
        and receipt.get("generated_query_count") == V1_TASK_COUNT
        and receipt.get("generated_component_count")
        == V1_TASK_COUNT * V1_COMPONENTS_PER_QUERY
        and receipt.get("materialization_manifest_sha256")
        == plan.get("materialization_manifest_sha256")
    ):
        raise ReservationError(
            "task-generation-v1 uniqueness must bind exactly 51 generated "
            "package queries with 12 components each"
        )
    return receipt, hashlib.sha256(path.read_bytes()).hexdigest()


def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": REGISTRY_SCHEMA,
        "revision": 0,
        "entries": {},
        "slot_claims": {},
    }


def _validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise ReservationError(f"registry schema_version must be {REGISTRY_SCHEMA}")
    if (
        not isinstance(registry.get("revision"), int)
        or isinstance(registry["revision"], bool)
        or registry["revision"] < 0
    ):
        raise ReservationError("registry revision must be a non-negative integer")
    entries = registry.get("entries")
    slot_claims = registry.get("slot_claims")
    if not isinstance(entries, dict):
        raise ReservationError("registry entries must be an object")
    if not isinstance(slot_claims, dict):
        raise ReservationError("registry slot_claims must be an object")
    expected_slot_claims: dict[str, str] = {}
    batch_code_owners: dict[str, str] = {}
    for task_id, entry in entries.items():
        _require_token(task_id, "registry task_id")
        if not isinstance(entry, dict) or entry.get("task_id") != task_id:
            raise ReservationError(f"registry entry identity mismatch: {task_id}")
        batch_id = _require_token(
            entry.get("generation_batch_id"), f"registry[{task_id}].generation_batch_id"
        )
        _require_token(entry.get("protocol_id"), f"registry[{task_id}].protocol_id")
        _require_token(
            entry.get("generation_session_id"),
            f"registry[{task_id}].generation_session_id",
        )
        slot_id = _require_token(entry.get("slot_id"), f"registry[{task_id}].slot_id")
        topic = entry.get("topic")
        if not isinstance(topic, str) or not topic.strip() or "|" in topic:
            raise ReservationError(f"registry[{task_id}].topic is invalid")
        _require_sha256(
            entry.get("proposal_sha256"), f"registry[{task_id}].proposal_sha256"
        )
        batch_identity_fields = (
            entry.get("generation_batch_code"),
            entry.get("generation_batch_created_at_utc"),
            entry.get("batch_code_reservation_receipt_sha256"),
        )
        if any(value is not None for value in batch_identity_fields):
            batch_code, batch_created_at, batch_receipt_sha256 = batch_identity_fields
            if not isinstance(batch_code, str) or not BATCH_CODE_RE.fullmatch(batch_code):
                raise ReservationError(f"registry[{task_id}].generation_batch_code is invalid")
            if not isinstance(batch_created_at, str) or not batch_created_at:
                raise ReservationError(
                    f"registry[{task_id}].generation_batch_created_at_utc is invalid"
                )
            _require_sha256(
                batch_receipt_sha256,
                f"registry[{task_id}].batch_code_reservation_receipt_sha256",
            )
            owner = batch_code_owners.setdefault(batch_code, batch_id)
            if owner != batch_id:
                raise ReservationError(
                    f"generation batch code {batch_code} is claimed by multiple batches"
                )
        expected_slot_key = f"{batch_id}|{topic.strip()}|{slot_id}"
        if entry.get("slot_key") != expected_slot_key:
            raise ReservationError(f"registry[{task_id}].slot_key is inconsistent")
        if entry.get("state") not in RESERVATION_STATES:
            raise ReservationError(f"registry[{task_id}].state is invalid")
        if expected_slot_key in expected_slot_claims:
            raise ReservationError(f"duplicate registry slot claim: {expected_slot_key}")
        expected_slot_claims[expected_slot_key] = task_id
    if slot_claims != expected_slot_claims:
        raise ReservationError("registry entries and slot_claims are not one-to-one")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def reserve(
    registry_path: Path,
    plan_path: Path,
    uniqueness_receipt_path: Path,
    batch_code_receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = _load_json(plan_path, "reservation plan")
    claims = _validate_plan(plan)
    batch_code_receipt_sha256 = _validate_batch_code_receipt(batch_code_receipt_path, plan)
    _, uniqueness_sha256 = _validate_uniqueness_receipt(uniqueness_receipt_path, plan)
    plan_sha256 = hashlib.sha256(plan_path.read_bytes()).hexdigest()

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = registry_path.with_name(f"{registry_path.name}.lock")
    with lock_path.open("a+b") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        if registry_path.exists():
            registry = _load_json(registry_path, "reservation registry")
            before_bytes = registry_path.read_bytes()
        else:
            registry = _empty_registry()
            before_bytes = _canonical_bytes(registry)
        _validate_registry(registry)
        for registered_entry in registry["entries"].values():
            if (
                registered_entry.get("generation_batch_code")
                == plan["generation_batch_code"]
                and registered_entry.get("generation_batch_id")
                != plan["generation_batch_id"]
            ):
                raise ReservationError("generation_batch_code is owned by another batch")
        updated = copy.deepcopy(registry)
        entries = updated["entries"]
        slot_claims = updated["slot_claims"]
        collisions: list[str] = []
        created: list[str] = []
        resumed: list[str] = []

        for claim in claims:
            task_id = claim["task_id"]
            slot_key = claim["slot_key"]
            existing = entries.get(task_id)
            slot_owner = slot_claims.get(slot_key)
            expected_entry = {**claim, "state": "reserved"}
            if existing is not None:
                if existing == expected_entry and slot_owner == task_id:
                    resumed.append(task_id)
                else:
                    collisions.append(f"task_id already claimed or registered: {task_id}")
                continue
            if slot_owner is not None:
                collisions.append(f"V1 topic slot already owned by {slot_owner}: {slot_key}")
                continue
            entries[task_id] = expected_entry
            slot_claims[slot_key] = task_id
            created.append(task_id)

        if collisions:
            raise ReservationError("; ".join(sorted(collisions)))
        if created:
            updated["revision"] += 1
            after_bytes = _canonical_bytes(updated)
            _atomic_write(registry_path, after_bytes)
        else:
            after_bytes = before_bytes

        receipt = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "PASS",
            "operation": "reserve",
            "reservation_state": "reserved",
            "atomic_lock_acquired": True,
            "registry_reconciled": True,
            "collision_count": 0,
            "protocol_id": plan["protocol_id"],
            "generation_batch_id": plan["generation_batch_id"],
            "generation_session_id": plan["generation_session_id"],
            "generation_batch_code": plan["generation_batch_code"],
            "generation_batch_created_at_utc": plan["generation_batch_created_at_utc"],
            "batch_code_reservation_receipt_sha256": batch_code_receipt_sha256,
            "proposal_plan_sha256": plan["proposal_plan_sha256"],
            "corpus_index_sha256": plan["corpus_index_sha256"],
            "reservation_plan_sha256": plan_sha256,
            "uniqueness_receipt_sha256": uniqueness_sha256,
            "registry_before_sha256": _sha256_bytes(before_bytes),
            "registry_after_sha256": _sha256_bytes(after_bytes),
            "registry_revision": updated["revision"],
            "claim_count": len(claims),
            "created_task_ids": sorted(created),
            "resumed_task_ids": sorted(resumed),
            "reserved_task_ids": sorted(claim["task_id"] for claim in claims),
            "slot_keys": sorted(claim["slot_key"] for claim in claims),
            "idempotent_resume_only_for_same_owner_and_proposal": True,
            "terminal_or_tombstoned_ids_reusable": False,
        }
        return updated, receipt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--uniqueness-receipt", required=True, type=Path)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite reservation receipt: {args.output}", file=sys.stderr)
        return 2
    try:
        _, receipt = reserve(
            args.registry,
            args.plan,
            args.uniqueness_receipt,
            args.batch_code_receipt,
        )
    except ReservationError as exc:
        failure = {
            "schema_version": RECEIPT_SCHEMA,
            "decision": "FAIL",
            "operation": "reserve",
            "errors": [str(exc)],
        }
        _atomic_write(args.output, _canonical_bytes(failure))
        print(str(exc), file=sys.stderr)
        return 1
    _atomic_write(args.output, _canonical_bytes(receipt))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
