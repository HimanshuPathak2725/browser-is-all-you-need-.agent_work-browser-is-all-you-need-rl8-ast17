#!/usr/bin/env python3
"""Bind a zero-match V1 proposal receipt into the atomic 51-ID plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


V1_TOPICS = (
    "Allergies", "Bank Account", "Binary Search Tree", "Circular Buffer", "Clock",
    "Complex Numbers", "Crypto Square", "Diamond", "Grade School",
    "Kindergarten Garden", "Linked List", "Parallel Letter Frequency",
    "Phone Number", "Spiral Matrix", "Sublist", "Yacht", "Zebra Puzzle",
)
V1_TASK_COUNT = len(V1_TOPICS) * 3
V1_COMPONENTS_PER_QUERY = 12


def is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-plan", required=True, type=Path)
    parser.add_argument("--uniqueness-receipt", required=True, type=Path)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite reservation plan: {args.output}")
    proposal = json.loads(args.proposal_plan.read_text(encoding="utf-8"))
    uniqueness = json.loads(args.uniqueness_receipt.read_text(encoding="utf-8"))
    batch_receipt = json.loads(args.batch_code_receipt.read_text(encoding="utf-8"))
    batch_receipt_sha = hashlib.sha256(args.batch_code_receipt.read_bytes()).hexdigest()
    proposal_sha = hashlib.sha256(args.proposal_plan.read_bytes()).hexdigest()
    zero_fields = (
        "parse_failures", "task_id_matches", "exact_matches", "near_matches",
        "structural_matches", "semantic_matches", "ambiguous_matches",
    )
    if not (
        uniqueness.get("decision") == "PASS"
        and uniqueness.get("repository_scope_complete") is True
        and uniqueness.get("proposal_plan_sha256") == proposal_sha
        and uniqueness.get("proposal_count") == V1_TASK_COUNT
        and uniqueness.get("generated_query_count") == V1_TASK_COUNT
        and uniqueness.get("generated_component_count")
        == V1_TASK_COUNT * V1_COMPONENTS_PER_QUERY
        and is_sha256(uniqueness.get("materialization_manifest_sha256"))
        and all(uniqueness.get(field) == 0 for field in zero_fields)
    ):
        raise SystemExit("uniqueness receipt is not a complete zero-match PASS for this plan")
    if not (
        batch_receipt.get("schema_version") == "charm-batch-code-reservation-receipt-v1"
        and batch_receipt.get("decision") == "PASS"
        and batch_receipt.get("operation") == "reserve_batch_code"
        and batch_receipt.get("reservation_state") == "permanent"
        and batch_receipt.get("generation_batch_id") == proposal.get("generation_batch_id")
        and batch_receipt.get("generation_session_id") == proposal.get("generation_session_id")
        and batch_receipt.get("historical_alias_only") is False
        and batch_receipt.get("codes_reusable") is False
        and isinstance(batch_receipt.get("generation_batch_code"), str)
        and len(batch_receipt["generation_batch_code"]) == 5
        and batch_receipt["generation_batch_code"].isdigit()
    ):
        raise SystemExit("batch-code receipt is not a permanent reservation for this plan")
    proposals = proposal.get("proposals")
    if not isinstance(proposals, list) or len(proposals) != 51:
        raise SystemExit("proposal plan must contain exactly 51 tasks")
    slots = {(item.get("topic"), item.get("slot_id")) for item in proposals if isinstance(item, dict)}
    if slots != {(topic, str(slot)) for topic in V1_TOPICS for slot in (1, 2, 3)}:
        raise SystemExit("proposal plan does not cover the exact V1 topic slots")
    plan = {
        "schema_version": "charm-task-id-plan-v2",
        "protocol_id": "task-generation-v1",
        "generation_batch_id": proposal["generation_batch_id"],
        "generation_session_id": proposal["generation_session_id"],
        "generation_batch_created_at_utc": batch_receipt["generation_batch_created_at_utc"],
        "generation_batch_code": batch_receipt["generation_batch_code"],
        "batch_code_reservation_receipt_sha256": batch_receipt_sha,
        "proposal_plan_sha256": proposal_sha,
        "materialization_manifest_sha256": uniqueness[
            "materialization_manifest_sha256"
        ],
        "corpus_index_sha256": uniqueness["corpus_index_sha256"],
        "claims": [{
            "task_id": item["task_id"],
            "topic": item["topic"],
            "slot_id": item["slot_id"],
            "proposal_sha256": item["proposal_sha256"],
        } for item in proposals],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(plan, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, args.output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
