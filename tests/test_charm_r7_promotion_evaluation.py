from __future__ import annotations

import json
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot.charm_grpo import CharmGRPOProjectionError
from glm47_posttraining.aider_polyglot.charm_r7_promotion import (
    build_r7_private_validation_targets,
    build_r7_public_evaluation_bundle,
    validate_r7_private_validation_targets,
    validate_r7_promotion_split,
    validate_r7_public_evaluation_bundle,
)


REPO = Path(__file__).resolve().parents[1]
SPLIT = REPO / "configs/full_v5_charm_grpo/r7-r87-promotion-evaluation-split.json"


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_split_is_exact_disjoint_balanced_and_source_bound() -> None:
    result = validate_r7_promotion_split(SPLIT)
    assert result["decision"] == "PASS"
    assert len(result["development_ids"]) == 6
    assert len(result["shadow_ids"]) == 5
    assert not set(result["development_ids"]) & set(result["shadow_ids"])
    assert result["header_mode_counts"] == {
        "editable": 1,
        "extended": 1,
        "frozen": 1,
        "reconstructed": 1,
        "repaired": 1,
    }


def test_public_bundle_is_byte_exact_answer_free_and_keeps_shadow_separate(
    tmp_path: Path,
) -> None:
    paths = build_r7_public_evaluation_bundle(SPLIT, tmp_path / "public")
    result = validate_r7_public_evaluation_bundle(SPLIT, tmp_path / "public")
    assert result["development_task_count"] == 6
    assert result["unseen_shadow_task_count"] == 5
    assert len(_rows(paths["checkpoint_development"])) == 6
    assert len(_rows(paths["unseen_shadow"])) == 5
    assert all(
        row["prompt"][-1]["role"] == "user"
        for path in (paths["checkpoint_development"], paths["unseen_shadow"])
        for row in _rows(path)
    )


def test_private_loss_bundle_contains_only_six_development_targets(
    tmp_path: Path,
) -> None:
    paths = build_r7_private_validation_targets(SPLIT, tmp_path / "private")
    result = validate_r7_private_validation_targets(SPLIT, tmp_path / "private")
    rows = _rows(paths["targets"])
    split = validate_r7_promotion_split(SPLIT)
    assert result["target_task_count"] == 6
    assert result["shadow_target_count"] == 0
    assert [row["task_id"] for row in rows] == split["development_ids"]
    assert not set(split["shadow_ids"]) & {row["task_id"] for row in rows}
    for row in rows:
        public_prompt = split["monitor_by_id"][row["task_id"]]["prompt"]
        assert row["messages"][:-1] == public_prompt
        assert row["messages"][-1]["role"] == "assistant"
        assert row["messages"][-1]["content"]


def test_split_rejects_shadow_checkpoint_selection_exposure(tmp_path: Path) -> None:
    value = json.loads(SPLIT.read_text(encoding="utf-8"))
    value["unseen_shadow_contract"]["checkpoint_selection_exposure_count"] = 1
    drift = REPO / "configs/full_v5_charm_grpo/.r7-promotion-test-drift.json"
    try:
        drift.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(CharmGRPOProjectionError, match="balance/access"):
            validate_r7_promotion_split(drift)
    finally:
        drift.unlink(missing_ok=True)
