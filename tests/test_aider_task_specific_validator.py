import json
from pathlib import Path

import pytest

from w8_biayn.aider_task_validator.common import load_jsonl
from w8_biayn.aider_task_validator.task_specific import (
    project_task_specific_slice,
    validate_task_specific,
    verify_task_specific_catalog,
)
from w8_biayn.aider_task_validator.validator import ValidationError


ROOT = Path(__file__).parents[1]
TRAIN = ROOT / "dataset/jsonls/staging/charm-v1-20260803T193513Z-sft-v4/train.jsonl"
PRE = ROOT / "dataset/jsonls/staging/charm-v1-20260803T193513Z-sft-v4/pre.jsonl"
BASELINE = (
    ROOT
    / "dataset/reports/validation/charm-v1-20260803T193513Z-baseline3-v6"
    / "dataset_summary.json"
)
SELECTED = (
    ROOT
    / "dataset/reports/validation/charm-v1-20260803T193513Z-independent-audit-v2"
    / "selected_manifest.json"
)
CONSUMER = (
    ROOT
    / "dataset/reports/validation/charm-v1-20260803T193513Z-consumer-v3"
    / "consumer_verification.json"
)
PROFILES = ROOT / "configs/aider_task_validator/task-specific-v1.json"
TOPICS = ["Clock", "Complex Numbers", "Spiral Matrix", "Zebra Puzzle"]


def test_task_specific_profile_catalog_is_scalable_and_complete_for_initial_scope() -> None:
    result = verify_task_specific_catalog(PROFILES)

    assert result["decision"] == "PASS"
    assert result["supported_topic_count"] == 4
    assert result["supported_task_profile_count"] == 12
    assert result["supported_topics"] == sorted(TOPICS)


def test_task_specific_validator_rejects_unbound_baseline(tmp_path: Path) -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    baseline["train_jsonl_sha256"] = "0" * 64
    tampered = tmp_path / "baseline.json"
    tampered.write_text(json.dumps(baseline), encoding="utf-8")

    with pytest.raises(ValidationError, match="hash-bound"):
        validate_task_specific(
            TRAIN,
            PRE,
            tampered,
            SELECTED,
            PROFILES,
            tmp_path / "report",
            TOPICS,
            rerun_execution=False,
        )


def test_current_four_topic_static_gate_and_slice_projection(tmp_path: Path) -> None:
    report_root = tmp_path / "task-specific"
    receipt = validate_task_specific(
        TRAIN,
        PRE,
        BASELINE,
        SELECTED,
        PROFILES,
        report_root,
        TOPICS,
        rerun_execution=False,
    )

    assert receipt["decision"] == "PASS"
    assert receipt["baseline3_eligible_total"] == 51
    assert receipt["selected_task_count"] == 12
    assert receipt["passed_task_count"] == 12
    assert all(item["decision"] == "PASS" for item in receipt["topic_summary"].values())

    slice_root = tmp_path / "slice"
    manifest = project_task_specific_slice(
        TRAIN,
        PRE,
        report_root / "task-specific-receipt.json",
        CONSUMER,
        slice_root,
    )

    assert manifest["decision"] == "PASS"
    assert manifest["status"] == "consumer_verified_task_specific_slice"
    assert manifest["task_count"] == 12
    assert manifest["topic_counts"] == {topic: 3 for topic in sorted(TOPICS)}
    assert manifest["training_authorized"] is False
    assert len(load_jsonl(slice_root / "private/pre.jsonl")) == 12
    assert len(load_jsonl(slice_root / "sft/train.jsonl")) == 12
