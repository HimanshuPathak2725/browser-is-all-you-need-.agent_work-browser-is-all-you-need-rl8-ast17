from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "scripts/charm_v1_combined_generation_plan.py"


def _load():
    spec = importlib.util.spec_from_file_location("charm_v1_combined_plan", OWNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_plan_binds_verified_anchor_and_all_admission_counts() -> None:
    plan = _load().build()
    serialized = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()

    assert plan["authorized_task_count"] == 51
    assert len(plan["proposals"]) == 51
    assert sum(plan["action_counts"]["action_shapes"].values()) == 51
    assert plan["source_counts"] == {"verified_non_synthetic": 1, "synthetic": 50}
    evidence = plan["source_evidence"]
    assert evidence["verified_success_testcase"] == "clock"
    assert evidence["verified_success_count"] == 2
    assert len(evidence["verified_success_receipts"]) == 2
    assert all(Path(item["result_path"]).is_file() for item in evidence["verified_success_receipts"])
    assert all(Path(item["chat_path"]).is_file() for item in evidence["verified_success_receipts"])
    assert hashlib.sha256(serialized).hexdigest()


def test_checked_in_canonical_plan_is_exact_validator_hash_preimage() -> None:
    path = ROOT / "artifacts/charm-task-generation-v1/v1-20260803T193513Z/v1-canonical-generation-plan.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

    assert path.read_bytes() == expected
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(expected).hexdigest()
