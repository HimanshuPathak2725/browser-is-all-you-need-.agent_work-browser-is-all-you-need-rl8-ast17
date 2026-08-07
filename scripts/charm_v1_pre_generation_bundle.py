#!/usr/bin/env python3
"""Derive the digest-bound CHARM V1 pre-generation admission bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/charm-task-generation-v1/v1-20260803T193513Z"
AUDIT = ROOT / "artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit"
RECOVERED = ROOT / "artifacts/charm-task-generation-v1/recovered-previous-best-20260731"
PREVIOUS_LEDGER = RECOVERED / "failure-ledger/attempt_ledger.csv"
POLICY = ROOT / "dataset/configs/charm-v1-admission-policy.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"bound file missing: {path}")
    return {"path": str(path.resolve()), "sha256": sha256(path)}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"):
        digest.update(path.relative_to(root).as_posix().encode()); digest.update(b"\0")
        digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def evidence() -> tuple[dict[str, int], dict[str, int | str], dict[str, dict[str, str]]]:
    paths = {
        "audit_summary": AUDIT / "AUDIT_SUMMARY.json",
        "detailed_audit": AUDIT / "DETAILED_POSTRUN_AUDIT.md",
        "validator_v4_spec": AUDIT / "VALIDATOR_V4_SPEC.md",
        "mechanism_summary": AUDIT / "failure-ledger/mechanism_summary.json",
        "dataset_shape": AUDIT / "dataset_shape_audit.json",
        "training_dynamics": AUDIT / "training_dynamics_audit.json",
    }
    bindings = {name: bind(path) for name, path in paths.items()}
    summary = read_json(paths["audit_summary"])
    mechanisms = read_json(paths["mechanism_summary"])
    shape = read_json(paths["dataset_shape"])
    dynamics = read_json(paths["training_dynamics"])
    primary = summary["primary_findings"]
    profile = {name: int(primary[name]) for name in (
        "actual_attempts", "failed_attempts", "compile_or_link_failures",
        "public_api_absent_or_misnamed_failures", "semantic_counterexamples",
        "runtime_failures", "existing_header_change_rows",
        "genuine_repair_trajectory_rows", "calibration_rows",
    )}
    compile_sum = sum(int(mechanisms["failed_attempt_counts"].get(name, 0)) for name in (
        "candidate-internal-compile-error", "missing-required-standard-header",
        "public-api-absent-or-misnamed", "warning-as-error",
    ))
    if compile_sum != profile["compile_or_link_failures"]:
        raise RuntimeError("compile/link findings do not reconcile")
    if mechanisms["attempts"] != profile["actual_attempts"] or mechanisms["failed_attempts"] != profile["failed_attempts"]:
        raise RuntimeError("attempt findings do not reconcile")
    if shape["existing_scaffold_actions"]["rows_changing_existing_header"] != profile["existing_header_change_rows"]:
        raise RuntimeError("header action findings do not reconcile")
    if shape["repair_supervision"]["genuine_failed_candidate_to_feedback_to_correction_rows"] != profile["genuine_repair_trajectory_rows"]:
        raise RuntimeError("repair findings do not reconcile")
    if shape["actual_mixture_projection"]["calibration_or_no_change_rows"] != profile["calibration_rows"]:
        raise RuntimeError("calibration findings do not reconcile")
    if dynamics["eval_rows_logged"] != 0:
        raise RuntimeError("failure profile unexpectedly has training-time eval rows")

    with (AUDIT / "failure-ledger/attempt_ledger.csv").open(newline="", encoding="utf-8") as handle:
        attempts = list(csv.DictReader(handle))
    invalid = sum(row["evidence_confidence"] != "direct" for row in attempts)
    known_stages = {"compile-or-link", "pass", "semantic-counterexample", "runtime-or-sanitizer"}
    unresolved = sum(row["failure_stage"] not in known_stages for row in attempts)
    consistency = read_json(AUDIT / "receipt_consistency_audit.json")
    recovery = read_json(RECOVERED / "RECOVERY_RECEIPT.json")
    recovery_ok = (
        recovery.get("decision") == "PASS"
        and recovery.get("ledger", {}).get("attempt_ledger_csv_sha256") == sha256(PREVIOUS_LEDGER)
        and recovery.get("historical_score_reconciliation", {}).get("decision") == "PASS"
    )
    unauthorized = 0 if consistency.get("all_consistent") is True and recovery_ok else 1
    health: dict[str, int | str] = {
        "status": "valid" if invalid == unresolved == unauthorized == 0 else "invalid",
        "invalid_evidence_count": invalid,
        "unresolved_diagnosis_count": unresolved,
        "unauthorized_disposition_count": unauthorized,
    }
    return profile, health, bindings


def previous_best() -> tuple[str, list[str]]:
    ledger_hash = sha256(PREVIOUS_LEDGER)
    with PREVIOUS_LEDGER.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 104 or len({(row["run_id"], row["testcase"], row["attempt"]) for row in rows}) != 104:
        raise RuntimeError("previous-best ledger is not the reconciled 4x26 set")
    return ledger_hash, sorted({row["run_id"] for row in rows})


def build(
    *,
    generation_plan: Path,
    uniqueness_receipt: Path,
    batch_code_receipt: Path,
    reservation_plan: Path,
    reservation_receipt: Path,
    oracle_source_manifest: Path,
    dependency_preflight: Path,
    proposal_plan: Path | None = None,
    builder_source: Path | None = None,
    uniqueness_scanner_source: Path | None = None,
) -> dict[str, Any]:
    policy = read_json(POLICY)
    if policy.get("schema_version") != "charm-v1-admission-policy-v1":
        raise RuntimeError("unexpected admission policy")
    authority = policy["authority"]
    if authority["training"] is not False or authority["canary_execution"] is not False:
        raise RuntimeError("generation trigger cannot authorize training/canary execution")
    profile, health, failure_bindings = evidence()
    ledger_hash, previous_runs = previous_best()
    plan = read_json(generation_plan)
    audit_tree = ROOT / "updated task/audit-sft-data-quality"
    source_paths = {
        "builder_source": builder_source if builder_source is not None else ROOT / ".agents/skills/charm-skill/scripts/build_v1_tasks.py",
        "verifier_source": oracle_source_manifest,
        "eval_wrapper_source": ROOT / "examples/modal/aider_sft_eval_app.py",
        "feedback_policy": ROOT / "scripts/charm_v1_redacted_feedback.py",
        "tokenizer_manifest": ROOT / "dataset/configs/glm47-flash-tokenizer-manifest.json",
        "chat_template": ROOT / "dataset/configs/glm47-flash-chat-template.jinja",
        "heldout_manifest": ROOT / "dataset/configs/fixed26-heldout-manifest.json",
        "batch_code_reserver_source": ROOT / ".agents/skills/charm-skill/scripts/reserve_batch_code.py",
        "task_id_reserver_source": ROOT / ".agents/skills/charm-skill/scripts/reserve_v1_task_ids.py",
        "uniqueness_scanner_source": uniqueness_scanner_source if uniqueness_scanner_source is not None else ROOT / "scripts/charm_v1_repository_uniqueness_v5.py",
    }
    sources = {name: bind(path) for name, path in source_paths.items()}
    iteration = policy["iteration"]
    return {
        "schema_version": "charm-generator-admission-v4.1",
        "policy_version": policy["policy_version"], "example_only": False,
        "iteration_contract": {
            "iteration_id": plan["generation_batch_id"], **iteration,
            "previous_best_run_ids": previous_runs,
            "previous_best_attempt_ledger_sha256": ledger_hash,
            "feedback_policy_id": policy["feedback_policy_id"],
        },
        "failure_evidence": {
            **health,
            "profile": {"profile_id": AUDIT.parent.name, "counts": profile},
            "artifact_bindings": failure_bindings,
            "receipt_consistency_binding": bind(AUDIT / "receipt_consistency_audit.json"),
            "previous_best_recovery_binding": bind(RECOVERED / "RECOVERY_RECEIPT.json"),
        },
        "audit_skill_tree": {"path": str(audit_tree.resolve()), "sha256": tree_sha256(audit_tree)},
        "generation_plan": plan,
        "feedback_policy": {
            "policy_id": policy["feedback_policy_id"],
            "policy_sha256": sources["feedback_policy"]["sha256"],
            "private_test_output_disclosed": False,
            "separate_full_private_diagnostic_lane": True,
            "repair_training_matches_promotion_policy": True,
            "sanitized": True, "maximum_feedback_lines": 100,
            "hidden_answers_disclosed": False, "expected_outputs_disclosed": False,
            "private_test_names_disclosed": False,
        },
        "generation_plan_binding": bind(generation_plan),
        **({"proposal_plan_binding": bind(proposal_plan)} if proposal_plan is not None else {}),
        "dependency_preflight": bind(dependency_preflight),
        "uniqueness_receipt": bind(uniqueness_receipt),
        "batch_code_reservation_receipt": bind(batch_code_receipt),
        "task_id_reservation_plan": bind(reservation_plan),
        "task_id_reservation_receipt": bind(reservation_receipt),
        "proof_plan": policy["proof_plan"], "source_bindings": sources,
        "serialization_plan": policy["serialization_plan"],
        "exposure_plan": policy["exposure_plan"],
        "canary_plan": {**policy["canary_plan"], "previous_best_attempt_ledger_sha256": ledger_hash},
        "training_dynamics_plan": policy["training_dynamics_plan"],
        "admission_policy_binding": bind(POLICY),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-plan", required=True, type=Path)
    parser.add_argument("--uniqueness-receipt", required=True, type=Path)
    parser.add_argument("--batch-code-receipt", required=True, type=Path)
    parser.add_argument("--reservation-plan", required=True, type=Path)
    parser.add_argument("--reservation-receipt", required=True, type=Path)
    parser.add_argument("--oracle-source-manifest", required=True, type=Path)
    parser.add_argument("--dependency-preflight", required=True, type=Path)
    parser.add_argument("--proposal-plan", type=Path)
    parser.add_argument("--builder-source", type=Path)
    parser.add_argument("--uniqueness-scanner-source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite admission bundle: {args.output}")
    data = (
        json.dumps(
            build(
                generation_plan=args.generation_plan,
                uniqueness_receipt=args.uniqueness_receipt,
                batch_code_receipt=args.batch_code_receipt,
                reservation_plan=args.reservation_plan,
                reservation_receipt=args.reservation_receipt,
                oracle_source_manifest=args.oracle_source_manifest,
                dependency_preflight=args.dependency_preflight,
                proposal_plan=args.proposal_plan,
                builder_source=args.builder_source,
                uniqueness_scanner_source=args.uniqueness_scanner_source,
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{args.output.name}.", dir=args.output.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary_name, args.output)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    print(hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
