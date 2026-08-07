#!/usr/bin/env python3
"""Bind the four-topic 60-task proposal and uniqueness PASS into an ID plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


PROTOCOL_ID = "task-generation-four-topic-60-v1"
PLAN_SCHEMA = "charm-task-id-plan-v2"
PROPOSAL_SCHEMA = "charm-v1-proposal-plan-v1"
TOPICS = ("Clock", "Complex Numbers", "Spiral Matrix", "Zebra Puzzle")
SLOTS = {str(index) for index in range(1, 16)}
TASK_COUNT = len(TOPICS) * len(SLOTS)
ZERO_MATCH_FIELDS = (
    "parse_failures",
    "task_id_matches",
    "exact_matches",
    "near_matches",
    "structural_matches",
    "semantic_matches",
    "ambiguous_matches",
)


class PlanError(ValueError):
    """Raised when a frozen input cannot authorize task-ID claims."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlanError(f"{label} must be a JSON object")
    return value


def is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def build_plan(
    proposal_path: Path,
    uniqueness_path: Path,
    batch_receipt_path: Path,
) -> dict[str, Any]:
    proposal = load_json(proposal_path, "proposal plan")
    uniqueness = load_json(uniqueness_path, "uniqueness receipt")
    batch_receipt = load_json(batch_receipt_path, "batch-code receipt")
    proposal_sha256 = sha256(proposal_path)
    batch_receipt_sha256 = sha256(batch_receipt_path)

    proposals = proposal.get("proposals")
    if not (
        proposal.get("schema_version") == PROPOSAL_SCHEMA
        and proposal.get("protocol_id") == PROTOCOL_ID
        and proposal.get("authorized_task_count") == TASK_COUNT
        and proposal.get("topics") == list(TOPICS)
        and proposal.get("tasks_per_topic") == 15
        and isinstance(proposals, list)
        and len(proposals) == TASK_COUNT
    ):
        raise PlanError("proposal plan does not have the frozen four-topic 60-task shape")

    slots_by_topic: dict[str, set[str]] = {}
    task_ids: set[str] = set()
    claims: list[dict[str, str]] = []
    for index, item in enumerate(proposals):
        if not isinstance(item, dict):
            raise PlanError(f"proposal {index} must be an object")
        task_id = item.get("task_id")
        topic = item.get("topic")
        slot_id = item.get("slot_id")
        proposal_digest = item.get("proposal_sha256")
        if (
            not isinstance(task_id, str)
            or not task_id.startswith("charm-ft60-")
            or task_id in task_ids
            or topic not in TOPICS
            or slot_id not in SLOTS
            or not is_sha256(proposal_digest)
        ):
            raise PlanError(f"invalid or duplicate proposal identity at index {index}")
        task_ids.add(task_id)
        slots_by_topic.setdefault(topic, set()).add(slot_id)
        claims.append(
            {
                "task_id": task_id,
                "topic": topic,
                "slot_id": slot_id,
                "proposal_sha256": proposal_digest,
            }
        )
    if slots_by_topic != {topic: SLOTS for topic in TOPICS}:
        raise PlanError("proposal plan must cover slots 1 through 15 for every topic")

    if not (
        uniqueness.get("decision") == "PASS"
        and uniqueness.get("repository_scope_complete") is True
        and uniqueness.get("proposal_plan_sha256") == proposal_sha256
        and uniqueness.get("proposal_count") == TASK_COUNT
        and uniqueness.get("generated_query_count") == 0
        and uniqueness.get("generated_component_count") == 0
        and all(uniqueness.get(field) == 0 for field in ZERO_MATCH_FIELDS)
        and is_sha256(uniqueness.get("corpus_index_sha256"))
    ):
        raise PlanError("uniqueness receipt is not a complete zero-match PASS for this plan")

    if not (
        batch_receipt.get("schema_version")
        == "charm-batch-code-reservation-receipt-v1"
        and batch_receipt.get("decision") == "PASS"
        and batch_receipt.get("operation") == "reserve_batch_code"
        and batch_receipt.get("reservation_state") == "permanent"
        and batch_receipt.get("atomic_lock_acquired") is True
        and batch_receipt.get("registry_reconciled") is True
        and batch_receipt.get("generation_batch_id")
        == proposal.get("generation_batch_id")
        and batch_receipt.get("generation_session_id")
        == proposal.get("generation_session_id")
        and batch_receipt.get("generation_batch_code")
        == proposal.get("generation_batch_code")
        and batch_receipt.get("historical_alias_only") is False
        and batch_receipt.get("codes_reusable") is False
        and proposal.get("batch_code_reservation_receipt_sha256")
        == batch_receipt_sha256
    ):
        raise PlanError("batch-code receipt is not the permanent reservation bound by the plan")

    return {
        "schema_version": PLAN_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "generation_batch_id": proposal["generation_batch_id"],
        "generation_session_id": proposal["generation_session_id"],
        "generation_batch_created_at_utc": proposal["generation_batch_created_at_utc"],
        "generation_batch_code": proposal["generation_batch_code"],
        "batch_code_reservation_receipt_sha256": batch_receipt_sha256,
        "proposal_plan_sha256": proposal_sha256,
        "corpus_index_sha256": uniqueness["corpus_index_sha256"],
        "claims": claims,
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise PlanError(f"refusing to overwrite reservation plan: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--uniqueness-receipt", required=True, type=Path)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        plan = build_plan(
            args.proposal_plan,
            args.uniqueness_receipt,
            args.batch_code_receipt,
        )
        write_new(args.output, plan)
    except PlanError as exc:
        parser.error(str(exc))
    print(sha256(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
