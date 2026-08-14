from __future__ import annotations

import json
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot.charm_grpo import CharmGRPOProjectionError
from glm47_posttraining.aider_polyglot.charm_r7 import (
    REPAIR_FEEDBACK,
    build_charm_r7_exact40_dataset,
    validate_charm_r7_exact40_dataset,
    validate_r7_selection,
)


REPO = Path(__file__).resolve().parents[1]
SELECTION = REPO / "configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-selection.json"


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_r7_selection_is_exact_and_digest_bound() -> None:
    result = validate_r7_selection(SELECTION)
    assert result["decision"] == "PASS"
    assert len(result["selected_tasks"]) == 40
    assert len(result["monitor_tasks"]) == 11
    assert len(result["canary_ids"]) == 20
    assert len(set(result["ordered_ids"])) == 40
    assert set(result["canary_ids"]) < set(result["ordered_ids"])


def test_r7_build_has_exact_mef_lanes_schedules_and_privacy(tmp_path: Path) -> None:
    output = tmp_path / "r7"
    paths = build_charm_r7_exact40_dataset(SELECTION, output, run_id="test-r7")
    validation = validate_charm_r7_exact40_dataset(output)
    assert validation == {
        "decision": "PASS",
        "manifest_sha256": validation["manifest_sha256"],
        "selection_sha256": validation["selection_sha256"],
        "gradient_task_count": 40,
        "repair_task_count": 10,
        "monitor_task_count": 11,
        "canary_task_count": 20,
        "private_marker_count": 0,
        "task_overlap_count": 0,
    }
    train = _rows(paths["grpo_train"])
    canary = _rows(paths["grpo_canary"])
    monitor = _rows(paths["monitor"])
    assert len(train) == 40
    assert len(canary) == 20
    assert len(monitor) == 11
    assert sum(row["metadata"]["curriculum_role"] == "repair" for row in train) == 10
    assert sum(row["metadata"]["curriculum_role"] == "repair" for row in canary) == 5
    assert all(row["metadata"]["gradient_bearing"] is True for row in train)
    assert all(row["metadata"]["gradient_bearing"] is False for row in monitor)
    assert all(
        row["metadata"]["reward_policy"] == "hybrid-bipolar45-mef-v1"
        for row in train + monitor
    )
    for row in train:
        roles = [message["role"] for message in row["prompt"]]
        if row["metadata"]["curriculum_role"] == "repair":
            assert roles[-2:] == ["assistant", "user"]
            assert row["prompt"][-1]["content"] == REPAIR_FEEDBACK
        else:
            assert roles[-1] == "user"
    assert len(_rows(paths["full_schedule"])) == 120
    assert len(_rows(paths["canary_schedule"])) == 100


def test_r7_build_is_deterministic_except_run_id(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    paths_a = build_charm_r7_exact40_dataset(SELECTION, first, run_id="same")
    paths_b = build_charm_r7_exact40_dataset(SELECTION, second, run_id="same")
    for key in (
        "grpo_train",
        "grpo_canary",
        "monitor",
        "full_schedule",
        "canary_schedule",
        "subset_manifest",
        "manifest",
    ):
        assert paths_a[key].read_bytes() == paths_b[key].read_bytes()


def test_r7_selection_rejects_digest_or_ratio_drift(tmp_path: Path) -> None:
    value = json.loads(SELECTION.read_text(encoding="utf-8"))
    value["source"]["selected_manifest_sha256"] = "0" * 64
    stale = REPO / "configs/full_v5_charm_grpo/.r7-test-stale.json"
    try:
        stale.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(CharmGRPOProjectionError, match="source binding"):
            validate_r7_selection(stale)
    finally:
        stale.unlink(missing_ok=True)

    value = json.loads(SELECTION.read_text(encoding="utf-8"))
    value["canary_task_ids"][0] = value["groups"]["temporal_state"][1]
    drift = REPO / "configs/full_v5_charm_grpo/.r7-test-drift.json"
    try:
        drift.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(CharmGRPOProjectionError):
            validate_r7_selection(drift)
    finally:
        drift.unlink(missing_ok=True)


def test_runtime_package_never_contains_reference_or_source_evidence(tmp_path: Path) -> None:
    output = tmp_path / "r7"
    build_charm_r7_exact40_dataset(SELECTION, output)
    relative_files = {
        path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()
    }
    assert not any("/.reference/" in f"/{name}/" for name in relative_files)
    assert not any("/.negative/" in f"/{name}/" for name in relative_files)
    assert not any(name.endswith("/.rubric.json") for name in relative_files)
