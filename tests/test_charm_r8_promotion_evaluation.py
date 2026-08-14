from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot.charm_grpo import CharmGRPOProjectionError
from glm47_posttraining.aider_polyglot.charm_r8_checkpoint_selection import (
    METRICS_SCHEMA,
    select_r8_checkpoint,
)
from glm47_posttraining.aider_polyglot.charm_r8_promotion import (
    build_r8_private_validation_targets,
    build_r8_public_evaluation_bundle,
    validate_r8_private_validation_targets,
    validate_r8_promotion_split,
    validate_r8_public_evaluation_bundle,
)


REPO = Path(__file__).resolve().parents[1]
SPLIT = REPO / "configs/full_v5_charm_grpo/r8-r87-promotion-evaluation-split.json"
CALIBRATION_TASKS = {
    "charm-v1r87-37414-dcb547c5-bezier-complex-samples",
    "charm-v1r87-37414-dcb547c5-rubric-cap-scores",
    "charm-v1r87-37414-dcb547c5-successor-thread-audit",
}


def _metrics(*, shadow_exposure: int = 0) -> dict[str, object]:
    frozen = validate_r8_promotion_split(SPLIT)
    values = [
        ("iter_0000001", 1, 0.80, 0.70, 0.40, False),
        ("iter_0000002", 2, 0.98, 0.95, 0.20, False),
        ("iter_0000003", 3, 0.90, 0.90, 0.25, False),
        ("iter_0000004", 4, 0.92, 0.91, 0.30, False),
        ("iter_0000005", 5, 0.93, 0.90, 0.22, True),
    ]
    return {
        "schema_version": METRICS_SCHEMA,
        "decision": "COMPLETE",
        "split_sha256": frozen["split_sha256"],
        "development_task_ids": frozen["development_ids"],
        "development_task_count": 6,
        "shadow_checkpoint_selection_exposure_count": shadow_exposure,
        "official_fixed26_checkpoint_selection_exposure_count": 0,
        "checkpoints": [
            {
                "checkpoint_id": checkpoint_id,
                "optimizer_step": step,
                "adapter_sha256": hashlib.sha256(checkpoint_id.encode()).hexdigest(),
                "is_final": is_final,
                "compile_rate": compile_rate,
                "hidden_test_pass_rate": hidden_rate,
                "target_token_validation_loss": loss,
                "development_task_count": 6,
                "infrastructure_failure_count": 0,
                "malformed_output_count": 0,
                "context_exhaustion_rate": 0.0,
            }
            for checkpoint_id, step, compile_rate, hidden_rate, loss, is_final in values
        ],
    }


def test_r8_split_keeps_calibration_tasks_post_selection_only() -> None:
    result = validate_r8_promotion_split(SPLIT)
    assert result["decision"] == "PASS"
    assert len(result["development_ids"]) == 6
    assert len(result["shadow_ids"]) == 5
    assert CALIBRATION_TASKS <= set(result["shadow_ids"])
    assert not CALIBRATION_TASKS & set(result["development_ids"])
    assert result["header_mode_counts"] == {
        "editable": 1,
        "extended": 1,
        "frozen": 1,
        "reconstructed": 1,
        "repaired": 1,
    }


def test_r8_public_and_private_bundles_preserve_shadow_boundary(tmp_path: Path) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"
    public_paths = build_r8_public_evaluation_bundle(SPLIT, public)
    private_paths = build_r8_private_validation_targets(SPLIT, private)
    public_result = validate_r8_public_evaluation_bundle(SPLIT, public)
    private_result = validate_r8_private_validation_targets(SPLIT, private)
    public_manifest = json.loads(public_paths["manifest"].read_text(encoding="utf-8"))
    private_manifest = json.loads(private_paths["manifest"].read_text(encoding="utf-8"))
    assert public_result["development_task_count"] == 6
    assert public_result["unseen_shadow_task_count"] == 5
    assert private_result["target_task_count"] == 6
    assert private_result["shadow_target_count"] == 0
    assert public_manifest["schema_version"] == "charm-r8-public-evaluation-bundle-v1"
    assert private_manifest["schema_version"] == (
        "charm-r8-private-validation-target-bundle-v1"
    )


def test_checkpoint_selection_uses_weighted_metrics_not_final_position(
    tmp_path: Path,
) -> None:
    metrics = tmp_path / "metrics.json"
    metrics.write_text(json.dumps(_metrics(), sort_keys=True) + "\n", encoding="utf-8")
    result = select_r8_checkpoint(
        split_file=SPLIT,
        metrics_file=metrics,
        output=tmp_path / "selection.json",
    )
    assert result["decision"] == "PASS"
    assert result["selected_checkpoint_id"] == "iter_0000002"
    assert result["selected_checkpoint_is_final"] is False
    assert result["final_checkpoint_selected_by_position"] is False
    assert len(result["ranking"]) == 5


def test_checkpoint_selection_rejects_any_shadow_exposure(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.json"
    metrics.write_text(
        json.dumps(_metrics(shadow_exposure=1), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(CharmGRPOProjectionError, match="frozen split contract"):
        select_r8_checkpoint(
            split_file=SPLIT,
            metrics_file=metrics,
            output=tmp_path / "selection.json",
        )
