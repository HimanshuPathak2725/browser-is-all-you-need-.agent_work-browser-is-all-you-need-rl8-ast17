from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/charm-skill/scripts/validate_generation_readiness.py"


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("charm_generation_readiness", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, content: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "sha256": _sha(path)}


def _uniqueness(path: Path, proposal_plan_sha256: str | None = None) -> dict[str, str]:
    payload = {
        "decision": "PASS",
        "repository_scope_complete": True,
        "parse_failures": 0,
        "task_id_matches": 0,
        "exact_matches": 0,
        "near_matches": 0,
        "structural_matches": 0,
        "semantic_matches": 0,
        "ambiguous_matches": 0,
        "corpus_index_sha256": hashlib.sha256(b"corpus-index").hexdigest(),
        "proposal_plan_sha256": proposal_plan_sha256 or hashlib.sha256(b"proposal-plan").hexdigest(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return {"path": str(path), "sha256": _sha(path)}


def _reservation(
    tmp_path: Path,
    uniqueness_binding: dict[str, str],
    proposal_plan_sha256: str,
    task_count: int,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    uniqueness = json.loads(Path(uniqueness_binding["path"]).read_text(encoding="utf-8"))
    batch_id = "generation-batch-test"
    session_id = "generation-session-test"
    batch_code = "31415"
    batch_created_at = "2026-08-04T03:15:38Z"
    batch_receipt = {
        "schema_version": VALIDATOR.BATCH_CODE_RESERVATION_RECEIPT_SCHEMA,
        "decision": "PASS",
        "operation": "reserve_batch_code",
        "atomic_lock_acquired": True,
        "registry_reconciled": True,
        "reservation_state": "permanent",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_derivation": VALIDATOR.BATCH_CODE_DERIVATION,
        "historical_alias_only": False,
        "codes_reusable": False,
        "registry_before_sha256": hashlib.sha256(b"batch-registry-before").hexdigest(),
        "registry_after_sha256": hashlib.sha256(b"batch-registry-after").hexdigest(),
        "registry_revision": 1,
    }
    batch_receipt_binding = _write(
        tmp_path / "batch-code-reservation-receipt.json",
        json.dumps(batch_receipt, sort_keys=True, separators=(",", ":")) + "\n",
    )
    claims = [
        {
            "task_id": f"task-{index:02d}",
            "topic": f"topic-{index // 3:02d}",
            "slot_id": str(index % 3 + 1),
            "proposal_sha256": hashlib.sha256(f"proposal-{index}".encode()).hexdigest(),
        }
        for index in range(task_count)
    ]
    plan = {
        "schema_version": VALIDATOR.TASK_ID_PLAN_SCHEMA,
        "protocol_id": "charm-generic",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_receipt_binding["sha256"],
        "proposal_plan_sha256": proposal_plan_sha256,
        "corpus_index_sha256": uniqueness["corpus_index_sha256"],
        "claims": claims,
    }
    plan_binding = _write(
        tmp_path / "task-id-plan.json",
        json.dumps(plan, sort_keys=True, separators=(",", ":")) + "\n",
    )
    slot_keys = [
        f"{batch_id}|{claim['topic']}|{claim['slot_id']}" for claim in claims
    ]
    receipt = {
        "schema_version": VALIDATOR.TASK_ID_RESERVATION_RECEIPT_SCHEMA,
        "decision": "PASS",
        "operation": "reserve",
        "reservation_state": "reserved",
        "atomic_lock_acquired": True,
        "registry_reconciled": True,
        "collision_count": 0,
        "protocol_id": plan["protocol_id"],
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        "generation_batch_code": batch_code,
        "generation_batch_created_at_utc": batch_created_at,
        "batch_code_reservation_receipt_sha256": batch_receipt_binding["sha256"],
        "proposal_plan_sha256": proposal_plan_sha256,
        "corpus_index_sha256": uniqueness["corpus_index_sha256"],
        "reservation_plan_sha256": plan_binding["sha256"],
        "uniqueness_receipt_sha256": uniqueness_binding["sha256"],
        "registry_before_sha256": hashlib.sha256(b"registry-before").hexdigest(),
        "registry_after_sha256": hashlib.sha256(b"registry-after").hexdigest(),
        "registry_revision": 1,
        "claim_count": task_count,
        "created_task_ids": sorted(claim["task_id"] for claim in claims),
        "resumed_task_ids": [],
        "reserved_task_ids": sorted(claim["task_id"] for claim in claims),
        "slot_keys": sorted(slot_keys),
        "idempotent_resume_only_for_same_owner_and_proposal": True,
        "terminal_or_tombstoned_ids_reusable": False,
    }
    receipt_binding = _write(
        tmp_path / "task-id-reservation-receipt.json",
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
    )
    return batch_receipt_binding, plan_binding, receipt_binding


@pytest.fixture
def valid_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], Path]:
    evidence_bindings: dict[str, dict[str, str]] = {}
    expected_hashes: dict[str, str] = {}
    for name in VALIDATOR.REQUIRED_PROFILE_HASHES:
        binding = _write(tmp_path / "evidence" / f"{name}.txt", f"exact {name}\n")
        evidence_bindings[name] = binding
        expected_hashes[name] = binding["sha256"]
    monkeypatch.setattr(VALIDATOR, "REQUIRED_PROFILE_HASHES", expected_hashes)

    audit_skill = tmp_path / "updated task" / "audit-sft-data-quality"
    _write(audit_skill / "SKILL.md", "---\nname: audit-sft-data-quality\ndescription: test\n---\n")
    _write(audit_skill / "references" / "workflow.md", "test workflow\n")
    audit_tree_hash = VALIDATOR.tree_sha256(audit_skill)

    source_bindings = {
        name: _write(tmp_path / "sources" / f"{name}.txt", f"exact {name}\n")
        for name in VALIDATOR.SOURCE_BINDING_NAMES
    }
    feedback_hash = source_bindings["feedback_policy"]["sha256"]
    previous_ledger_hash = hashlib.sha256(b"previous-attempt-ledger").hexdigest()

    bundle: dict[str, Any] = {
        "schema_version": VALIDATOR.SCHEMA_VERSION,
        "policy_version": VALIDATOR.POLICY_VERSION,
        "example_only": False,
        "iteration_contract": {
            "iteration_id": "iteration-v4-test",
            "target_behavior": "increase first-turn public API completeness",
            "observed_failure_hypothesis": "starter/action shortcut",
            "planned_data_intervention": "rebalance API action topology",
            "primary_metric": "mean_pass_at_1_over_4_frozen_trials",
            "promotion_threshold": "improve without regression",
            "stop_condition": "stop on API or pass@1 regression",
            "previous_best_run_ids": ["previous-best-rerun"],
            "previous_best_attempt_ledger_sha256": previous_ledger_hash,
            "authorized_training_diff": ["dataset_mixture"],
            "feedback_policy_id": "redacted-compiler-feedback-v1",
        },
        "failure_evidence": {
            "status": "valid",
            "invalid_evidence_count": 0,
            "unresolved_diagnosis_count": 0,
            "unauthorized_disposition_count": 0,
            "profile": {
                "profile_id": VALIDATOR.FAILURE_PROFILE_ID,
                "counts": dict(VALIDATOR.REQUIRED_PROFILE_COUNTS),
            },
            "artifact_bindings": evidence_bindings,
        },
        "audit_skill_tree": {"path": str(audit_skill), "sha256": audit_tree_hash},
        "generation_plan": {
            "authorized_task_count": 20,
            "role_counts": {
                "direct_verified_success": 11,
                "boundary_case": 4,
                "repair_trajectory": 4,
                "calibration": 1,
            },
            "action_counts": {
                "empty_starter": 4,
                "existing_header_change": 11,
                "header_only_or_template": 2,
                "header_and_source": 9,
                "unparseable": 0,
                "unjustified_noop": 0,
                "action_shapes": {
                    "header_and_source": 9,
                    "header_only_or_template": 2,
                    "source_only": 8,
                    "calibration_no_change": 1,
                },
            },
            "editable_layout_counts": {
                "cpp_only": 8,
                "header_only": 2,
                "header_and_cpp": 10,
                "multi_file_gt2": 2,
            },
            "starter_type_counts": {
                "empty": 4,
                "skeleton": 5,
                "partial_implementation": 4,
                "semantic_bug": 3,
                "compile_bug": 2,
                "near_correct": 2,
            },
            "api_capability_counts": {name: 20 for name in VALIDATOR.API_CAPABILITIES},
            "header_mode_counts": {name: 4 for name in VALIDATOR.HEADER_MODES},
            "dataset_shape_plan": {
                "histograms": {
                    name: {"present": 20} for name in VALIDATOR.DATASET_SHAPE_HISTOGRAMS
                },
                "families_below_minimum": [],
            },
            "families": [
                {
                    "family_id": "test-family",
                    "action_topology_count": 4,
                    "has_existing_scaffold": True,
                }
            ],
            "source_counts": {"verified_non_synthetic": 2, "synthetic": 18},
            "required_mechanism_ids": sorted(VALIDATOR.REQUIRED_MECHANISMS),
            "repair_plan": {
                "genuine_four_turn_suffix_required": True,
                "failing_candidate_receipt_required": True,
                "corrected_candidate_receipt_required": True,
                "metadata_only_rows_count_as_repair": False,
                "planned_genuine_repair_count": 4,
                "repair_type_counts": {name: 4 for name in VALIDATOR.REPAIR_TYPES},
            },
        },
        "feedback_policy": {
            "policy_id": "redacted-compiler-feedback-v1",
            "policy_sha256": feedback_hash,
            "private_test_output_disclosed": False,
            "separate_full_private_diagnostic_lane": True,
            "repair_training_matches_promotion_policy": True,
            "sanitized": True,
            "maximum_feedback_lines": 100,
            "hidden_answers_disclosed": False,
            "expected_outputs_disclosed": False,
            "private_test_names_disclosed": False,
        },
        "uniqueness_receipt": None,
        "task_id_reservation_plan": None,
        "task_id_reservation_receipt": None,
        "proof_plan": {field: True for field in VALIDATOR.PROOF_PLAN_FIELDS},
        "source_bindings": source_bindings,
        "serialization_plan": {
            "exact_token_replay_required": True,
            "exact_loss_mask_required": True,
            "exact_eos_required": True,
            "whole_file_application_replay_required": True,
            "max_unparseable_rows": 0,
            "max_truncated_rows": 0,
            "max_private_leak_rows": 0,
        },
        "exposure_plan": {
            "previous_anchor_effective_exposure": 26000,
            "planned_anchor_effective_exposure": 26000,
            "dilution_explicitly_authorized": False,
            "retention_canary_defined": True,
        },
        "canary_plan": {
            "previous_best_attempt_ledger_sha256": previous_ledger_hash,
            "task_count": 20,
            "epochs_before_decision": 5,
            "evaluation_during_training": True,
            "frozen_trial_count": 4,
            "stop_if_pass_at_1_drop_exceeds_tasks": 1,
            "stop_if_public_api_absent_increase_pp": 2.0,
            "stop_on_contamination": True,
            "stop_on_missing_action_topology": True,
            "max_malformed_outputs": 0,
            "max_infrastructure_failures": 0,
            "max_context_exhaustion_fraction": 0.01,
            "full_training_blocked_until_canary_pass": True,
        },
        "training_dynamics_plan": {
            "log_every_checkpoint": True,
            "require_training_loss": True,
            "require_validation_loss": True,
            "require_compile_rate": True,
            "require_hidden_test_rate": True,
            "early_stopping_enabled": True,
            "selection_policy": "best_composite_not_always_final",
            "checkpoint_selection_weights": {
                "compile": 0.40,
                "hidden_tests": 0.40,
                "validation_loss": 0.20,
            },
        },
    }
    proposal_plan_sha256 = hashlib.sha256(
        json.dumps(bundle["generation_plan"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    bundle["uniqueness_receipt"] = _uniqueness(tmp_path / "uniqueness.json", proposal_plan_sha256)
    (
        bundle["batch_code_reservation_receipt"],
        bundle["task_id_reservation_plan"],
        bundle["task_id_reservation_receipt"],
    ) = _reservation(tmp_path, bundle["uniqueness_receipt"], proposal_plan_sha256, 20)
    subject = tmp_path / "admission.json"
    subject.write_text(json.dumps(bundle), encoding="utf-8")
    return bundle, subject


def _decision(bundle: dict[str, Any], subject: Path, stage: str = "pre-generation") -> dict[str, Any]:
    return VALIDATOR.validate_bundle(bundle, subject, stage)


def test_valid_pre_generation_bundle_passes(valid_bundle: tuple[dict[str, Any], Path]) -> None:
    bundle, subject = valid_bundle
    receipt = _decision(bundle, subject)
    assert receipt["decision"] == "PASS"
    assert receipt["hard_failure_ids"] == []
    assert all(rule["deterministic"] and rule["confidence"] == 1.0 for rule in receipt["rules"])


Mutation = Callable[[dict[str, Any]], None]


def _set_example(bundle: dict[str, Any]) -> None:
    bundle["example_only"] = True


def _remove_ledger(bundle: dict[str, Any]) -> None:
    bundle["iteration_contract"]["previous_best_attempt_ledger_sha256"] = "missing"


def _wrong_profile(bundle: dict[str, Any]) -> None:
    bundle["failure_evidence"]["profile"]["profile_id"] = "wrong-profile"


def _too_many_empty_starters(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["action_counts"]["empty_starter"] = 6


def _remove_header_edits(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["action_counts"]["existing_header_change"] = 0


def _break_role_mix(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["role_counts"] = {
        "direct_verified_success": 20,
        "boundary_case": 0,
        "repair_trajectory": 0,
        "calibration": 0,
    }


def _all_synthetic(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["source_counts"] = {"synthetic": 20}


def _omit_mechanism(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["required_mechanism_ids"].remove("public-api-completeness")


def _leak_private_feedback(bundle: dict[str, Any]) -> None:
    bundle["feedback_policy"]["private_test_output_disclosed"] = True


def _misbind_feedback_policy(bundle: dict[str, Any]) -> None:
    bundle["feedback_policy"]["policy_sha256"] = hashlib.sha256(b"different-policy").hexdigest()


def _fake_repairs(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["repair_plan"]["genuine_four_turn_suffix_required"] = False


def _disable_api_probe(bundle: dict[str, Any]) -> None:
    bundle["proof_plan"]["public_api_probe_required"] = False


def _drop_source_bytes(bundle: dict[str, Any]) -> None:
    bundle["source_bindings"]["eval_wrapper_source"]["path"] = "missing-wrapper.py"


def _dilute_anchors(bundle: dict[str, Any]) -> None:
    bundle["exposure_plan"] = {
        "previous_anchor_effective_exposure": 26000,
        "planned_anchor_effective_exposure": 13000,
        "dilution_explicitly_authorized": False,
        "retention_canary_defined": False,
    }


def _remove_canary_block(bundle: dict[str, Any]) -> None:
    bundle["canary_plan"]["full_training_blocked_until_canary_pass"] = False


def _remove_atomic_id_lock(bundle: dict[str, Any]) -> None:
    receipt_path = Path(bundle["task_id_reservation_receipt"]["path"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["atomic_lock_acquired"] = False
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    bundle["task_id_reservation_receipt"]["sha256"] = _sha(receipt_path)



def _remove_batch_code_lock(bundle: dict[str, Any]) -> None:
    receipt_path = Path(bundle["batch_code_reservation_receipt"]["path"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["atomic_lock_acquired"] = False
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    bundle["batch_code_reservation_receipt"]["sha256"] = _sha(receipt_path)


def _break_editable_layout(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["editable_layout_counts"]["cpp_only"] = 9


def _undercover_api_capability(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["api_capability_counts"]["repair_api"] = 14


def _skew_starter_distribution(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["starter_type_counts"]["empty"] = 6
    bundle["generation_plan"]["starter_type_counts"]["skeleton"] = 3


def _omit_repair_subtype(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["repair_plan"]["repair_type_counts"]["linker_repair"] = 0


def _overshare_feedback(bundle: dict[str, Any]) -> None:
    bundle["feedback_policy"]["maximum_feedback_lines"] = 101


def _unbalance_header_modes(bundle: dict[str, Any]) -> None:
    bundle["generation_plan"]["header_mode_counts"]["frozen"] = 7
    bundle["generation_plan"]["header_mode_counts"]["editable"] = 1


def _drop_shape_histogram(bundle: dict[str, Any]) -> None:
    del bundle["generation_plan"]["dataset_shape_plan"]["histograms"]["api_shape"]


def _disable_early_stopping(bundle: dict[str, Any]) -> None:
    bundle["training_dynamics_plan"]["early_stopping_enabled"] = False



def _change_selection_weights(bundle: dict[str, Any]) -> None:
    bundle["training_dynamics_plan"]["checkpoint_selection_weights"] = {
        "compile": 0.30,
        "hidden_tests": 0.40,
        "validation_loss": 0.30,
    }


@pytest.mark.parametrize(
    ("mutate", "expected_rule"),
    [
        (_set_example, "V4G-002"),
        (_remove_ledger, "V4G-011"),
        (_wrong_profile, "V4G-012"),
        (_too_many_empty_starters, "V4G-021"),
        (_remove_header_edits, "V4G-022"),
        (_break_role_mix, "V4G-020"),
        (_all_synthetic, "V4G-027"),
        (_omit_mechanism, "V4G-028"),
        (_leak_private_feedback, "V4G-030"),
        (_misbind_feedback_policy, "V4G-062"),
        (_fake_repairs, "V4G-031"),
        (_disable_api_probe, "V4G-050"),
        (_drop_source_bytes, "V4G-060.03"),
        (_dilute_anchors, "V4G-070"),
        (_remove_canary_block, "CAN-001"),
        (_remove_atomic_id_lock, "ID-002"),
        (_remove_batch_code_lock, "ID-003"),
        (_break_editable_layout, "ADM-001"),
        (_undercover_api_capability, "ADM-002"),
        (_skew_starter_distribution, "ADM-003"),
        (_omit_repair_subtype, "CURR-102"),
        (_overshare_feedback, "CURR-103"),
        (_unbalance_header_modes, "HDR-001"),
        (_drop_shape_histogram, "SHAPE-001"),
        (_disable_early_stopping, "DYN-002"),
        (_change_selection_weights, "DYN-003"),
    ],
)
def test_pre_generation_negative_regressions_fail_closed(
    valid_bundle: tuple[dict[str, Any], Path], mutate: Mutation, expected_rule: str
) -> None:
    original, subject = valid_bundle
    bundle = copy.deepcopy(original)
    mutate(bundle)
    receipt = _decision(bundle, subject)
    assert receipt["decision"] == "FAIL"
    assert expected_rule in receipt["hard_failure_ids"]


def _add_task_receipts(bundle: dict[str, Any], tmp_path: Path) -> None:
    roles = (
        ["direct_verified_success"] * 11
        + ["boundary_case"] * 4
        + ["repair_trajectory"] * 4
        + ["calibration"]
    )
    actions = (
        ["header_and_source"] * 9
        + ["header_only_or_template"] * 2
        + ["source_only"] * 8
        + ["calibration_no_change"]
    )
    starters = (
        ["empty"] * 4
        + ["skeleton"] * 5
        + ["partial_implementation"] * 4
        + ["semantic_bug"] * 3
        + ["compile_bug"] * 2
        + ["near_correct"] * 2
    )
    header_modes = [
        mode for mode in sorted(VALIDATOR.HEADER_MODES) for _ in range(4)
    ]
    layouts = ["cpp_only"] * 8 + ["header_only"] * 2 + ["header_and_cpp"] * 10
    receipts = []
    rows = zip(roles, actions, starters, header_modes, layouts, strict=True)
    for index, (role, action, starter, header_mode, layout) in enumerate(rows):
        receipt: dict[str, Any] = {
            "task_id": f"task-{index:02d}",
            "role": role,
            "task_type": "calibration" if role == "calibration" else "standard",
            "action_topology": action,
            "starter_type": starter,
            "header_mode": header_mode,
            "editable_layout": layout,
            "multi_file_gt2": index < 2,
            "api_capabilities": sorted(VALIDATOR.API_CAPABILITIES),
            "repair_types": sorted(VALIDATOR.REPAIR_TYPES) if role == "repair_trajectory" else [],
            "requires_public_api_change": layout != "cpp_only",
            "existing_header_changed": layout != "cpp_only",
            "weighted45": 1.0,
            "oracle_receipt_sha256": hashlib.sha256(f"oracle-{index}".encode()).hexdigest(),
            "private_test_output_disclosed": False,
            **{field: True for field in VALIDATOR.TASK_PROOF_FIELDS},
        }
        if role == "repair_trajectory":
            receipt.update(
                {
                    "genuine_four_turn_structure_passed": True,
                    "failing_candidate_receipt_bound": True,
                    "corrected_candidate_receipt_bound": True,
                    "feedback_policy_match_passed": True,
                }
            )
        receipts.append(receipt)
    bundle["task_receipts"] = receipts
    bundle["post_generation_uniqueness_receipt"] = _uniqueness(
        tmp_path / "post-generation-uniqueness.json"
    )


def test_post_generation_rejects_missing_header_change(
    valid_bundle: tuple[dict[str, Any], Path], tmp_path: Path
) -> None:
    bundle, subject = valid_bundle
    _add_task_receipts(bundle, tmp_path)
    assert _decision(bundle, subject, "post-generation")["decision"] == "PASS"
    bundle["task_receipts"][8]["existing_header_changed"] = False
    receipt = _decision(bundle, subject, "post-generation")
    assert receipt["decision"] == "FAIL"
    assert "V4G-101" in receipt["hard_failure_ids"]


def _add_serialization_and_corpus(bundle: dict[str, Any]) -> None:
    bundle["serialization_receipts"] = [
        {
            "task_id": receipt["task_id"],
            **{field: True for field in VALIDATOR.SERIALIZATION_PROOF_FIELDS},
            "token_ids_sha256": hashlib.sha256(f"tokens-{index}".encode()).hexdigest(),
            "loss_mask_sha256": hashlib.sha256(f"mask-{index}".encode()).hexdigest(),
        }
        for index, receipt in enumerate(bundle["task_receipts"])
    ]
    bundle["corpus_admission"] = {
        "all_task_receipts_reconciled": True,
        "all_serialization_receipts_reconciled": True,
        "duplicate_count": 0,
        "heldout_collision_count": 0,
        "semantic_ambiguity_count": 0,
        "ancestor_correction_coexistence_count": 0,
        "unresolved_review_count": 0,
        "baseline3_status": "passed",
        "validator_v2_batch_status": "batch_v2_analyzed",
        "baseline1_score": 100.0,
        "baseline2_score": 100.0,
        "critical_rule_pass_fraction": 1.0,
        "major_rule_pass_fraction": 1.0,
        "minor_rule_pass_fraction": 1.0,
        "repair_coverage": 0.20,
        "calibration_coverage": 0.05,
        "duplicate_risk": 0.0,
        "generalization_risk_score": 0.10,
        "curriculum_drift_count": 0,
        "training_admission_status": "passed",
        "selected_manifest_sha256": hashlib.sha256(b"selected-manifest").hexdigest(),
        "train_jsonl_sha256": hashlib.sha256(b"train-jsonl").hexdigest(),
    }
    bundle["dataset_shape_receipt"] = {
        "status": "passed",
        "histograms": {
            name: {"present": 20} for name in VALIDATOR.DATASET_SHAPE_HISTOGRAMS
        },
        "families_below_minimum": [],
        "receipt_sha256": hashlib.sha256(b"dataset-shape").hexdigest(),
    }
    bundle["api_failure_predictor"] = {
        "status": "passed",
        "deterministic": True,
        "task_count": 20,
        "api_reconstruction_score": 0.99,
        "predicted_api_failure_risk": 0.01,
        "method_sha256": hashlib.sha256(b"api-predictor-method").hexdigest(),
        "receipt_sha256": hashlib.sha256(b"api-predictor-receipt").hexdigest(),
    }


def test_pre_training_rejects_truncated_serialization(
    valid_bundle: tuple[dict[str, Any], Path], tmp_path: Path
) -> None:
    bundle, subject = valid_bundle
    _add_task_receipts(bundle, tmp_path)
    _add_serialization_and_corpus(bundle)
    assert _decision(bundle, subject, "pre-training")["decision"] == "PASS"
    bundle["serialization_receipts"][0]["no_truncation"] = False
    receipt = _decision(bundle, subject, "pre-training")
    assert receipt["decision"] == "FAIL"
    assert "V4G-200" in receipt["hard_failure_ids"]


def _add_promotion_evidence(bundle: dict[str, Any]) -> None:
    bundle["canary_result"] = {
        "status": "passed",
        "task_count": 20,
        "epochs_run": 5,
        "evaluation_rows_logged": 104,
        "mean_pass_at_1_drop_tasks": 0,
        "public_api_absent_increase_pp": 0.0,
        "contamination_count": 0,
        "malformed_output_count": 0,
        "infrastructure_failure_count": 0,
        "context_exhaustion_fraction": 0.0,
        "all_required_action_topologies_observed": True,
        "receipt_sha256": hashlib.sha256(b"canary").hexdigest(),
    }
    bundle["training_dynamics_result"] = {
        "status": "passed",
        "checkpoints": [
            {
                "step": 1,
                "training_loss": 0.2,
                "validation_loss": 0.3,
                "compile_rate": 0.99,
                "hidden_test_rate": 0.95,
            }
        ],
        "all_checkpoints_logged": True,
        "early_stopping_applied": True,
        "selection_policy": "best_composite_not_always_final",
        "selected_checkpoint_reason": "best_composite",
        "selected_checkpoint_id": "checkpoint-1",
        "receipt_sha256": hashlib.sha256(b"dynamics").hexdigest(),
    }
    bundle["promotion_result"] = {
        "evaluation_health_passed": True,
        "matched_previous_attempt_ledger": True,
        "transition_matrix_complete": True,
        "primary_metric_passed": True,
        "regression_budget_passed": True,
        "compile_reachability_not_regressed": True,
        "public_api_completeness_not_regressed": True,
        "feedback_policy_match_passed": True,
        "compile_rate": 0.99,
        "link_rate": 0.99,
        "api_exposure_rate": 0.98,
        "semantic_failure_rate": 0.03,
        "runtime_failure_rate": 0.0,
        "header_reconstruction_rate": 0.96,
        "previous_mean_pass_at_1": 0.35,
        "candidate_mean_pass_at_1": 0.40,
        "evaluation_rows_logged": 104,
        "shadow_validation_passed": True,
        "generalization_shadow_passed": True,
        "shadow_compile_rate": 0.99,
        "shadow_hidden_test_pass_rate": 0.92,
        "observed_anchor_effective_exposure": 26000,
        "baseline3_deployment_status": "passed",
        "critical_rule_pass_fraction": 1.0,
        "major_rule_pass_fraction": 1.0,
        "minor_rule_pass_fraction": 1.0,
        "duplicate_risk": 0.0,
        "generalization_risk_score": 0.10,
        "curriculum_drift_count": 0,
        "decision": "promote",
        "receipt_sha256": hashlib.sha256(b"promotion").hexdigest(),
    }
    bundle["promotion_score"] = {
        "weights": dict(VALIDATOR.PROMOTION_SCORE_WEIGHTS),
        "component_scores": {name: 100.0 for name in VALIDATOR.PROMOTION_SCORE_WEIGHTS},
        "computed_score": 100.0,
        "critical_gates_all_passed": True,
    }


def test_promotion_rejects_failed_canary(
    valid_bundle: tuple[dict[str, Any], Path], tmp_path: Path
) -> None:
    bundle, subject = valid_bundle
    _add_task_receipts(bundle, tmp_path)
    _add_serialization_and_corpus(bundle)
    _add_promotion_evidence(bundle)
    assert _decision(bundle, subject, "promotion")["decision"] == "PASS"
    bundle["canary_result"]["mean_pass_at_1_drop_tasks"] = 2
    receipt = _decision(bundle, subject, "promotion")
    assert receipt["decision"] == "FAIL"
    assert "V4G-300" in receipt["hard_failure_ids"]


def test_promotion_score_cannot_override_api_failure(
    valid_bundle: tuple[dict[str, Any], Path], tmp_path: Path
) -> None:
    bundle, subject = valid_bundle
    _add_task_receipts(bundle, tmp_path)
    _add_serialization_and_corpus(bundle)
    _add_promotion_evidence(bundle)
    bundle["promotion_result"]["api_exposure_rate"] = 0.96
    receipt = _decision(bundle, subject, "promotion")
    assert receipt["decision"] == "FAIL"
    assert "PROM-003" in receipt["hard_failure_ids"]
    assert "SCORE-001" not in receipt["hard_failure_ids"]


def test_deployment_requires_separate_certification(
    valid_bundle: tuple[dict[str, Any], Path], tmp_path: Path
) -> None:
    bundle, subject = valid_bundle
    _add_task_receipts(bundle, tmp_path)
    _add_serialization_and_corpus(bundle)
    _add_promotion_evidence(bundle)
    assert _decision(bundle, subject, "deployment")["decision"] == "FAIL"
    bundle["deployment_certification"] = {
        "status": "certified",
        "decision": "deploy",
        "promotion_receipt_verified": True,
        "consumer_verification_passed": True,
        "artifact_manifest_complete": True,
        "model_card_complete": True,
        "rollback_plan_complete": True,
        "monitoring_plan_complete": True,
        "security_review_passed": True,
        "reproducibility_passed": True,
        "promotion_receipt_sha256": hashlib.sha256(b"promotion").hexdigest(),
        "artifact_manifest_sha256": hashlib.sha256(b"artifacts").hexdigest(),
        "receipt_sha256": hashlib.sha256(b"deployment").hexdigest(),
    }
    receipt = _decision(bundle, subject, "deployment")
    assert receipt["decision"] == "PASS"
    rule_ids = [rule["rule_id"] for rule in receipt["rules"]]
    assert len(rule_ids) == len(set(rule_ids))


def test_v1_generation_plan_requires_permanent_batch_identity_on_every_proposal() -> None:
    identity = {
        "generation_batch_id": "batch-v1",
        "generation_session_id": "session-v1",
        "generation_batch_code": "31415",
        "generation_batch_created_at_utc": "2026-08-04T03:15:38Z",
        "batch_code_reservation_receipt_sha256": hashlib.sha256(b"batch-receipt").hexdigest(),
    }
    claims = [
        {
            "task_id": f"task-{index}",
            "proposal_sha256": hashlib.sha256(f"proposal-{index}".encode()).hexdigest(),
        }
        for index in range(2)
    ]
    task_id_plan = {
        "protocol_id": "task-generation-v1",
        **identity,
        "claims": claims,
    }
    generation_plan = {
        "protocol_id": "task-generation-v1",
        **identity,
        "proposals": [
            {
                **claim,
                "generation_batch_code": identity["generation_batch_code"],
                "generation_batch_created_at_utc": identity["generation_batch_created_at_utc"],
                "batch_code_reservation_receipt_sha256": identity[
                    "batch_code_reservation_receipt_sha256"
                ],
            }
            for claim in claims
        ],
    }

    assert VALIDATOR._v1_generation_plan_identity_propagated(
        generation_plan, task_id_plan, 2
    )
    missing_top_level_code = copy.deepcopy(generation_plan)
    del missing_top_level_code["generation_batch_code"]
    assert not VALIDATOR._v1_generation_plan_identity_propagated(
        missing_top_level_code, task_id_plan, 2
    )
    missing_proposal_receipt = copy.deepcopy(generation_plan)
    del missing_proposal_receipt["proposals"][0][
        "batch_code_reservation_receipt_sha256"
    ]
    assert not VALIDATOR._v1_generation_plan_identity_propagated(
        missing_proposal_receipt, task_id_plan, 2
    )
