from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/charm-skill/scripts/reserve_v1_task_ids.py"
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


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_inputs(
    root: Path,
    *,
    batch_id: str,
    session_id: str,
    task_id: str = "allergies-bit-policy",
    slot_id: str = "1",
) -> tuple[Path, Path]:
    proposal_sha256 = _sha(f"proposal-plan-{batch_id}".encode())
    corpus_sha256 = _sha(b"complete-repository-corpus-index")
    batch_created_at = "2026-08-04T03:15:38Z"
    batch_code = f"{int(_sha(batch_id.encode())[:8], 16) % 100_000:05d}"
    batch_receipt = {
        "schema_version": "charm-batch-code-reservation-receipt-v1",
        "decision": "PASS",
        "operation": "reserve_batch_code",
        "atomic_lock_acquired": True,
        "registry_reconciled": True,
        "reservation_state": "permanent",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        "generation_batch_created_at_utc": batch_created_at,
        "generation_batch_code": batch_code,
        "batch_code_derivation": "unix-seconds-mod-100000-linear-probe-v1",
        "historical_alias_only": False,
        "codes_reusable": False,
    }
    root.mkdir(parents=True, exist_ok=True)
    batch_receipt_path = root / "batch-code-receipt.json"
    batch_receipt_path.write_text(json.dumps(batch_receipt), encoding="utf-8")
    plan = {
        "schema_version": "charm-task-id-plan-v2",
        "protocol_id": "charm-generic",
        "generation_batch_id": batch_id,
        "generation_session_id": session_id,
        "generation_batch_created_at_utc": batch_created_at,
        "generation_batch_code": batch_code,
        "batch_code_reservation_receipt_sha256": _sha(batch_receipt_path.read_bytes()),
        "proposal_plan_sha256": proposal_sha256,
        "corpus_index_sha256": corpus_sha256,
        "materialization_manifest_sha256": _sha(b"materialization-manifest"),
        "claims": [
            {
                "task_id": task_id,
                "topic": "Allergies",
                "slot_id": slot_id,
                "proposal_sha256": _sha(f"{batch_id}-{task_id}".encode()),
            }
        ],
    }
    uniqueness = {
        "decision": "PASS",
        "repository_scope_complete": True,
        "parse_failures": 0,
        "task_id_matches": 0,
        "exact_matches": 0,
        "near_matches": 0,
        "structural_matches": 0,
        "semantic_matches": 0,
        "ambiguous_matches": 0,
        "proposal_plan_sha256": proposal_sha256,
        "corpus_index_sha256": corpus_sha256,
        "proposal_count": 1,
        "generated_query_count": 1,
        "generated_component_count": 12,
        "materialization_manifest_sha256": plan["materialization_manifest_sha256"],
    }
    plan_path = root / "plan.json"
    uniqueness_path = root / "uniqueness.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    uniqueness_path.write_text(json.dumps(uniqueness), encoding="utf-8")
    return plan_path, uniqueness_path


def _command(
    registry: Path, plan: Path, uniqueness: Path, output: Path
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--registry",
        str(registry),
        "--plan",
        str(plan),
        "--uniqueness-receipt",
        str(uniqueness),
        "--batch-code-receipt",
        str(plan.with_name("batch-code-receipt.json")),
        "--output",
        str(output),
    ]


def _make_full_v1_plan(plan_path: Path, *, replacement_topic: str | None = None) -> None:
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    topics = list(V1_TOPICS)
    if replacement_topic is not None:
        topics[-1] = replacement_topic
    payload["protocol_id"] = "task-generation-v1"
    payload["claims"] = [
        {
            "task_id": f"v1-task-{topic_index:02d}-{slot_id}",
            "topic": topic,
            "slot_id": str(slot_id),
            "proposal_sha256": _sha(f"{topic_index}-{slot_id}-{topic}".encode()),
        }
        for topic_index, topic in enumerate(topics, start=1)
        for slot_id in range(1, 4)
    ]
    plan_path.write_text(json.dumps(payload), encoding="utf-8")
    uniqueness_path = plan_path.with_name("uniqueness.json")
    uniqueness = json.loads(uniqueness_path.read_text(encoding="utf-8"))
    uniqueness["proposal_count"] = 51
    uniqueness["generated_query_count"] = 51
    uniqueness["generated_component_count"] = 51 * 12
    uniqueness_path.write_text(json.dumps(uniqueness), encoding="utf-8")


