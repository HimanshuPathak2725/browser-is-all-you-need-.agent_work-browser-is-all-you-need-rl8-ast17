from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


publisher = load_module(
    "publish_aider_cleanroom_wandb",
    ROOT / "scripts/publish_aider_cleanroom_wandb.py",
)
modal_publisher = load_module(
    "aider_cleanroom_wandb_publish_app",
    ROOT / "examples/modal/aider_cleanroom_wandb_publish_app.py",
)


def receipt(*, tries: int = 1) -> dict[str, object]:
    return {
        "kind": "aider-gpt56-luna-cleanroom-run",
        "phase": "full",
        "status": "passed",
        "run_id": "run-1",
        "tries": tries,
        "task_count": 1,
        "metrics": {
            "pass_at_1": 0,
            "pass_at_k": 1 if tries == 2 else 0,
            "well_formed_tasks": 1,
        },
        "task_receipts": [
            {
                "task_id": "clock",
                "result": {
                    "pass_at_1": 0,
                    "pass_at_k": 1 if tries == 2 else 0,
                    "well_formed": True,
                    "malformed_responses": 0,
                    "error_outputs": 0,
                },
                "api_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "reasoning_tokens": 2,
                },
            }
        ],
        "preflight_binding": {"path": "/tmp/preflight/run_receipt.json"},
    }


def test_build_summary_records_pass_two_repairs() -> None:
    summary = publisher.build_summary(receipt(tries=2))
    assert summary["eval/pass_at_1_rate"] == 0
    assert summary["eval/pass_at_2_rate"] == 1
    assert summary["eval/repaired_on_attempt_2"] == 1


def test_build_task_rows() -> None:
    assert publisher.build_task_rows(receipt())[0] == (
        "clock",
        0,
        0,
        True,
        0,
        0,
        10,
        5,
        2,
    )


def test_load_completed_receipt_rejects_failed_run(tmp_path: Path) -> None:
    payload = receipt()
    payload["status"] = "failed"
    path = tmp_path / "run_receipt.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="completed, passed"):
        publisher.load_completed_receipt(path)


def test_resolve_preflight_receipt_from_binding() -> None:
    assert publisher.resolve_preflight_receipt(receipt(), "") == Path(
        "/tmp/preflight/run_receipt.json"
    )


def test_modal_payload_contains_metrics_but_no_raw_evidence() -> None:
    payload = receipt(tries=2)
    payload.update(
        {
            "model_requested": "gpt-5.6-luna",
            "provider": "openrouter",
            "provider_model_requested": "openai/gpt-5.6-luna",
            "aider_commit": "aider-sha",
            "polyglot_commit": "polyglot-sha",
            "reasoning_effort": "medium",
        }
    )
    result = modal_publisher.build_payload(payload)
    assert result["summary"]["eval/pass_at_2"] == 1
    assert result["summary"]["eval/repaired_on_attempt_2"] == 1
    assert result["config"]["raw_evidence_uploaded"] is False
    assert len(result["rows"]) == 1
    serialized = json.dumps(result)
    assert "run_bundle.tar.gz" not in serialized
    assert "preflight_binding" not in serialized


def test_collect_controller_logs_preserves_bytes_and_hashes(tmp_path: Path) -> None:
    log_root = tmp_path / "controller-logs"
    log_root.mkdir()
    (log_root / "clock.stdout.txt").write_bytes(b"model output\ntest feedback\n")
    files = modal_publisher.collect_controller_logs(tmp_path)
    assert files == [
        {
            "path": "clock.stdout.txt",
            "bytes": 27,
            "sha256": "fec768daa467dcebfe6a5dba7b3f97748f91ed945e627ac28d8c769c7090ce38",
            "data": b"model output\ntest feedback\n",
        }
    ]


def test_collect_controller_logs_rejects_credential_patterns(tmp_path: Path) -> None:
    log_root = tmp_path / "controller-logs"
    log_root.mkdir()
    (log_root / "unsafe.txt").write_text(
        "Authorization: Bearer sk-secret-value-1234567890\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="credential-like"):
        modal_publisher.collect_controller_logs(tmp_path)
