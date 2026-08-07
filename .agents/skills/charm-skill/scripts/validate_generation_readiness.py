#!/usr/bin/env python3
"""Fail-closed CHARM generator/admission/canary validator.

The validator checks digest-bound evidence and independently produced receipts.
It does not generate tasks, solve tasks, or manufacture missing evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "charm-generator-admission-v4.1"
RECEIPT_VERSION = "charm-generator-admission-receipt-v4.1"
POLICY_VERSION = "charm-synthmem-api-action-remediation-v2"
FAILURE_PROFILE_ID = "synthmem-v3-modal-eval4-20260803T054055Z"
TASK_ID_PLAN_SCHEMA = "charm-task-id-plan-v2"
TASK_ID_RESERVATION_RECEIPT_SCHEMA = "charm-task-id-reservation-receipt-v2"
BATCH_CODE_RESERVATION_RECEIPT_SCHEMA = "charm-batch-code-reservation-receipt-v1"
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

STAGE_ORDER = {
    "pre-generation": 0,
    "post-generation": 1,
    "pre-training": 2,
    "promotion": 3,
    "deployment": 4,
}

REQUIRED_PROFILE_HASHES = {
    "audit_summary": "b2553fe505bbecd4420159deb7e070f30b3da71c8b1e5ff224b69a96a9c54f90",
    "detailed_audit": "4876a032875f0a31773bcc79d949d95131effaf8213ae9213953b4963c0f1ca6",
    "validator_v4_spec": "55ef7e69fb0a6d7f2d861ee761407f15971fb2fd0b28354d31e70cef11aaaef8",
    "mechanism_summary": "52e6b1581e86e7bdd5fbee8f5ec583ef17e9906dab56e57ffc95cca3c4c2c7a6",
    "dataset_shape": "6edba0c806293ab3a788434edba61ebd9bffb2506321d6d0f1191646be9a246b",
    "training_dynamics": "6f0bf263cb883930ebf3505c435f407ffa36e1fecbc05816050d56f09c0028e8",
}

REQUIRED_PROFILE_COUNTS = {
    "actual_attempts": 311,
    "failed_attempts": 288,
    "compile_or_link_failures": 281,
    "public_api_absent_or_misnamed_failures": 264,
    "semantic_counterexamples": 6,
    "runtime_failures": 1,
    "existing_header_change_rows": 0,
    "genuine_repair_trajectory_rows": 0,
    "calibration_rows": 0,
}

REQUIRED_MECHANISMS = {
    "public-api-completeness",
    "file-action-selection",
    "header-self-containment",
    "compiler-feedback-repair",
    "state-transition-ordering",
    "container-lifetime",
    "member-shadowing",
    "warning-as-error",
    "whole-file-application",
    "anchor-retention",
}

ROLE_RANGES = {
    "direct_verified_success": (0.50, 0.70),
    "boundary_case": (0.15, 0.25),
    "repair_trajectory": (0.20, 0.30),
    "calibration": (0.05, 0.08),
}

STARTER_TARGETS = {
    "empty": 0.20,
    "skeleton": 0.25,
    "partial_implementation": 0.20,
    "semantic_bug": 0.15,
    "compile_bug": 0.10,
    "near_correct": 0.10,
}

API_CAPABILITIES = {
    "implement_missing_api",
    "preserve_api",
    "extend_api",
    "repair_api",
    "refactor_api",
}

REPAIR_TYPES = {
    "compile_repair",
    "linker_repair",
    "api_repair",
    "hidden_test_repair",
    "runtime_repair",
    "sanitizer_repair",
}

HEADER_MODES = {
    "frozen",
    "editable",
    "reconstructed",
    "repaired",
    "extended",
}

DATASET_SHAPE_HISTOGRAMS = {
    "topic",
    "difficulty",
    "starter",
    "repair",
    "file_count",
    "header_edit",
    "template_usage",
    "exception_usage",
    "concurrency_usage",
    "pointer_usage",
    "ast_nodes",
    "api_shape",
}

PROMOTION_SCORE_WEIGHTS = {
    "task_quality": 0.15,
    "curriculum": 0.20,
    "admission": 0.20,
    "shadow_validation": 0.20,
    "benchmark_simulation": 0.15,
    "training_dynamics": 0.10,
}

SOURCE_BINDING_RULE_ORDER = (
    "builder_source",
    "chat_template",
    "eval_wrapper_source",
    "feedback_policy",
    "heldout_manifest",
    "task_id_reserver_source",
    "tokenizer_manifest",
    "uniqueness_scanner_source",
    "verifier_source",
    "batch_code_reserver_source",
)
SOURCE_BINDING_NAMES = set(SOURCE_BINDING_RULE_ORDER)

PROOF_PLAN_FIELDS = {
    "public_api_probe_required",
    "header_isolation_required",
    "strict_cpp17_werror_required",
    "target_pass_required",
    "starter_rejection_required",
    "failure_mutation_required",
    "semantic_mutation_required",
    "grader_determinism_required",
    "grader_portability_required",
    "sanitizer_required",
    "anti_cheat_required",
    "dynamic_nonce_required",
    "application_replay_required",
    "required_companion_file_check",
    "global_uniqueness_recheck_after_generation",
}

TASK_PROOF_FIELDS = {
    "target_passed",
    "starter_rejected",
    "failure_mutation_rejected",
    "semantic_mutation_rejected",
    "protected_artifacts_unchanged",
    "api_probe_passed",
    "header_isolation_passed",
    "strict_cpp17_werror_passed",
    "grader_determinism_passed",
    "grader_portability_passed",
    "sanitizer_passed",
    "anti_cheat_passed",
    "dynamic_nonce_passed",
    "application_replay_passed",
    "required_companion_files_complete",
}

SERIALIZATION_PROOF_FIELDS = {
    "exact_token_replay_passed",
    "loss_mask_passed",
    "eos_passed",
    "no_truncation",
    "whole_file_parse_passed",
    "proved_target_hash_match",
    "editable_scope_passed",
    "protected_scope_passed",
    "action_harmony_passed",
    "no_private_artifact_leakage",
}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    passed: bool
    observed: Any
    expected: Any
    evidence: str
    reason: str
    suggested_fix: str
    confidence: float = 1.0
    deterministic: bool = True


class Gate:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def check(
        self,
        rule_id: str,
        condition: bool,
        *,
        observed: Any,
        expected: Any,
        evidence: str,
        reason: str,
        suggested_fix: str,
        severity: str = "critical",
    ) -> None:
        self.findings.append(
            Finding(
                rule_id=rule_id,
                severity=severity,
                passed=bool(condition),
                observed=observed,
                expected=expected,
                evidence=evidence,
                reason=reason,
                suggested_fix=suggested_fix,
            )
        )


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _integer(value: Any, default: int = -1) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _number(value: Any, default: float = float("nan")) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return default


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return len(set(value.lower())) > 1


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _resolve_path(subject_path: Path, raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = subject_path.parent / path
    return path.resolve()


def _verify_file_binding(
    gate: Gate,
    subject_path: Path,
    binding: Any,
    *,
    rule_id: str,
    label: str,
    required_hash: str | None = None,
) -> Path | None:
    data = _mapping(binding)
    path = _resolve_path(subject_path, data.get("path"))
    declared = data.get("sha256")
    exists = path is not None and path.is_file()
    actual = _sha256_file(path) if exists else None
    valid = exists and _is_sha256(declared) and actual == declared
    if required_hash is not None:
        valid = valid and actual == required_hash
    gate.check(
        rule_id,
        valid,
        observed={"path": str(path) if path else None, "declared": declared, "actual": actual},
        expected={"file_present": True, "sha256": required_hash or "declared digest"},
        evidence=label,
        reason="Exact source/evidence bytes must be present and digest-bound.",
        suggested_fix=f"Package the exact {label} bytes and refresh its SHA-256 binding.",
    )
    return path if valid else None


def _load_json_binding(
    gate: Gate,
    subject_path: Path,
    binding: Any,
    *,
    rule_id: str,
    label: str,
) -> dict[str, Any]:
    path = _verify_file_binding(
        gate,
        subject_path,
        binding,
        rule_id=rule_id,
        label=label,
    )
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return _mapping(value)


def _check_zero_match_receipt(
    gate: Gate,
    receipt: dict[str, Any],
    *,
    rule_id: str,
    evidence: str,
    expected_proposal_plan_sha256: str | None = None,
    expected_generated_query_count: int | None = None,
) -> None:
    match_fields = (
        "parse_failures",
        "task_id_matches",
        "exact_matches",
        "near_matches",
        "structural_matches",
        "semantic_matches",
        "ambiguous_matches",
    )
    observed = {field: receipt.get(field) for field in match_fields}
    passed = (
        receipt.get("decision") == "PASS"
        and receipt.get("repository_scope_complete") is True
        and all(_integer(receipt.get(field)) == 0 for field in match_fields)
        and _is_sha256(receipt.get("corpus_index_sha256"))
        and _is_sha256(receipt.get("proposal_plan_sha256"))
        and (
            expected_generated_query_count is None
            or (
                receipt.get("proposal_count") == expected_generated_query_count
                and receipt.get("generated_query_count")
                == expected_generated_query_count
                and receipt.get("generated_component_count")
                == expected_generated_query_count * 12
                and _is_sha256(receipt.get("materialization_manifest_sha256"))
            )
        )
        and (
            expected_proposal_plan_sha256 is None
            or receipt.get("proposal_plan_sha256") == expected_proposal_plan_sha256
        )
    )
    gate.check(
        rule_id,
        passed,
        observed={
            "decision": receipt.get("decision"),
            "repository_scope_complete": receipt.get("repository_scope_complete"),
            **observed,
        },
        expected={
            "decision": "PASS",
            "repository_scope_complete": True,
            "all_counts": 0,
            "proposal_plan_sha256": expected_proposal_plan_sha256 or "valid SHA-256",
            "generated_query_count": expected_generated_query_count
            if expected_generated_query_count is not None
            else "protocol-defined",
        },
        evidence=evidence,
        reason="Task generation cannot proceed with a duplicate, ambiguous match, or incomplete scan.",
        suggested_fix="Complete the repository-wide scan and replace every matched or ambiguous proposal.",
    )


def _v1_generation_plan_identity_propagated(
    generation_plan: dict[str, Any],
    task_id_plan: dict[str, Any],
    total: int,
) -> bool:
    """Require the permanent batch identity on the V1 plan and every proposal."""
    if task_id_plan.get("protocol_id") != "task-generation-v1":
        return True
    identity_fields = (
        "generation_batch_id",
        "generation_session_id",
        "generation_batch_code",
        "generation_batch_created_at_utc",
        "batch_code_reservation_receipt_sha256",
    )
    if any(
        generation_plan.get(field) != task_id_plan.get(field)
        for field in identity_fields
    ):
        return False
    batch_code = task_id_plan.get("generation_batch_code")
    batch_created_at = task_id_plan.get("generation_batch_created_at_utc")
    batch_receipt_sha256 = task_id_plan.get(
        "batch_code_reservation_receipt_sha256"
    )
    if not (
        isinstance(batch_code, str)
        and len(batch_code) == 5
        and batch_code.isdigit()
        and isinstance(batch_created_at, str)
        and bool(batch_created_at)
        and _is_sha256(batch_receipt_sha256)
    ):
        return False
    claims = {
        row.get("task_id"): row
        for row in _list(task_id_plan.get("claims"))
        if isinstance(row, dict) and isinstance(row.get("task_id"), str)
    }
    proposals = _list(generation_plan.get("proposals"))
    return (
        len(claims) == total
        and len(proposals) == total
        and all(
            isinstance(row, dict)
            and isinstance(row.get("task_id"), str)
            and row.get("task_id") in claims
            and row.get("proposal_sha256")
            == claims[row["task_id"]].get("proposal_sha256")
            and row.get("generation_batch_code") == batch_code
            and row.get("generation_batch_created_at_utc") == batch_created_at
            and row.get("batch_code_reservation_receipt_sha256")
            == batch_receipt_sha256
            for row in proposals
        )
    )


def _check_v1_generation_plan_identity(
    gate: Gate,
    *,
    generation_plan: dict[str, Any],
    task_id_plan: dict[str, Any],
    total: int,
) -> None:
    passed = _v1_generation_plan_identity_propagated(
        generation_plan, task_id_plan, total
    )
    gate.check(
        "ID-004",
        passed,
        observed={
            "protocol_id": task_id_plan.get("protocol_id"),
            "generation_batch_code": generation_plan.get("generation_batch_code"),
            "generation_batch_created_at_utc": generation_plan.get(
                "generation_batch_created_at_utc"
            ),
            "proposal_count": len(_list(generation_plan.get("proposals"))),
        },
        expected="the atomic batch identity and receipt digest on the V1 plan and all proposals",
        evidence="generation_plan and task_id_reservation_plan",
        reason="A later reservation receipt cannot retroactively repair missing batch identity in frozen task bytes.",
        suggested_fix="Regenerate from an owner that propagates the permanent batch code before uniqueness and materialization.",
    )

def _check_task_id_reservation(
    gate: Gate,
    *,
    total: int,
    proposal_plan_sha256: str,
    uniqueness: dict[str, Any],
    uniqueness_binding: Any,
    plan: dict[str, Any],
    plan_binding: Any,
    receipt: dict[str, Any],
    batch_receipt: dict[str, Any],
    batch_receipt_binding: Any,
) -> None:
    claims = _list(plan.get("claims"))
    task_ids = [
        claim.get("task_id")
        for claim in claims
        if isinstance(claim, dict) and isinstance(claim.get("task_id"), str)
    ]
    slot_keys = [
        f"{plan.get('generation_batch_id')}|{claim.get('topic')}|{claim.get('slot_id')}"
        for claim in claims
        if isinstance(claim, dict)
    ]
    slots_by_topic: dict[str, set[str]] = {}
    for claim in claims:
        if (
            isinstance(claim, dict)
            and isinstance(claim.get("topic"), str)
            and isinstance(claim.get("slot_id"), str)
        ):
            slots_by_topic.setdefault(claim["topic"], set()).add(claim["slot_id"])
    protocol_id = plan.get("protocol_id")
    batch_code = plan.get("generation_batch_code")
    batch_created_at = plan.get("generation_batch_created_at_utc")
    expected_batch_receipt_hash = _mapping(batch_receipt_binding).get("sha256")
    batch_receipt_valid = (
        batch_receipt.get("schema_version") == BATCH_CODE_RESERVATION_RECEIPT_SCHEMA
        and batch_receipt.get("decision") == "PASS"
        and batch_receipt.get("operation") == "reserve_batch_code"
        and batch_receipt.get("atomic_lock_acquired") is True
        and batch_receipt.get("registry_reconciled") is True
        and batch_receipt.get("reservation_state") == "permanent"
        and batch_receipt.get("generation_batch_id") == plan.get("generation_batch_id")
        and batch_receipt.get("generation_session_id") == plan.get("generation_session_id")
        and batch_receipt.get("generation_batch_code") == batch_code
        and batch_receipt.get("generation_batch_created_at_utc") == batch_created_at
        and batch_receipt.get("batch_code_derivation") == BATCH_CODE_DERIVATION
        and batch_receipt.get("historical_alias_only") is False
        and batch_receipt.get("codes_reusable") is False
        and _is_sha256(batch_receipt.get("registry_before_sha256"))
        and _is_sha256(batch_receipt.get("registry_after_sha256"))
        and _integer(batch_receipt.get("registry_revision"), -1) >= 1
    )
    gate.check(
        "ID-003",
        batch_receipt_valid,
        observed={
            "decision": batch_receipt.get("decision"),
            "generation_batch_code": batch_receipt.get("generation_batch_code"),
            "generation_batch_id": batch_receipt.get("generation_batch_id"),
            "generation_session_id": batch_receipt.get("generation_session_id"),
            "historical_alias_only": batch_receipt.get("historical_alias_only"),
        },
        expected=(
            "a permanent, atomic, repository-unique five-digit timestamp-derived batch-code "
            "reservation owned by this batch and session"
        ),
        evidence="batch_code_reservation_receipt",
        reason="A five-digit timestamp fragment is not unique without an atomic permanent registry.",
        suggested_fix="Reserve a fresh code under the canonical batch-code registry lock.",
    )
    v1_shape_valid = protocol_id != "task-generation-v1" or (
        total == V1_TASK_COUNT
        and set(slots_by_topic) == set(V1_TOPICS)
        and all(slots == V1_SLOT_IDS for slots in slots_by_topic.values())
    )
    claims_valid = (
        plan.get("schema_version") == TASK_ID_PLAN_SCHEMA
        and isinstance(protocol_id, str)
        and bool(protocol_id)
        and isinstance(plan.get("generation_batch_id"), str)
        and bool(plan.get("generation_batch_id"))
        and isinstance(plan.get("generation_session_id"), str)
        and bool(plan.get("generation_session_id"))
        and isinstance(batch_code, str)
        and len(batch_code) == 5
        and batch_code.isdigit()
        and isinstance(batch_created_at, str)
        and bool(batch_created_at)
        and plan.get("batch_code_reservation_receipt_sha256")
        == expected_batch_receipt_hash
        and batch_receipt_valid
        and plan.get("proposal_plan_sha256") == proposal_plan_sha256
        and plan.get("corpus_index_sha256") == uniqueness.get("corpus_index_sha256")
        and len(claims) == total
        and len(task_ids) == total
        and len(set(task_ids)) == total
        and len(set(slot_keys)) == total
        and v1_shape_valid
        and all(
            isinstance(claim, dict)
            and isinstance(claim.get("task_id"), str)
            and bool(claim.get("task_id"))
            and isinstance(claim.get("topic"), str)
            and bool(claim.get("topic"))
            and isinstance(claim.get("slot_id"), str)
            and bool(claim.get("slot_id"))
            and _is_sha256(claim.get("proposal_sha256"))
            for claim in claims
        )
    )
    gate.check(
        "ID-001",
        claims_valid,
        observed={
            "schema_version": plan.get("schema_version"),
            "claim_count": len(claims),
            "unique_task_ids": len(set(task_ids)),
            "unique_slot_keys": len(set(slot_keys)),
            "protocol_id": protocol_id,
            "topic_count": len(slots_by_topic),
            "topics": sorted(slots_by_topic),
            "generation_batch_id": plan.get("generation_batch_id"),
            "generation_session_id": plan.get("generation_session_id"),
            "generation_batch_code": batch_code,
            "generation_batch_created_at_utc": batch_created_at,
        },
        expected={
            "claim_count": total,
            "unique_task_ids": total,
            "unique_slot_keys": total,
            "v1_topics": list(V1_TOPICS)
            if protocol_id == "task-generation-v1"
            else "protocol-defined",
            "v1_slots": sorted(V1_SLOT_IDS)
            if protocol_id == "task-generation-v1"
            else "protocol-defined",
            "binding": "current uniqueness corpus index",
        },
        evidence="task_id_reservation_plan",
        reason="Task IDs and V1 slots must be frozen before any generation session can claim them.",
        suggested_fix="Rebuild the task-ID plan with unique IDs, slots, owner session, and hashes.",
    )

    reserved_ids = _list(receipt.get("reserved_task_ids"))
    created_ids = _list(receipt.get("created_task_ids"))
    resumed_ids = _list(receipt.get("resumed_task_ids"))
    receipt_slot_keys = _list(receipt.get("slot_keys"))
    receipt_lists_valid = all(
        isinstance(value, str)
        for values in (reserved_ids, created_ids, resumed_ids, receipt_slot_keys)
        for value in values
    )
    expected_plan_hash = _mapping(plan_binding).get("sha256")
    expected_uniqueness_hash = _mapping(uniqueness_binding).get("sha256")
    receipt_valid = (
        receipt.get("schema_version") == TASK_ID_RESERVATION_RECEIPT_SCHEMA
        and receipt.get("decision") == "PASS"
        and receipt.get("operation") == "reserve"
        and receipt.get("reservation_state") == "reserved"
        and receipt.get("atomic_lock_acquired") is True
        and receipt.get("registry_reconciled") is True
        and _integer(receipt.get("collision_count"), -1) == 0
        and receipt.get("protocol_id") == protocol_id
        and receipt.get("generation_batch_id") == plan.get("generation_batch_id")
        and receipt.get("generation_session_id") == plan.get("generation_session_id")
        and receipt.get("generation_batch_code") == batch_code
        and receipt.get("generation_batch_created_at_utc") == batch_created_at
        and receipt.get("batch_code_reservation_receipt_sha256")
        == expected_batch_receipt_hash
        and receipt.get("proposal_plan_sha256") == proposal_plan_sha256
        and receipt.get("corpus_index_sha256") == plan.get("corpus_index_sha256")
        and receipt.get("reservation_plan_sha256") == expected_plan_hash
        and receipt.get("uniqueness_receipt_sha256") == expected_uniqueness_hash
        and _is_sha256(receipt.get("registry_before_sha256"))
        and _is_sha256(receipt.get("registry_after_sha256"))
        and _integer(receipt.get("registry_revision"), -1) >= 0
        and _integer(receipt.get("claim_count"), -1) == total
        and receipt_lists_valid
        and sorted(reserved_ids) == sorted(task_ids)
        and not set(created_ids).intersection(resumed_ids)
        and sorted(created_ids + resumed_ids) == sorted(task_ids)
        and sorted(receipt_slot_keys) == sorted(slot_keys)
        and receipt.get("idempotent_resume_only_for_same_owner_and_proposal") is True
        and receipt.get("terminal_or_tombstoned_ids_reusable") is False
    )
    gate.check(
        "ID-002",
        receipt_valid,
        observed={
            "decision": receipt.get("decision"),
            "atomic_lock_acquired": receipt.get("atomic_lock_acquired"),
            "registry_reconciled": receipt.get("registry_reconciled"),
            "collision_count": receipt.get("collision_count"),
            "claim_count": receipt.get("claim_count"),
            "reserved_task_ids": reserved_ids,
        },
        expected=(
            "an atomic zero-collision reservation of every planned task ID and slot, owned by "
            "this session, with tombstoned/terminal IDs permanently non-reusable"
        ),
        evidence="task_id_reservation_receipt",
        reason="A uniqueness scan alone leaves a multi-session read-then-write race.",
        suggested_fix=(
            "Under the canonical registry lock, reserve a fresh collision-free ID set; resume "
            "only an identical reservation owned by the same session and proposal."
        ),
    )


def _check_common(bundle: dict[str, Any], subject_path: Path, gate: Gate) -> None:
    gate.check(
        "V4G-000",
        bundle.get("schema_version") == SCHEMA_VERSION,
        observed=bundle.get("schema_version"),
        expected=SCHEMA_VERSION,
        evidence="schema_version",
        reason="The validator accepts only the versioned V4 generator-admission schema.",
        suggested_fix="Regenerate the admission bundle from the V4 template.",
    )
    gate.check(
        "V4G-001",
        bundle.get("policy_version") == POLICY_VERSION,
        observed=bundle.get("policy_version"),
        expected=POLICY_VERSION,
        evidence="policy_version",
        reason="Threshold or rule drift must create a new explicit policy version.",
        suggested_fix="Use the active remediation policy or authorize and version a policy change.",
    )
    gate.check(
        "V4G-002",
        bundle.get("example_only") is False,
        observed=bundle.get("example_only"),
        expected=False,
        evidence="example_only",
        reason="The bundled template is not evidence and must never authorize generation.",
        suggested_fix="Replace every placeholder with real evidence, then set example_only to false.",
    )

    contract = _mapping(bundle.get("iteration_contract"))
    required_contract = {
        "iteration_id",
        "target_behavior",
        "observed_failure_hypothesis",
        "planned_data_intervention",
        "primary_metric",
        "promotion_threshold",
        "stop_condition",
        "previous_best_run_ids",
        "previous_best_attempt_ledger_sha256",
        "authorized_training_diff",
        "feedback_policy_id",
    }
    missing_contract = sorted(
        key
        for key in required_contract
        if key not in contract or contract.get(key) in (None, "", [], {})
    )
    gate.check(
        "V4G-010",
        not missing_contract,
        observed=missing_contract,
        expected="all iteration-contract fields populated",
        evidence="iteration_contract",
        reason="Generation must test a falsifiable intervention rather than accumulate tasks.",
        suggested_fix="Freeze the target behavior, hypothesis, intervention, metrics, and stop rule.",
    )
    ledger_hash = contract.get("previous_best_attempt_ledger_sha256")
    gate.check(
        "V4G-011",
        _is_sha256(ledger_hash),
        observed=ledger_hash,
        expected="non-placeholder SHA-256 of the previous-best attempt ledger",
        evidence="iteration_contract.previous_best_attempt_ledger_sha256",
        reason="Aggregate historical scores cannot support matched pass/fail transitions.",
        suggested_fix="Re-evaluate the previous-best checkpoint and package its attempt ledger.",
    )

    evidence = _mapping(bundle.get("failure_evidence"))
    profile = _mapping(evidence.get("profile"))
    profile_counts = _mapping(profile.get("counts"))
    count_mismatches = {
        key: profile_counts.get(key)
        for key, expected in REQUIRED_PROFILE_COUNTS.items()
        if profile_counts.get(key) != expected
    }
    gate.check(
        "V4G-012",
        profile.get("profile_id") == FAILURE_PROFILE_ID and not count_mismatches,
        observed={"profile_id": profile.get("profile_id"), "count_mismatches": count_mismatches},
        expected={"profile_id": FAILURE_PROFILE_ID, "counts": REQUIRED_PROFILE_COUNTS},
        evidence="failure_evidence.profile",
        reason="The next generation must be conditioned on the exact audited regression profile.",
        suggested_fix="Bind the exact post-run failure profile and its reconciled counts.",
    )
    evidence_health = {
        "status": evidence.get("status"),
        "invalid_evidence_count": evidence.get("invalid_evidence_count"),
        "unresolved_diagnosis_count": evidence.get("unresolved_diagnosis_count"),
        "unauthorized_disposition_count": evidence.get("unauthorized_disposition_count"),
    }
    gate.check(
        "V4G-013",
        evidence_health == {
            "status": "valid",
            "invalid_evidence_count": 0,
            "unresolved_diagnosis_count": 0,
            "unauthorized_disposition_count": 0,
        },
        observed=evidence_health,
        expected={"status": "valid", "all_blocker_counts": 0},
        evidence="failure_evidence health",
        reason="Invalid or unresolved failure evidence cannot authorize synthesis.",
        suggested_fix="Repair the evaluator or diagnosis and regenerate accepted evidence manifests.",
    )

    bindings = _mapping(evidence.get("artifact_bindings"))
    for index, (name, expected_hash) in enumerate(sorted(REQUIRED_PROFILE_HASHES.items()), 1):
        _verify_file_binding(
            gate,
            subject_path,
            bindings.get(name),
            rule_id=f"V4G-014.{index:02d}",
            label=f"failure-profile {name}",
            required_hash=expected_hash,
        )

    audit_tree = _mapping(bundle.get("audit_skill_tree"))
    audit_root = _resolve_path(subject_path, audit_tree.get("path"))
    audit_declared = audit_tree.get("sha256")
    audit_actual = tree_sha256(audit_root) if audit_root and audit_root.is_dir() else None
    gate.check(
        "V4G-015",
        audit_root is not None
        and audit_root.is_dir()
        and _is_sha256(audit_declared)
        and audit_actual == audit_declared,
        observed={"path": str(audit_root) if audit_root else None, "declared": audit_declared, "actual": audit_actual},
        expected="complete updated-task audit skill tree with matching digest",
        evidence="audit_skill_tree",
        reason="CHARM synthesis authority must bind the exact operator-supplied audit skill bytes.",
        suggested_fix="Copy the complete updated-task audit skill and refresh its deterministic tree hash.",
    )

    plan = _mapping(bundle.get("generation_plan"))
    total = _integer(plan.get("authorized_task_count"), 0)
    role_counts = _mapping(plan.get("role_counts"))
    roles_valid = total > 0 and set(role_counts) == set(ROLE_RANGES)
    role_observed: dict[str, Any] = {}
    if roles_valid:
        roles_valid = sum(_integer(value, -1) for value in role_counts.values()) == total
        for role, (minimum, maximum) in ROLE_RANGES.items():
            count = _integer(role_counts.get(role), -1)
            fraction = count / total if total else -1.0
            role_observed[role] = {"count": count, "fraction": fraction}
            roles_valid = roles_valid and minimum <= fraction <= maximum
    gate.check(
        "V4G-020",
        roles_valid,
        observed={"authorized_task_count": total, "roles": role_observed or role_counts},
        expected={role: bounds for role, bounds in ROLE_RANGES.items()},
        evidence="generation_plan.role_counts",
        reason="The corpus must balance direct, boundary, genuine repair, and calibration supervision.",
        suggested_fix="Recompose the exact task plan within every role range; metadata relabeling is insufficient.",
    )

    actions = _mapping(plan.get("action_counts"))
    action_shapes = _mapping(actions.get("action_shapes"))
    empty_fraction = _integer(actions.get("empty_starter"), -1) / total if total else 1.0
    existing_header_fraction = (
        _integer(actions.get("existing_header_change"), -1) / total if total else -1.0
    )
    header_only_fraction = (
        _integer(actions.get("header_only_or_template"), -1) / total if total else -1.0
    )
    header_source_fraction = (
        _integer(actions.get("header_and_source"), -1) / total if total else -1.0
    )
    max_shape_fraction = (
        max((_integer(value, total + 1) for value in action_shapes.values()), default=total + 1)
        / total
        if total
        else 1.0
    )
    action_observed = {
        "empty_starter_fraction": empty_fraction,
        "existing_header_change_fraction": existing_header_fraction,
        "header_only_or_template_fraction": header_only_fraction,
        "header_and_source_fraction": header_source_fraction,
        "max_single_action_shape_fraction": max_shape_fraction,
        "unparseable": actions.get("unparseable"),
        "unjustified_noop": actions.get("unjustified_noop"),
    }
    gate.check(
        "V4G-021",
        empty_fraction <= 0.25,
        observed=empty_fraction,
        expected="<= 0.25",
        evidence="generation_plan.action_counts.empty_starter",
        reason="The corrective corpus must break the empty-starter/action shortcut.",
        suggested_fix="Replace empty-starter rows with verified existing-scaffold tasks.",
    )
    gate.check(
        "V4G-022",
        existing_header_fraction >= 0.30,
        observed=existing_header_fraction,
        expected=">= 0.30 for this remediation profile",
        evidence="generation_plan.action_counts.existing_header_change",
        reason="Existing-header editing is the primary intervention for the 264 API-visibility failures.",
        suggested_fix="Add independently verified tasks that require modifying an existing public header.",
    )
    gate.check(
        "V4G-023",
        header_only_fraction >= 0.05,
        observed=header_only_fraction,
        expected=">= 0.05",
        evidence="generation_plan.action_counts.header_only_or_template",
        reason="Header-only and template placement require direct supervision.",
        suggested_fix="Add header-only or template-in-header tasks with isolated-header proof.",
    )
    gate.check(
        "V4G-024",
        header_source_fraction >= 0.20,
        observed=header_source_fraction,
        expected=">= 0.20",
        evidence="generation_plan.action_counts.header_and_source",
        reason="The model must learn coordinated public declaration and implementation edits.",
        suggested_fix="Add tasks whose correct action changes both the existing header and source.",
    )
    gate.check(
        "V4G-025",
        bool(action_shapes)
        and max_shape_fraction <= 0.60
        and _integer(actions.get("unparseable")) == 0
        and _integer(actions.get("unjustified_noop")) == 0,
        observed=action_observed,
        expected={"max_single_shape": 0.60, "unparseable": 0, "unjustified_noop": 0},
        evidence="generation_plan.action_counts",
        reason="A single action topology or invalid target can recreate the prior shortcut.",
        suggested_fix="Diversify action shapes and remove unparseable or unjustified no-op plans.",
    )

    families = _list(plan.get("families"))
    bad_families = [
        _mapping(item).get("family_id")
        for item in families
        if _integer(_mapping(item).get("action_topology_count")) < 2
        or _mapping(item).get("has_existing_scaffold") is not True
    ]
    gate.check(
        "V4G-026",
        bool(families) and not bad_families,
        observed={"family_count": len(families), "failing_families": bad_families},
        expected="every family has >=2 action topologies and an existing scaffold",
        evidence="generation_plan.families",
        reason="Topic balance does not prevent action-shape collapse within a family.",
        suggested_fix="Add the missing action topology and existing-scaffold example per family.",
    )

    source_counts = _mapping(plan.get("source_counts"))
    non_synthetic = sum(
        _integer(count, 0) for source, count in source_counts.items() if source != "synthetic"
    )
    gate.check(
        "V4G-027",
        sum(_integer(value, -1) for value in source_counts.values()) == total and non_synthetic > 0,
        observed=source_counts,
        expected="counts sum to authorized total and at least one verified non-synthetic source",
        evidence="generation_plan.source_counts",
        reason="An all-synthetic origin is a blocked monoculture under this policy.",
        suggested_fix="Include independently verified human/canonical or organic-trajectory anchors.",
    )

    mechanisms = set(_list(plan.get("required_mechanism_ids")))
    missing_mechanisms = sorted(REQUIRED_MECHANISMS - mechanisms)
    gate.check(
        "V4G-028",
        not missing_mechanisms,
        observed=sorted(mechanisms),
        expected=sorted(REQUIRED_MECHANISMS),
        evidence="generation_plan.required_mechanism_ids",
        reason="Every observed high-priority failure mechanism must receive explicit coverage.",
        suggested_fix="Add independent tasks and negative controls for each missing mechanism.",
    )

    feedback = _mapping(bundle.get("feedback_policy"))
    feedback_ok = (
        feedback.get("policy_id") == contract.get("feedback_policy_id")
        and feedback.get("policy_id") == "redacted-compiler-feedback-v1"
        and _is_sha256(feedback.get("policy_sha256"))
        and feedback.get("private_test_output_disclosed") is False
        and feedback.get("separate_full_private_diagnostic_lane") is True
        and feedback.get("repair_training_matches_promotion_policy") is True
    )
    gate.check(
        "V4G-030",
        feedback_ok,
        observed=feedback,
        expected={
            "policy_id": "redacted-compiler-feedback-v1",
            "private_test_output_disclosed": False,
            "separate_full_private_diagnostic_lane": True,
            "repair_training_matches_promotion_policy": True,
        },
        evidence="feedback_policy",
        reason="Private compiler/test output cannot leak into training or be compared with a redacted lane.",
        suggested_fix="Freeze a hash-bound redacted policy and use it for both repair training and promotion.",
    )

    repair_plan = _mapping(plan.get("repair_plan"))
    planned_repair_count = _integer(role_counts.get("repair_trajectory"), -1)
    gate.check(
        "V4G-031",
        repair_plan.get("genuine_four_turn_suffix_required") is True
        and repair_plan.get("failing_candidate_receipt_required") is True
        and repair_plan.get("corrected_candidate_receipt_required") is True
        and repair_plan.get("metadata_only_rows_count_as_repair") is False
        and _integer(repair_plan.get("planned_genuine_repair_count")) == planned_repair_count,
        observed=repair_plan,
        expected="all repair rows are real fail -> feedback -> correction trajectories",
        evidence="generation_plan.repair_plan",
        reason="Failure metadata attached to a final answer is not repair supervision.",
        suggested_fix="Construct genuine four-turn rows with bound failing and passing receipts.",
    )

    layout_counts = _mapping(plan.get("editable_layout_counts"))
    layout_fractions = {
        name: _integer(layout_counts.get(name), -1) / total if total else -1.0
        for name in ("cpp_only", "header_only", "header_and_cpp", "multi_file_gt2")
    }
    layout_ok = (
        _integer(layout_counts.get("cpp_only"), -1) >= 0
        and layout_fractions["cpp_only"] <= 0.40
        and 0.10 <= layout_fractions["header_only"] <= 0.20
        and layout_fractions["header_and_cpp"] >= 0.40
        and layout_fractions["multi_file_gt2"] >= 0.10
    )
    gate.check(
        "ADM-001",
        layout_ok,
        observed=layout_fractions,
        expected={
            "cpp_only": "<=0.40 (critical ceiling 0.60)",
            "header_only": "0.10..0.20",
            "header_and_cpp": ">=0.40 (critical floor 0.30)",
            "multi_file_gt2": ">=0.10",
        },
        evidence="generation_plan.editable_layout_counts",
        reason="A source-only curriculum recreates the API-exposure failure mode.",
        suggested_fix="Rebalance the frozen task plan before any task is generated.",
    )

    api_counts = _mapping(plan.get("api_capability_counts"))
    missing_api_capabilities = sorted(
        capability
        for capability in API_CAPABILITIES
        if _integer(api_counts.get(capability), -1) < 15
    )
    gate.check(
        "ADM-002",
        not missing_api_capabilities,
        observed=api_counts,
        expected={capability: ">=15 tasks" for capability in sorted(API_CAPABILITIES)},
        evidence="generation_plan.api_capability_counts",
        reason="Training admission requires direct coverage of every API reconstruction behavior.",
        suggested_fix="Add independently verified tasks for each deficient API capability.",
    )

    starter_counts = _mapping(plan.get("starter_type_counts"))
    starter_observed: dict[str, Any] = {}
    maximum_starter_deviation = 1.0
    starter_ok = total > 0 and set(starter_counts) == set(STARTER_TARGETS)
    if starter_ok:
        starter_ok = sum(_integer(value, -1) for value in starter_counts.values()) == total
        maximum_starter_deviation = 0.0
        for starter, target in STARTER_TARGETS.items():
            count = _integer(starter_counts.get(starter), -1)
            fraction = count / total
            deviation = abs(fraction - target)
            maximum_starter_deviation = max(maximum_starter_deviation, deviation)
            starter_observed[starter] = {
                "count": count,
                "fraction": fraction,
                "target": target,
                "deviation": deviation,
            }
        starter_ok = (
            starter_ok
            and maximum_starter_deviation <= 0.05 + 1e-12
            and _integer(actions.get("empty_starter"), -1)
            == _integer(starter_counts.get("empty"), -2)
        )
    gate.check(
        "ADM-003",
        starter_ok,
        observed=starter_observed or starter_counts,
        expected={"targets": STARTER_TARGETS, "maximum_absolute_deviation": 0.05},
        evidence="generation_plan.starter_type_counts",
        reason="Starter monoculture teaches an invalid file-action shortcut.",
        suggested_fix="Rebalance starter types to within five percentage points of every target.",
        severity="critical" if maximum_starter_deviation > 0.10 else "major",
    )

    repair_fraction = planned_repair_count / total if total else -1.0
    gate.check(
        "CURR-101",
        0.20 <= repair_fraction <= 0.30,
        observed=repair_fraction,
        expected="0.20..0.30 (critical reject below 0.15)",
        evidence="generation_plan.role_counts.repair_trajectory",
        reason="The corpus must contain enough genuine repair supervision to teach recovery.",
        suggested_fix="Add verified fail-feedback-correction trajectories.",
    )

    repair_type_counts = _mapping(repair_plan.get("repair_type_counts"))
    missing_repair_types = sorted(
        repair_type
        for repair_type in REPAIR_TYPES
        if planned_repair_count <= 0
        or _integer(repair_type_counts.get(repair_type), -1) / planned_repair_count < 0.05
    )
    gate.check(
        "CURR-102",
        not missing_repair_types,
        observed=repair_type_counts,
        expected={repair_type: ">=5% of repair rows" for repair_type in sorted(REPAIR_TYPES)},
        evidence="generation_plan.repair_plan.repair_type_counts",
        reason="Repair supervision must cover compile, link, API, hidden-test, runtime, and sanitizer recovery.",
        suggested_fix="Add receipt-backed repair rows for every missing repair mechanism.",
    )

    feedback_sanitization_ok = (
        feedback.get("sanitized") is True
        and _integer(feedback.get("maximum_feedback_lines"), 101) <= 100
        and feedback.get("hidden_answers_disclosed") is False
        and feedback.get("expected_outputs_disclosed") is False
        and feedback.get("private_test_names_disclosed") is False
    )
    gate.check(
        "CURR-103",
        feedback_sanitization_ok,
        observed=feedback,
        expected="sanitized <=100-line feedback with no hidden answers, expected outputs, or private test names",
        evidence="feedback_policy",
        reason="Private feedback leakage invalidates repair supervision and matched evaluation.",
        suggested_fix="Apply the bound redaction policy and regenerate every repair row.",
    )

    calibration_ok = 0.05 <= (
        _integer(role_counts.get("calibration"), -1) / total if total else -1.0
    ) <= 0.08
    gate.check(
        "CAL-001",
        calibration_ok,
        observed=role_counts.get("calibration"),
        expected="5-8% task_type=calibration rows",
        evidence="generation_plan.role_counts.calibration",
        reason="No-change calibration rows prevent reflexive unnecessary edits.",
        suggested_fix="Add oracle-backed already-correct tasks with task_type=calibration.",
    )

    header_mode_counts = _mapping(plan.get("header_mode_counts"))
    header_mode_observed = {
        mode: _integer(header_mode_counts.get(mode), -1) / total if total else -1.0
        for mode in HEADER_MODES
    }
    header_mode_ok = (
        set(header_mode_counts) == HEADER_MODES
        and sum(_integer(value, -1) for value in header_mode_counts.values()) == total
        and all(0.10 <= fraction <= 0.30 for fraction in header_mode_observed.values())
    )
    gate.check(
        "HDR-001",
        header_mode_ok,
        observed=header_mode_observed,
        expected="frozen/editable/reconstructed/repaired/extended each 10-30%",
        evidence="generation_plan.header_mode_counts",
        reason="Header behavior must be balanced instead of always frozen.",
        suggested_fix="Rebalance the five header modes around the 20% target.",
    )

    planned_shape = _mapping(plan.get("dataset_shape_plan"))
    planned_histograms = _mapping(planned_shape.get("histograms"))
    missing_histograms = sorted(
        name for name in DATASET_SHAPE_HISTOGRAMS if not _mapping(planned_histograms.get(name))
    )
    gate.check(
        "SHAPE-001",
        not missing_histograms and _list(planned_shape.get("families_below_minimum")) == [],
        observed={
            "missing_histograms": missing_histograms,
            "families_below_minimum": planned_shape.get("families_below_minimum"),
        },
        expected="all required shape histograms present and no family below its frozen minimum",
        evidence="generation_plan.dataset_shape_plan",
        reason="Training admission requires an explicit, complete dataset-shape contract.",
        suggested_fix="Populate every histogram and repair all family minimum deficits.",
    )

    uniqueness = _load_json_binding(
        gate,
        subject_path,
        bundle.get("uniqueness_receipt"),
        rule_id="V4G-040.01",
        label="pre-generation repository-wide uniqueness receipt",
    )
    # New owner bundles bind the exact frozen plan file.  Use that byte hash
    # after proving that its parsed JSON is the same object embedded in the
    # admission bundle.  Legacy bundles without this optional binding retain
    # the historical in-memory canonical-JSON convention.
    generation_plan_binding = bundle.get("generation_plan_binding")
    if generation_plan_binding is not None:
        bound_plan = _load_json_binding(
            gate,
            subject_path,
            generation_plan_binding,
            rule_id="V4G-019.01",
            label="frozen generation plan",
        )
        bound_plan_matches = bound_plan == plan
        gate.check(
            "V4G-019.02",
            bound_plan_matches,
            observed={"embedded_matches_bound_plan": bound_plan_matches},
            expected={"embedded_matches_bound_plan": True},
            evidence="generation_plan and generation_plan_binding",
            reason="The embedded generation contract must be the exact parsed frozen-plan subject.",
            suggested_fix="Regenerate the admission bundle from the bound frozen generation plan.",
        )
        generation_plan_sha256 = (
            _mapping(generation_plan_binding).get("sha256", "")
            if bound_plan_matches
            else ""
        )
    else:
        generation_plan_sha256 = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    proposal_plan_binding = bundle.get("proposal_plan_binding")
    if proposal_plan_binding is not None:
        proposal_plan = _load_json_binding(
            gate,
            subject_path,
            proposal_plan_binding,
            rule_id="V4G-018.01",
            label="reserved proposal plan",
        )
        proposal_hash = _mapping(proposal_plan_binding).get("sha256", "")
        proposal_matches = (
            proposal_plan.get("protocol_id") == plan.get("protocol_id")
            and proposal_plan.get("authorized_task_count") == plan.get("authorized_task_count")
            and proposal_plan.get("proposals") == plan.get("proposals")
            and plan.get("proposal_plan_sha256") == proposal_hash
        )
        gate.check(
            "V4G-018.02",
            proposal_matches,
            observed={
                "proposal_matches_generation_plan": proposal_matches,
                "generation_plan_sha256": generation_plan_sha256,
                "proposal_plan_sha256": proposal_hash,
            },
            expected={"proposal_matches_generation_plan": True},
            evidence="generation_plan and proposal_plan_binding",
            reason=(
                "A non-V1 curriculum may enrich the generation contract, but it must retain "
                "the exact reserved proposal identities and bytes."
            ),
            suggested_fix=(
                "Regenerate the curriculum plan from the reserved proposal plan and bind both."
            ),
        )
        proposal_plan_sha256 = proposal_hash if proposal_matches else ""
    else:
        proposal_plan_sha256 = generation_plan_sha256
    _check_zero_match_receipt(
        gate,
        uniqueness,
        rule_id="V4G-040.02",
        evidence="uniqueness receipt",
        expected_proposal_plan_sha256=proposal_plan_sha256,
        expected_generated_query_count=(
            total if plan.get("protocol_id") == "task-generation-v1" else None
        ),
    )

    task_id_plan_binding = bundle.get("task_id_reservation_plan")
    task_id_plan = _load_json_binding(
        gate,
        subject_path,
        task_id_plan_binding,
        rule_id="ID-000.01",
        label="task-ID reservation plan",
    )
    task_id_receipt_binding = bundle.get("task_id_reservation_receipt")
    task_id_receipt = _load_json_binding(
        gate,
        subject_path,
        task_id_receipt_binding,
        rule_id="ID-000.02",
        label="atomic task-ID reservation receipt",
    )
    batch_code_receipt_binding = bundle.get("batch_code_reservation_receipt")
    batch_code_receipt = _load_json_binding(
        gate,
        subject_path,
        batch_code_receipt_binding,
        rule_id="ID-000.03",
        label="atomic five-digit batch-code reservation receipt",
    )
    _check_task_id_reservation(
        gate,
        total=total,
        proposal_plan_sha256=proposal_plan_sha256,
        uniqueness=uniqueness,
        uniqueness_binding=bundle.get("uniqueness_receipt"),
        plan=task_id_plan,
        plan_binding=task_id_plan_binding,
        receipt=task_id_receipt,
        batch_receipt=batch_code_receipt,
        batch_receipt_binding=batch_code_receipt_binding,
    )
    _check_v1_generation_plan_identity(
        gate,
        generation_plan=plan,
        task_id_plan=task_id_plan,
        total=total,
    )

    proof_plan = _mapping(bundle.get("proof_plan"))
    missing_proofs = sorted(field for field in PROOF_PLAN_FIELDS if proof_plan.get(field) is not True)
    gate.check(
        "V4G-050",
        not missing_proofs,
        observed=missing_proofs,
        expected=sorted(PROOF_PLAN_FIELDS),
        evidence="proof_plan",
        reason="Every generated task must have API, executable, grader, safety, and application proof.",
        suggested_fix="Enable every proof and name the repository-owned command that produces its receipt.",
    )

    source_bindings = _mapping(bundle.get("source_bindings"))
    for index, name in enumerate(SOURCE_BINDING_RULE_ORDER, 1):
        _verify_file_binding(
            gate,
            subject_path,
            source_bindings.get(name),
            rule_id=f"V4G-060.{index:02d}",
            label=name.replace("_", " "),
        )

    bound_feedback_sha256 = _mapping(source_bindings.get("feedback_policy")).get("sha256")
    gate.check(
        "V4G-062",
        feedback.get("policy_sha256") == bound_feedback_sha256
        and _is_sha256(bound_feedback_sha256),
        observed={
            "feedback_policy_sha256": feedback.get("policy_sha256"),
            "source_binding_sha256": bound_feedback_sha256,
        },
        expected="the declared feedback policy and packaged policy bytes have the same SHA-256",
        evidence="feedback_policy and source_bindings.feedback_policy",
        reason="A policy label cannot substitute for the exact redaction-policy bytes.",
        suggested_fix=(
            "Bind the packaged feedback-policy source hash into the declared policy."
        ),
    )

    serialization = _mapping(bundle.get("serialization_plan"))
    serialization_ok = (
        serialization.get("exact_token_replay_required") is True
        and serialization.get("exact_loss_mask_required") is True
        and serialization.get("exact_eos_required") is True
        and serialization.get("whole_file_application_replay_required") is True
        and _integer(serialization.get("max_unparseable_rows")) == 0
        and _integer(serialization.get("max_truncated_rows")) == 0
        and _integer(serialization.get("max_private_leak_rows")) == 0
    )
    gate.check(
        "V4G-061",
        serialization_ok,
        observed=serialization,
        expected="exact token/mask/EOS/action replay with zero parse, truncation, or leakage failures",
        evidence="serialization_plan",
        reason="An executable solution beside a row does not prove the loss-bearing target is usable.",
        suggested_fix="Use the production tokenizer/template/parser and require exact per-row receipts.",
    )

    exposure = _mapping(bundle.get("exposure_plan"))
    previous_exposure = _number(exposure.get("previous_anchor_effective_exposure"), -1.0)
    planned_exposure = _number(exposure.get("planned_anchor_effective_exposure"), -1.0)
    exposure_ok = previous_exposure > 0 and (
        planned_exposure >= previous_exposure
        or (
            exposure.get("dilution_explicitly_authorized") is True
            and exposure.get("retention_canary_defined") is True
        )
    )
    gate.check(
        "V4G-070",
        exposure_ok,
        observed=exposure,
        expected="planned anchor exposure >= previous, or explicit dilution plus retention canary",
        evidence="exposure_plan",
        reason="Equal total steps can still silently halve known-successful anchor exposure.",
        suggested_fix="Restore anchor sampling weight or explicitly authorize and canary-test dilution.",
    )

    canary = _mapping(bundle.get("canary_plan"))
    canary_ledger = canary.get("previous_best_attempt_ledger_sha256")
    canary_ok = (
        canary_ledger == ledger_hash
        and _integer(canary.get("task_count")) == 20
        and _integer(canary.get("epochs_before_decision")) == 5
        and canary.get("evaluation_during_training") is True
        and _integer(canary.get("frozen_trial_count")) >= 4
        and _number(canary.get("stop_if_pass_at_1_drop_exceeds_tasks"), 99.0) <= 1.0
        and _number(canary.get("stop_if_public_api_absent_increase_pp"), 99.0) <= 2.0
        and canary.get("stop_on_contamination") is True
        and canary.get("stop_on_missing_action_topology") is True
        and _integer(canary.get("max_malformed_outputs")) == 0
        and _integer(canary.get("max_infrastructure_failures")) == 0
        and _number(canary.get("max_context_exhaustion_fraction"), 1.0) <= 0.01
        and canary.get("full_training_blocked_until_canary_pass") is True
    )
    gate.check(
        "CAN-001",
        canary_ok,
        observed=canary,
        expected="exactly 20 tasks and 5 epochs with evaluation, stop rules, and full training blocked",
        evidence="canary_plan",
        reason="A fixed small canary must pass before any full training run.",
        suggested_fix="Bind the previous ledger and freeze the 20-task/5-epoch canary.",
    )

    dynamics_plan = _mapping(bundle.get("training_dynamics_plan"))
    logging_plan_ok = (
        dynamics_plan.get("log_every_checkpoint") is True
        and dynamics_plan.get("require_training_loss") is True
        and dynamics_plan.get("require_validation_loss") is True
        and dynamics_plan.get("require_compile_rate") is True
        and dynamics_plan.get("require_hidden_test_rate") is True
    )
    gate.check(
        "DYN-001",
        logging_plan_ok,
        observed=dynamics_plan,
        expected="every checkpoint logs training loss, validation loss, compile rate, and hidden-test rate",
        evidence="training_dynamics_plan",
        reason="Near-zero training loss without held-out execution cannot select or promote a checkpoint.",
        suggested_fix="Freeze complete execution-aware checkpoint logging before generation.",
    )
    gate.check(
        "DYN-002",
        dynamics_plan.get("early_stopping_enabled") is True
        and dynamics_plan.get("selection_policy") == "best_composite_not_always_final",
        observed={
            "early_stopping_enabled": dynamics_plan.get("early_stopping_enabled"),
            "selection_policy": dynamics_plan.get("selection_policy"),
        },
        expected={"early_stopping_enabled": True, "selection_policy": "best_composite_not_always_final"},
        evidence="training_dynamics_plan",
        reason="The final checkpoint cannot be selected merely because training ended.",
        suggested_fix="Enable early stopping and forbid an always-final selection policy.",
    )
    selection_weights = _mapping(dynamics_plan.get("checkpoint_selection_weights"))
    gate.check(
        "DYN-003",
        selection_weights == {
            "compile": 0.40,
            "hidden_tests": 0.40,
            "validation_loss": 0.20,
        },
        observed=selection_weights,
        expected={"compile": 0.40, "hidden_tests": 0.40, "validation_loss": 0.20},
        evidence="training_dynamics_plan.checkpoint_selection_weights",
        reason="Loss alone cannot select a checkpoint under the execution-aware policy.",
        suggested_fix="Use the exact frozen 40/40/20 compile, hidden-test, and validation-loss weights.",
    )


def _check_post_generation(bundle: dict[str, Any], subject_path: Path, gate: Gate) -> None:
    plan = _mapping(bundle.get("generation_plan"))
    total = _integer(plan.get("authorized_task_count"), 0)
    receipts = [_mapping(item) for item in _list(bundle.get("task_receipts"))]
    task_ids = [item.get("task_id") for item in receipts]
    duplicate_ids = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
    gate.check(
        "V4G-100",
        len(receipts) == total
        and len(set(task_ids)) == total
        and all(isinstance(task_id, str) and task_id for task_id in task_ids),
        observed={"expected": total, "actual": len(receipts), "duplicate_ids": duplicate_ids},
        expected="one unique proof receipt per authorized task",
        evidence="task_receipts",
        reason="Aggregate counts cannot prove that every generated task passed.",
        suggested_fix="Produce one digest-bound receipt for every generated task ID.",
    )

    failing_tasks: dict[str, list[str]] = {}
    role_counts: dict[str, int] = {}
    action_counts: dict[str, int] = {}
    starter_counts: dict[str, int] = {}
    header_mode_counts: dict[str, int] = {}
    api_capability_counts = {name: 0 for name in API_CAPABILITIES}
    repair_type_counts = {name: 0 for name in REPAIR_TYPES}
    editable_layout_counts = {
        "cpp_only": 0,
        "header_only": 0,
        "header_and_cpp": 0,
        "multi_file_gt2": 0,
    }
    for receipt in receipts:
        task_id = str(receipt.get("task_id"))
        failed = [field for field in TASK_PROOF_FIELDS if receipt.get(field) is not True]
        if _number(receipt.get("weighted45"), -1.0) != 1.0:
            failed.append("weighted45")
        if not _is_sha256(receipt.get("oracle_receipt_sha256")):
            failed.append("oracle_receipt_sha256")
        if receipt.get("private_test_output_disclosed") is not False:
            failed.append("private_test_output_disclosed")
        if receipt.get("requires_public_api_change") is True and receipt.get("existing_header_changed") is not True:
            failed.append("existing_header_changed")
        if receipt.get("role") == "repair_trajectory":
            for field in (
                "genuine_four_turn_structure_passed",
                "failing_candidate_receipt_bound",
                "corrected_candidate_receipt_bound",
                "feedback_policy_match_passed",
            ):
                if receipt.get(field) is not True:
                    failed.append(field)
        if receipt.get("role") == "calibration" and receipt.get("task_type") != "calibration":
            failed.append("task_type")
        starter = receipt.get("starter_type")
        header_mode = receipt.get("header_mode")
        layout = receipt.get("editable_layout")
        capabilities = set(_list(receipt.get("api_capabilities")))
        repair_types = set(_list(receipt.get("repair_types")))
        if starter not in STARTER_TARGETS:
            failed.append("starter_type")
        if header_mode not in HEADER_MODES:
            failed.append("header_mode")
        if layout not in {"cpp_only", "header_only", "header_and_cpp"}:
            failed.append("editable_layout")
        if not capabilities or not capabilities <= API_CAPABILITIES:
            failed.append("api_capabilities")
        if receipt.get("role") == "repair_trajectory" and (
            not repair_types or not repair_types <= REPAIR_TYPES
        ):
            failed.append("repair_types")
        if failed:
            failing_tasks[task_id] = sorted(set(failed))
        role = receipt.get("role")
        action = receipt.get("action_topology")
        if isinstance(role, str):
            role_counts[role] = role_counts.get(role, 0) + 1
        if isinstance(action, str):
            action_counts[action] = action_counts.get(action, 0) + 1
        if isinstance(starter, str):
            starter_counts[starter] = starter_counts.get(starter, 0) + 1
        if isinstance(header_mode, str):
            header_mode_counts[header_mode] = header_mode_counts.get(header_mode, 0) + 1
        if isinstance(layout, str) and layout in editable_layout_counts:
            editable_layout_counts[layout] += 1
        if receipt.get("multi_file_gt2") is True:
            editable_layout_counts["multi_file_gt2"] += 1
        for capability in capabilities & API_CAPABILITIES:
            api_capability_counts[capability] += 1
        for repair_type in repair_types & REPAIR_TYPES:
            repair_type_counts[repair_type] += 1
    gate.check(
        "V4G-101",
        not failing_tasks,
        observed={"failing_count": len(failing_tasks), "sample": dict(list(failing_tasks.items())[:20])},
        expected="all per-task API/oracle/grader/safety/application proofs pass",
        evidence="task_receipts",
        reason="A generated task cannot self-certify or borrow another task's proof.",
        suggested_fix="Repair the owning generator, regenerate the task, and rerun every proof.",
    )
    gate.check(
        "V4G-102",
        role_counts == _mapping(plan.get("role_counts"))
        and action_counts == _mapping(_mapping(plan.get("action_counts")).get("action_shapes")),
        observed={"roles": role_counts, "actions": action_counts},
        expected={
            "roles": _mapping(plan.get("role_counts")),
            "actions": _mapping(_mapping(plan.get("action_counts")).get("action_shapes")),
        },
        evidence="task_receipts recomputed composition",
        reason="The selected task bytes must realize the predeclared mixture and action topology.",
        suggested_fix="Reconcile or regenerate the selected manifest; do not hand-edit counts.",
    )

    planned_repair_types = _mapping(_mapping(plan.get("repair_plan")).get("repair_type_counts"))
    composition_matches = (
        starter_counts == _mapping(plan.get("starter_type_counts"))
        and header_mode_counts == _mapping(plan.get("header_mode_counts"))
        and api_capability_counts == _mapping(plan.get("api_capability_counts"))
        and repair_type_counts == planned_repair_types
        and editable_layout_counts == _mapping(plan.get("editable_layout_counts"))
    )
    gate.check(
        "ADM-004",
        composition_matches,
        observed={
            "starter_type_counts": starter_counts,
            "header_mode_counts": header_mode_counts,
            "api_capability_counts": api_capability_counts,
            "repair_type_counts": repair_type_counts,
            "editable_layout_counts": editable_layout_counts,
        },
        expected={
            "starter_type_counts": _mapping(plan.get("starter_type_counts")),
            "header_mode_counts": _mapping(plan.get("header_mode_counts")),
            "api_capability_counts": _mapping(plan.get("api_capability_counts")),
            "repair_type_counts": planned_repair_types,
            "editable_layout_counts": _mapping(plan.get("editable_layout_counts")),
        },
        evidence="task_receipts content-derived curriculum composition",
        reason="Metadata totals cannot substitute for the exact generated task composition.",
        suggested_fix="Regenerate or reconcile task receipts from exact task bytes.",
    )

    receipt = _load_json_binding(
        gate,
        subject_path,
        bundle.get("post_generation_uniqueness_receipt"),
        rule_id="V4G-103.01",
        label="post-generation repository-wide uniqueness receipt",
    )
    _check_zero_match_receipt(gate, receipt, rule_id="V4G-103.02", evidence="post-generation uniqueness")


def _check_pre_training(bundle: dict[str, Any], gate: Gate) -> None:
    plan = _mapping(bundle.get("generation_plan"))
    total = _integer(plan.get("authorized_task_count"), 0)
    receipts = [_mapping(item) for item in _list(bundle.get("serialization_receipts"))]
    task_ids = [item.get("task_id") for item in receipts]
    failures: dict[str, list[str]] = {}
    for receipt in receipts:
        failed = [field for field in SERIALIZATION_PROOF_FIELDS if receipt.get(field) is not True]
        if not _is_sha256(receipt.get("token_ids_sha256")):
            failed.append("token_ids_sha256")
        if not _is_sha256(receipt.get("loss_mask_sha256")):
            failed.append("loss_mask_sha256")
        if failed:
            failures[str(receipt.get("task_id"))] = sorted(set(failed))
    gate.check(
        "V4G-200",
        len(receipts) == total and len(set(task_ids)) == total and not failures,
        observed={"expected": total, "actual": len(receipts), "failures": dict(list(failures.items())[:20])},
        expected="one fully passing serialization receipt per selected task",
        evidence="serialization_receipts",
        reason="The exact loss-bearing representation must pass, not a neighboring reference solution.",
        suggested_fix="Regenerate with the production tokenizer/template/parser and revalidate every row.",
    )

    corpus = _mapping(bundle.get("corpus_admission"))
    corpus_ok = (
        corpus.get("all_task_receipts_reconciled") is True
        and corpus.get("all_serialization_receipts_reconciled") is True
        and _integer(corpus.get("duplicate_count")) == 0
        and _integer(corpus.get("heldout_collision_count")) == 0
        and _integer(corpus.get("semantic_ambiguity_count")) == 0
        and _integer(corpus.get("ancestor_correction_coexistence_count")) == 0
        and _integer(corpus.get("unresolved_review_count")) == 0
        and corpus.get("baseline3_status") == "passed"
        and corpus.get("validator_v2_batch_status") == "batch_v2_analyzed"
        and _is_sha256(corpus.get("selected_manifest_sha256"))
        and _is_sha256(corpus.get("train_jsonl_sha256"))
    )
    gate.check(
        "V4G-201",
        corpus_ok,
        observed=corpus,
        expected="reconciled zero-collision Baseline-3 corpus with V2 batch analysis",
        evidence="corpus_admission",
        reason="Task-level oracle success does not establish corpus or serialized-data admission.",
        suggested_fix="Resolve lineage/collisions, rerun V1 Baseline 3, and reconcile V2 batch analysis.",
    )


    gate.check(
        "BASE-001",
        _number(corpus.get("baseline1_score"), -1.0) >= 90.0,
        observed=corpus.get("baseline1_score"),
        expected="structural baseline >=90",
        evidence="corpus_admission.baseline1_score",
        reason="JSON, metadata, compile evidence, and receipts must clear the structural baseline.",
        suggested_fix="Repair structural failures and recompute Baseline 1.",
    )

    baseline2_ok = (
        _number(corpus.get("baseline2_score"), -1.0) >= 95.0
        and _number(corpus.get("critical_rule_pass_fraction"), -1.0) == 1.0
        and _number(corpus.get("major_rule_pass_fraction"), -1.0) >= 0.98
        and _number(corpus.get("minor_rule_pass_fraction"), -1.0) >= 0.95
        and _number(corpus.get("repair_coverage"), -1.0) >= 0.20
        and _number(corpus.get("calibration_coverage"), -1.0) >= 0.05
        and _number(corpus.get("duplicate_risk"), 1.0) < 0.02
        and _number(corpus.get("generalization_risk_score"), 1.0) <= 0.30
        and _integer(corpus.get("curriculum_drift_count"), -1) == 0
        and corpus.get("training_admission_status") == "passed"
    )
    gate.check(
        "BASE-002",
        baseline2_ok,
        observed=corpus,
        expected={
            "baseline2": ">=95",
            "critical": "100%",
            "major": ">=98%",
            "minor": ">=95%",
            "repair": ">=20%",
            "calibration": ">=5%",
            "duplicate_risk": "<2%",
            "generalization_risk": "<=0.30",
            "curriculum_drift": 0,
            "training_admission_status": "passed",
        },
        evidence="corpus_admission",
        reason="Task validity alone does not establish curriculum or training admission.",
        suggested_fix="Rebuild the mixture and rerun curriculum and admission analysis.",
    )

    shape = _mapping(bundle.get("dataset_shape_receipt"))
    actual_histograms = _mapping(shape.get("histograms"))
    missing_actual_histograms = sorted(
        name for name in DATASET_SHAPE_HISTOGRAMS if not _mapping(actual_histograms.get(name))
    )
    shape_ok = (
        shape.get("status") == "passed"
        and not missing_actual_histograms
        and _list(shape.get("families_below_minimum")) == []
        and _is_sha256(shape.get("receipt_sha256"))
    )
    gate.check(
        "SHAPE-002",
        shape_ok,
        observed={
            "status": shape.get("status"),
            "missing_histograms": missing_actual_histograms,
            "families_below_minimum": shape.get("families_below_minimum"),
        },
        expected="complete actual dataset histograms, no deficient family, digest-bound receipt",
        evidence="dataset_shape_receipt",
        reason="The materialized corpus must realize the planned dataset shape.",
        suggested_fix="Recompute shape from exact selected rows and repair every deficient family.",
    )

    predictor = _mapping(bundle.get("api_failure_predictor"))
    predictor_ok = (
        predictor.get("status") == "passed"
        and predictor.get("deterministic") is True
        and _integer(predictor.get("task_count"), -1) == total
        and _number(predictor.get("api_reconstruction_score"), -1.0) >= 0.97
        and _number(predictor.get("predicted_api_failure_risk"), 1.0) <= 0.03
        and _is_sha256(predictor.get("method_sha256"))
        and _is_sha256(predictor.get("receipt_sha256"))
    )
    gate.check(
        "API-PRED-001",
        predictor_ok,
        observed=predictor,
        expected="deterministic score >=0.97 and predicted API failure risk <=0.03 for every selected task",
        evidence="api_failure_predictor",
        reason="The 264 API-exposure failures require a pre-training predictive gate.",
        suggested_fix="Repair low-scoring rows and rerun the frozen API reconstruction predictor.",
    )


def _check_promotion(bundle: dict[str, Any], gate: Gate) -> None:
    canary = _mapping(bundle.get("canary_result"))
    canary_ok = (
        canary.get("status") == "passed"
        and _integer(canary.get("task_count")) == 20
        and _integer(canary.get("epochs_run")) == 5
        and _integer(canary.get("evaluation_rows_logged")) > 0
        and _number(canary.get("mean_pass_at_1_drop_tasks"), 99.0) <= 1.0
        and _number(canary.get("public_api_absent_increase_pp"), 99.0) <= 2.0
        and _integer(canary.get("contamination_count")) == 0
        and _integer(canary.get("malformed_output_count")) == 0
        and _integer(canary.get("infrastructure_failure_count")) == 0
        and _number(canary.get("context_exhaustion_fraction"), 1.0) <= 0.01
        and canary.get("all_required_action_topologies_observed") is True
        and _is_sha256(canary.get("receipt_sha256"))
    )
    gate.check(
        "V4G-300",
        canary_ok,
        observed=canary,
        expected="passing bounded canary within every predeclared stop threshold",
        evidence="canary_result",
        reason="A failed or missing canary must stop the full training run.",
        suggested_fix="Reject the mixture, repair the causal data gap, and rerun a fresh canary.",
    )

    promotion = _mapping(bundle.get("promotion_result"))
    promotion_ok = (
        promotion.get("evaluation_health_passed") is True
        and promotion.get("matched_previous_attempt_ledger") is True
        and promotion.get("transition_matrix_complete") is True
        and promotion.get("primary_metric_passed") is True
        and promotion.get("regression_budget_passed") is True
        and promotion.get("compile_reachability_not_regressed") is True
        and promotion.get("public_api_completeness_not_regressed") is True
        and promotion.get("feedback_policy_match_passed") is True
        and promotion.get("decision") == "promote"
        and _is_sha256(promotion.get("receipt_sha256"))
    )
    gate.check(
        "V4G-301",
        promotion_ok,
        observed=promotion,
        expected="matched, reproducible promotion evidence with no API/compile regression",
        evidence="promotion_result",
        reason="Training completion or low loss cannot promote a checkpoint.",
        suggested_fix="Produce matched task transitions under the frozen evaluation and feedback contracts.",
    )


    metric_rules = (
        ("PROM-001", "compile_rate", lambda value: value >= 0.98, ">=0.98"),
        ("PROM-002", "link_rate", lambda value: value >= 0.98, ">=0.98"),
        ("PROM-003", "api_exposure_rate", lambda value: value >= 0.97, ">=0.97"),
        ("PROM-004", "semantic_failure_rate", lambda value: value <= 0.05, "<=0.05"),
        ("PROM-005", "runtime_failure_rate", lambda value: value <= 0.01, "<=0.01"),
        ("PROM-006", "header_reconstruction_rate", lambda value: value >= 0.95, ">=0.95"),
    )
    for rule_id, field, predicate, expected in metric_rules:
        value = _number(promotion.get(field), -1.0)
        gate.check(
            rule_id,
            predicate(value),
            observed=value,
            expected=expected,
            evidence=f"promotion_result.{field}",
            reason=f"Checkpoint promotion requires the frozen {field} threshold.",
            suggested_fix="Reject the checkpoint, repair the curriculum, and rerun a matched canary.",
        )

    previous_pass_at_1 = _number(promotion.get("previous_mean_pass_at_1"), -1.0)
    candidate_pass_at_1 = _number(promotion.get("candidate_mean_pass_at_1"), -1.0)
    gate.check(
        "PROM-007",
        previous_pass_at_1 >= 0.0 and candidate_pass_at_1 > previous_pass_at_1,
        observed={"previous": previous_pass_at_1, "candidate": candidate_pass_at_1},
        expected="candidate mean Pass@1 strictly greater than previous checkpoint",
        evidence="promotion_result matched Pass@1",
        reason="A checkpoint that does not improve the previous checkpoint cannot be promoted.",
        suggested_fix="Reject the checkpoint and revise the data hypothesis.",
    )
    gate.check(
        "PROM-008",
        _integer(promotion.get("evaluation_rows_logged"), -1) > 0,
        observed=promotion.get("evaluation_rows_logged"),
        expected=">0",
        evidence="promotion_result.evaluation_rows_logged",
        reason="A run with zero evaluation rows provides no promotion evidence.",
        suggested_fix="Run and log the frozen evaluation protocol at every checkpoint.",
    )
    gate.check(
        "PROM-009",
        promotion.get("shadow_validation_passed") is True
        and promotion.get("generalization_shadow_passed") is True
        and _number(promotion.get("shadow_compile_rate"), -1.0) >= 0.98
        and _number(promotion.get("shadow_hidden_test_pass_rate"), -1.0) >= 0.90,
        observed={
            "shadow_validation_passed": promotion.get("shadow_validation_passed"),
            "generalization_shadow_passed": promotion.get("generalization_shadow_passed"),
            "compile_rate": promotion.get("shadow_compile_rate"),
            "hidden_test_pass_rate": promotion.get("shadow_hidden_test_pass_rate"),
        },
        expected="matched unseen shadow validation passes with compile >=0.98 and hidden tests >=0.90",
        evidence="promotion_result shadow evaluation",
        reason="Training loss and in-distribution tests do not establish generalization.",
        suggested_fix="Run the frozen unseen shadow suite and reject any failing checkpoint.",
    )

    dynamics = _mapping(bundle.get("training_dynamics_result"))
    checkpoint_logs = [_mapping(item) for item in _list(dynamics.get("checkpoints"))]
    checkpoint_log_failures = [
        index
        for index, item in enumerate(checkpoint_logs)
        if _integer(item.get("step"), -1) < 0
        or not all(
            isinstance(item.get(field), (int, float)) and not isinstance(item.get(field), bool)
            for field in (
                "training_loss",
                "validation_loss",
                "compile_rate",
                "hidden_test_rate",
            )
        )
    ]
    dynamics_ok = (
        dynamics.get("status") == "passed"
        and bool(checkpoint_logs)
        and not checkpoint_log_failures
        and dynamics.get("all_checkpoints_logged") is True
        and dynamics.get("early_stopping_applied") is True
        and dynamics.get("selection_policy") == "best_composite_not_always_final"
        and dynamics.get("selected_checkpoint_reason") == "best_composite"
        and isinstance(dynamics.get("selected_checkpoint_id"), str)
        and bool(dynamics.get("selected_checkpoint_id"))
        and _is_sha256(dynamics.get("receipt_sha256"))
    )
    gate.check(
        "DYN-004",
        dynamics_ok,
        observed={
            "status": dynamics.get("status"),
            "checkpoint_count": len(checkpoint_logs),
            "invalid_checkpoint_indexes": checkpoint_log_failures,
            "early_stopping_applied": dynamics.get("early_stopping_applied"),
            "selection_policy": dynamics.get("selection_policy"),
        },
        expected="complete per-checkpoint execution-aware logs, early stopping, and best-composite selection",
        evidence="training_dynamics_result",
        reason="The final checkpoint cannot be selected solely because training ended.",
        suggested_fix="Log every checkpoint and select with the frozen 40/40/20 policy.",
    )

    exposure = _mapping(bundle.get("exposure_plan"))
    gate.check(
        "EXP-001",
        _number(promotion.get("observed_anchor_effective_exposure"), -1.0)
        == _number(exposure.get("planned_anchor_effective_exposure"), -2.0),
        observed={
            "planned": exposure.get("planned_anchor_effective_exposure"),
            "observed": promotion.get("observed_anchor_effective_exposure"),
        },
        expected="planned and observed anchor effective exposure are exactly equal",
        evidence="exposure_plan and promotion_result",
        reason="Silent exposure drift previously halved the successful anchor contribution.",
        suggested_fix="Reject the run and restore the exact frozen sampler/exposure plan.",
    )

    score = _mapping(bundle.get("promotion_score"))
    score_weights = _mapping(score.get("weights"))
    component_scores = _mapping(score.get("component_scores"))
    computed_score = sum(
        _number(component_scores.get(name), -1000.0) * weight
        for name, weight in PROMOTION_SCORE_WEIGHTS.items()
    )
    score_ok = (
        score_weights == PROMOTION_SCORE_WEIGHTS
        and set(component_scores) == set(PROMOTION_SCORE_WEIGHTS)
        and all(0.0 <= _number(component_scores.get(name), -1.0) <= 100.0 for name in PROMOTION_SCORE_WEIGHTS)
        and abs(_number(score.get("computed_score"), -1.0) - computed_score) <= 1e-9
        and computed_score >= 95.0
        and score.get("critical_gates_all_passed") is True
    )
    gate.check(
        "SCORE-001",
        score_ok,
        observed={"declared": score.get("computed_score"), "recomputed": computed_score, "weights": score_weights},
        expected={"minimum": 95.0, "weights": PROMOTION_SCORE_WEIGHTS, "critical_gates_all_passed": True},
        evidence="promotion_score",
        reason="The composite score is an additional promotion threshold, never an override for a critical failure.",
        suggested_fix="Fix every critical gate, then recompute the frozen weighted score.",
    )

    corpus = _mapping(bundle.get("corpus_admission"))
    baseline3_ok = (
        promotion.get("baseline3_deployment_status") == "passed"
        and _number(promotion.get("critical_rule_pass_fraction"), -1.0) == 1.0
        and _number(promotion.get("major_rule_pass_fraction"), -1.0) >= 0.98
        and _number(promotion.get("minor_rule_pass_fraction"), -1.0) >= 0.95
        and _number(promotion.get("duplicate_risk"), 1.0) < 0.02
        and _number(promotion.get("generalization_risk_score"), 1.0) <= 0.30
        and _integer(promotion.get("curriculum_drift_count"), -1) == 0
        and _number(corpus.get("repair_coverage"), -1.0) >= 0.20
        and _number(corpus.get("calibration_coverage"), -1.0) >= 0.05
    )
    gate.check(
        "BASE-003",
        baseline3_ok,
        observed=promotion,
        expected="all strengthened Baseline 3 deployment thresholds pass",
        evidence="promotion_result and corpus_admission",
        reason="Deployment Baseline 3 is conjunctive; no aggregate score can mask a failed threshold.",
        suggested_fix="Reject promotion and remediate the specific failed baseline component.",
    )


def _check_deployment(bundle: dict[str, Any], gate: Gate) -> None:
    deployment = _mapping(bundle.get("deployment_certification"))
    required_true = (
        "promotion_receipt_verified",
        "consumer_verification_passed",
        "artifact_manifest_complete",
        "model_card_complete",
        "rollback_plan_complete",
        "monitoring_plan_complete",
        "security_review_passed",
        "reproducibility_passed",
    )
    missing = sorted(field for field in required_true if deployment.get(field) is not True)
    deployment_ok = (
        deployment.get("status") == "certified"
        and deployment.get("decision") == "deploy"
        and not missing
        and _is_sha256(deployment.get("promotion_receipt_sha256"))
        and _is_sha256(deployment.get("artifact_manifest_sha256"))
        and _is_sha256(deployment.get("receipt_sha256"))
    )
    gate.check(
        "DEP-001",
        deployment_ok,
        observed={"status": deployment.get("status"), "decision": deployment.get("decision"), "missing": missing},
        expected="digest-bound local deployment certification with consumer, rollback, monitoring, security, and reproducibility proof",
        evidence="deployment_certification",
        reason="Checkpoint promotion does not itself authorize deployment.",
        suggested_fix="Complete the deployment evidence bundle; do not claim organizational signing from this local receipt.",
    )


def validate_bundle(bundle: dict[str, Any], subject_path: Path, stage: str) -> dict[str, Any]:
    gate = Gate()
    _check_common(bundle, subject_path, gate)
    if STAGE_ORDER[stage] >= STAGE_ORDER["post-generation"]:
        _check_post_generation(bundle, subject_path, gate)
    if STAGE_ORDER[stage] >= STAGE_ORDER["pre-training"]:
        _check_pre_training(bundle, gate)
    if STAGE_ORDER[stage] >= STAGE_ORDER["promotion"]:
        _check_promotion(bundle, gate)
    if STAGE_ORDER[stage] >= STAGE_ORDER["deployment"]:
        _check_deployment(bundle, gate)

    failures = [finding for finding in gate.findings if not finding.passed]
    subject_sha256 = hashlib.sha256(
        json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": RECEIPT_VERSION,
        "policy_version": POLICY_VERSION,
        "stage": stage,
        "subject_path": str(subject_path.resolve()),
        "subject_sha256": subject_sha256,
        "decision": "PASS" if not failures else "FAIL",
        "hard_failure_ids": [finding.rule_id for finding in failures],
        "passed_rule_count": len(gate.findings) - len(failures),
        "failed_rule_count": len(failures),
        "rules": [asdict(finding) for finding in gate.findings],
        "next_action": (
            "authorized_for_stage_transition"
            if not failures
            else "stop_not_completed_repair_evidence_and_rerun"
        ),
    }


def _rule_catalog() -> list[dict[str, str]]:
    return [
        {"range": "V4G-000..015", "purpose": "schema, iteration contract, exact failure evidence"},
        {"range": "V4G-020..031", "purpose": "role/action/source/repair/feedback plan"},
        {"range": "V4G-040..050", "purpose": "global uniqueness and proof-plan authorization"},
        {"range": "ID-000..003", "purpose": "atomic batch-code, task-ID, and slot reservation"},
        {"range": "V4G-060..080", "purpose": "source bytes, serialization, exposure, canary plan"},
        {"range": "V4G-100..103", "purpose": "per-task generated proof and post-generation uniqueness"},
        {"range": "V4G-200..201", "purpose": "exact SFT serialization and corpus admission"},
        {"range": "V4G-300..301", "purpose": "legacy canary and matched checkpoint promotion"},
        {"range": "ADM-001..004", "purpose": "editable layout, API capability, starter, and receipt-derived admission"},
        {"range": "CURR-101..103", "purpose": "repair ratio, subtype coverage, and feedback sanitation"},
        {"range": "CAL/HDR/SHAPE", "purpose": "calibration, header balance, and dataset-shape gates"},
        {"range": "API-PRED-001", "purpose": "deterministic pre-training API failure predictor"},
        {"range": "CAN/DYN/EXP", "purpose": "20-task canary, training dynamics, and exact exposure"},
        {"range": "PROM-001..009", "purpose": "absolute checkpoint promotion thresholds"},
        {"range": "SCORE/BASE", "purpose": "non-overriding score and strengthened baselines"},
        {"range": "DEP-001", "purpose": "local deployment certification"},
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="V4 admission bundle JSON")
    parser.add_argument("--output", type=Path, help="write the validation receipt here")
    parser.add_argument("--stage", choices=tuple(STAGE_ORDER), default="pre-generation")
    parser.add_argument("--list-rules", action="store_true")
    args = parser.parse_args(argv)

    if args.list_rules:
        print(json.dumps(_rule_catalog(), indent=2))
        return 0
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --list-rules is used")

    try:
        bundle = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"failed to read admission bundle: {exc}", file=sys.stderr)
        return 1
    if not isinstance(bundle, dict):
        print("admission bundle must be a JSON object", file=sys.stderr)
        return 1

    receipt = validate_bundle(bundle, args.input, args.stage)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{receipt['decision']} stage={args.stage} "
        f"passed={receipt['passed_rule_count']} failed={receipt['failed_rule_count']}"
    )
    if receipt["hard_failure_ids"]:
        print("hard failures: " + ", ".join(receipt["hard_failure_ids"]))
    return 0 if receipt["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