def test_v1_zero_query_uniqueness_cannot_reserve(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    _make_full_v1_plan(plan)
    payload = json.loads(uniqueness.read_text(encoding="utf-8"))
    payload["generated_query_count"] = 0
    payload["generated_component_count"] = 0
    uniqueness.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "failure.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not registry.exists()
    assert "exactly 51 generated package queries" in result.stderr


def test_same_session_retry_is_idempotent(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    first = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "first.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "second.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    second_receipt = json.loads((tmp_path / "second.json").read_text(encoding="utf-8"))
    assert second_receipt["created_task_ids"] == []
    assert second_receipt["resumed_task_ids"] == ["allergies-bit-policy"]
    assert json.loads(registry.read_text(encoding="utf-8"))["revision"] == 1


def test_parallel_sessions_cannot_claim_the_same_task_id(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan_a, uniqueness_a = _write_inputs(
        tmp_path / "session-a", batch_id="v1-batch-001", session_id="session-a"
    )
    plan_b, uniqueness_b = _write_inputs(
        tmp_path / "session-b", batch_id="v1-batch-002", session_id="session-b"
    )
    process_a = subprocess.Popen(
        _command(registry, plan_a, uniqueness_a, tmp_path / "receipt-a.json"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    process_b = subprocess.Popen(
        _command(registry, plan_b, uniqueness_b, tmp_path / "receipt-b.json"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _, stderr_a = process_a.communicate(timeout=10)
    _, stderr_b = process_b.communicate(timeout=10)
    assert sorted([process_a.returncode, process_b.returncode]) == [0, 1], (stderr_a, stderr_b)
    registry_payload = json.loads(registry.read_text(encoding="utf-8"))
    assert list(registry_payload["entries"]) == ["allergies-bit-policy"]
    assert registry_payload["revision"] == 1
    decisions = {
        json.loads((tmp_path / name).read_text(encoding="utf-8"))["decision"]
        for name in ("receipt-a.json", "receipt-b.json")
    }
    assert decisions == {"PASS", "FAIL"}


def test_different_session_cannot_take_an_existing_topic_slot(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan_a, uniqueness_a = _write_inputs(
        tmp_path / "session-a", batch_id="v1-batch-001", session_id="session-a"
    )
    plan_b, uniqueness_b = _write_inputs(
        tmp_path / "session-b",
        batch_id="v1-batch-001",
        session_id="session-b",
        task_id="allergies-threshold-ledger",
    )
    first = subprocess.run(
        _command(registry, plan_a, uniqueness_a, tmp_path / "first.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        _command(registry, plan_b, uniqueness_b, tmp_path / "second.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert "topic slot already owned" in second.stderr


def test_incomplete_uniqueness_scan_cannot_reserve(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    payload = json.loads(uniqueness.read_text(encoding="utf-8"))
    payload["repository_scope_complete"] = False
    uniqueness.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "failure.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not registry.exists()
    assert json.loads((tmp_path / "failure.json").read_text(encoding="utf-8"))["decision"] == "FAIL"


def test_tombstoned_task_id_is_never_reused(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan_a, uniqueness_a = _write_inputs(
        tmp_path / "session-a", batch_id="v1-batch-001", session_id="session-a"
    )
    first = subprocess.run(
        _command(registry, plan_a, uniqueness_a, tmp_path / "first.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stderr
    registry_payload = json.loads(registry.read_text(encoding="utf-8"))
    registry_payload["entries"]["allergies-bit-policy"]["state"] = "rejected_tombstone"
    registry.write_text(json.dumps(registry_payload), encoding="utf-8")

    plan_b, uniqueness_b = _write_inputs(
        tmp_path / "session-b", batch_id="v1-batch-002", session_id="session-b"
    )
    second = subprocess.run(
        _command(registry, plan_b, uniqueness_b, tmp_path / "second.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert second.returncode == 1
    assert "task_id already claimed or registered" in second.stderr


def test_v1_protocol_rejects_an_incomplete_topic_slot_plan(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    payload = json.loads(plan.read_text(encoding="utf-8"))
    payload["protocol_id"] = "task-generation-v1"
    plan.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "failure.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "exactly the frozen 17 topics" in result.stderr


def test_v1_protocol_accepts_the_exact_17_topic_51_slot_plan(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    _make_full_v1_plan(plan)
    result = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "receipt.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["claim_count"] == 51
    assert len(receipt["slot_keys"]) == 51


def test_v1_protocol_rejects_a_substituted_topic_even_with_51_claims(tmp_path: Path) -> None:
    registry = tmp_path / "registry" / "task_id_reservations.json"
    plan, uniqueness = _write_inputs(
        tmp_path / "session", batch_id="v1-batch-001", session_id="session-a"
    )
    _make_full_v1_plan(plan, replacement_topic="Unapproved Topic")
    result = subprocess.run(
        _command(registry, plan, uniqueness, tmp_path / "failure.json"),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "exactly the frozen 17 topics" in result.stderr
