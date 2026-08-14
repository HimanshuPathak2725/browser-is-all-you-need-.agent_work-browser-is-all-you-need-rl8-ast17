from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/charm-skill/scripts/transition_v1_task_ids.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("charm_task_id_transition_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _inputs(tmp_path: Path, *, protocol_id: str, count: int) -> tuple[Path, Path, Path]:
    identity = {
        "protocol_id": protocol_id,
        "generation_batch_id": "batch-owner",
        "generation_session_id": "session-owner",
        "generation_batch_code": "10331",
        "generation_batch_created_at_utc": "2026-08-05T06:12:11Z",
        "batch_code_reservation_receipt_sha256": "b" * 64,
    }
    claims = [
        {
            "task_id": f"task-{index:02d}",
            "topic": "Clock",
            "slot_id": str(index),
            "proposal_sha256": f"{index:064x}",
        }
        for index in range(count)
    ]
    plan = {
        "schema_version": "charm-task-id-plan-v2",
        **identity,
        "claims": claims,
    }
    registry = {
        "schema_version": "charm-task-id-reservation-registry-v1",
        "revision": 1,
        "entries": {
            claim["task_id"]: {
                **identity,
                "topic": claim["topic"],
                "slot_id": claim["slot_id"],
                "proposal_sha256": claim["proposal_sha256"],
                "state": "reserved",
                "transition_history": [],
            }
            for claim in claims
        },
    }
    plan_path = tmp_path / "plan.json"
    registry_path = tmp_path / "registry.json"
    evidence_path = tmp_path / "evidence.json"
    _write(plan_path, plan)
    _write(registry_path, registry)
    _write(evidence_path, {"decision": "PASS"})
    return registry_path, plan_path, evidence_path


def test_complete_non_v1_reservation_can_be_tombstoned(tmp_path: Path) -> None:
    module = _load_module()
    registry, plan, evidence = _inputs(
        tmp_path, protocol_id="task-generation-four-topic-60-v1", count=60
    )

    receipt = module.transition(
        registry_path=registry,
        plan_path=plan,
        from_state="reserved",
        to_state="rejected_tombstone",
        evidence_path=evidence,
    )

    assert receipt["decision"] == "PASS"
    assert receipt["task_count"] == 60
    assert len(receipt["transitioned_task_ids"]) == 60
    entries = json.loads(registry.read_text(encoding="utf-8"))["entries"]
    assert {row["state"] for row in entries.values()} == {"rejected_tombstone"}


def test_v1_transition_still_requires_exactly_51_claims(tmp_path: Path) -> None:
    module = _load_module()
    registry, plan, evidence = _inputs(
        tmp_path, protocol_id="task-generation-v1", count=50
    )
    with pytest.raises(ValueError, match="V1 remains exactly 51 claims"):
        module.transition(
            registry_path=registry,
            plan_path=plan,
            from_state="reserved",
            to_state="rejected_tombstone",
            evidence_path=evidence,
        )
