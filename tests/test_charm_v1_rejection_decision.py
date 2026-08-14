from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/charm_v1_rejection_decision.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("charm_v1_rejection_decision_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def test_rejection_decision_binds_exact_plan_and_failing_receipts(tmp_path: Path) -> None:
    module = _load_module()
    identity = {
        "generation_batch_id": "batch-v1",
        "generation_session_id": "session-v1",
        "generation_batch_code": "16180",
        "generation_batch_created_at_utc": "2026-08-04T05:00:00Z",
        "batch_code_reservation_receipt_sha256": "b" * 64,
    }
    plan = {
        "schema_version": module.PLAN_SCHEMA,
        "protocol_id": "task-generation-v1",
        **identity,
        "claims": [{"task_id": f"task-{index:02d}"} for index in range(51)],
    }
    plan_path = tmp_path / "plan.json"
    _write(plan_path, plan)
    scope_failure = {
        "decision": "not_completed",
        "generation_batch_id": identity["generation_batch_id"],
        "generation_session_id": identity["generation_session_id"],
        "hard_failure_ids": ["batch_code_identity_propagated"],
    }
    scope_path = tmp_path / "scope-failure.json"
    _write(scope_path, scope_failure)
    subject_path = tmp_path / "admission-bundle.json"
    _write(subject_path, {"task_id_reservation_plan": plan})
    v4_failure = {
        "decision": "FAIL",
        "hard_failure_ids": ["ID-004"],
        "subject_path": str(subject_path),
        "subject_sha256": hashlib.sha256(subject_path.read_bytes()).hexdigest(),
    }
    v4_path = tmp_path / "v4-failure.json"
    _write(v4_path, v4_failure)

    result = module.decide(plan_path, [scope_path, v4_path])
    assert result["decision"] == "PASS"
    assert result["action"] == "transition_to_rejected_tombstone"
    assert result["task_count"] == 51
    assert result["failure_evidence_count"] == 2

    passing_path = tmp_path / "passing.json"
    _write(
        passing_path,
        {
            **scope_failure,
            "decision": "PASS",
            "hard_failure_ids": [],
        },
    )
    with pytest.raises(ValueError, match="not a failing receipt"):
        module.decide(plan_path, [passing_path])


def test_rejection_decision_supports_complete_non_v1_protocol(tmp_path: Path) -> None:
    module = _load_module()
    identity = {
        "generation_batch_id": "batch-ft60",
        "generation_session_id": "session-ft60",
        "generation_batch_code": "10331",
        "generation_batch_created_at_utc": "2026-08-05T06:12:11Z",
        "batch_code_reservation_receipt_sha256": "c" * 64,
    }
    plan = {
        "schema_version": module.PLAN_SCHEMA,
        "protocol_id": "task-generation-four-topic-60-v1",
        **identity,
        "claims": [{"task_id": f"ft60-task-{index:02d}"} for index in range(60)],
    }
    plan_path = tmp_path / "plan.json"
    _write(plan_path, plan)
    failure_path = tmp_path / "failure.json"
    _write(
        failure_path,
        {
            "decision": "FAIL",
            "generation_batch_id": identity["generation_batch_id"],
            "generation_session_id": identity["generation_session_id"],
            "hard_failure_ids": ["V4G-027"],
        },
    )

    result = module.decide(plan_path, [failure_path])

    assert result["decision"] == "PASS"
    assert result["protocol_id"] == "task-generation-four-topic-60-v1"
    assert result["task_count"] == 60
    assert len(result["task_ids"]) == 60


def test_rejection_accepts_validator_canonical_subject_and_bound_plan(
    tmp_path: Path,
) -> None:
    module = _load_module()
    identity = {
        "generation_batch_id": "batch-ft60",
        "generation_session_id": "session-ft60",
        "generation_batch_code": "10331",
        "generation_batch_created_at_utc": "2026-08-05T06:12:11Z",
        "batch_code_reservation_receipt_sha256": "d" * 64,
    }
    plan = {
        "schema_version": module.PLAN_SCHEMA,
        "protocol_id": "task-generation-four-topic-60-v1",
        **identity,
        "claims": [{"task_id": f"ft60-task-{index:02d}"} for index in range(60)],
    }
    plan_path = tmp_path / "plan.json"
    _write(plan_path, plan)
    subject = {
        "task_id_reservation_plan": {
            "path": str(plan_path),
            "sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        }
    }
    subject_path = tmp_path / "bundle.json"
    _write(subject_path, subject)
    failure_path = tmp_path / "validator-failure.json"
    _write(
        failure_path,
        {
            "decision": "FAIL",
            "hard_failure_ids": ["V4G-027"],
            "subject_path": str(subject_path),
            "subject_sha256": hashlib.sha256(
                json.dumps(subject, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        },
    )

    result = module.decide(plan_path, [failure_path])

    assert result["decision"] == "PASS"
    assert result["failure_evidence"][0]["subject"]["hash_mode"] == "validator_canonical_json"
