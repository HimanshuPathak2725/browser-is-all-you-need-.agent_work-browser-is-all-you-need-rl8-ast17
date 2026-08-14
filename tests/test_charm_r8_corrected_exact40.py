from __future__ import annotations

import json
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot.charm_r7 import (
    build_charm_r7_exact40_dataset,
)
from glm47_posttraining.aider_polyglot.charm_r8 import (
    CALIBRATION_REPLACEMENTS,
    CONTRACT,
    build_corrected_exact40_dataset,
    validate_corrected_exact40_dataset,
    validate_corrected_selection,
)
from glm47_posttraining.aider_polyglot.public_api_manifest import PublicAPIManifestError


REPO = Path(__file__).resolve().parents[1]
HISTORICAL = REPO / "configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-selection.json"
CORRECTED = REPO / "configs/full_v5_charm_grpo/r8-candidate-hybrid45-exact40-r87-selection.json"


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_corrected_selection_excludes_no_op_calibrations_and_invalidates_admission() -> None:
    corrected = validate_corrected_selection(CORRECTED)
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    selection = corrected["selection"]
    assert corrected["rewardability_ready"] is True
    assert selection["reward_policy"] == "hybrid-bipolar45-v2"
    assert selection["schedule"] == historical["schedule"]
    assert selection["rubric_update"]["task_replacements"] == dict(
        sorted(CALIBRATION_REPLACEMENTS.items())
    )
    assert selection["rubric_update"]["curriculum_task_ids_changed"] is True
    assert selection["rubric_update"]["prompt_topology_changed"] is False
    assert selection["rubric_update"]["formula_changed"] is False
    assert selection["rubric_update"]["calibration_gradient_task_count"] == 0
    assert selection["rubric_update"]["failed_rewardability_replay"] == {
        "schema_version": "charm-r8-hybrid45-corpus-no-update-replay-v1",
        "file_sha256": selection["rubric_update"]["failed_rewardability_replay"][
            "file_sha256"
        ],
        "receipt_sha256": selection["rubric_update"]["failed_rewardability_replay"][
            "receipt_sha256"
        ],
        "optimizer_updates": 0,
        "task_count": 51,
        "functional_reference_pass_count": 51,
        "gradient_task_count": 40,
        "gradient_full_positive_reward_count": 37,
        "failed_task_ids": sorted(CALIBRATION_REPLACEMENTS),
        "raw_artifact_preserved_locally": True,
    }
    selected_ids = {
        task_id for task_ids in selection["groups"].values() for task_id in task_ids
    }
    assert not selected_ids & set(CALIBRATION_REPLACEMENTS)
    assert set(CALIBRATION_REPLACEMENTS.values()) <= selected_ids
    assert selection["expected_full_composition"]["role_counts"] == {
        "boundary_case": 10,
        "direct_verified_success": 20,
        "repair_trajectory": 10,
    }
    assert selection["expected_full_composition"]["header_mode_counts"] == {
        "editable": 8,
        "extended": 8,
        "frozen": 8,
        "reconstructed": 8,
        "repaired": 8,
    }


def test_corrected_runtime_uses_hybrid45_v2_with_rewardable_exact40(
    tmp_path: Path,
) -> None:
    historical_root = tmp_path / "historical"
    corrected_root = tmp_path / "corrected"
    historical_paths = build_charm_r7_exact40_dataset(HISTORICAL, historical_root)
    corrected_paths = build_corrected_exact40_dataset(CORRECTED, corrected_root)
    validation = validate_corrected_exact40_dataset(corrected_root)
    assert validation["decision"] == "PASS"
    assert validation["gradient_task_count"] == 40
    assert validation["repair_task_count"] == 10
    assert validation["public_api_manifest_count"] == 51
    runtime_manifest = json.loads(corrected_paths["manifest"].read_text(encoding="utf-8"))
    assert runtime_manifest["public_api_contract"]["authoritative_for_k2"] is True
    assert runtime_manifest["public_api_contract"]["reward_weights_changed"] is False
    assert len(list(corrected_root.glob("shadow/*/.grader/public_api_manifest.json"))) == 51

    historical_rows = _rows(historical_paths["grpo_train"])
    corrected_rows = _rows(corrected_paths["grpo_train"])
    historical_by_id = {
        row["metadata"]["base_task_id"]: row for row in historical_rows
    }
    corrected_by_id = {
        row["metadata"]["base_task_id"]: row for row in corrected_rows
    }
    assert set(corrected_by_id) - set(historical_by_id) == set(
        CALIBRATION_REPLACEMENTS.values()
    )
    assert set(historical_by_id) - set(corrected_by_id) == set(CALIBRATION_REPLACEMENTS)
    for task_id in set(corrected_by_id) & set(historical_by_id):
        assert corrected_by_id[task_id]["prompt"] == historical_by_id[task_id]["prompt"]
    assert all(row["metadata"]["reward_policy"] == "hybrid-bipolar45-v2" for row in corrected_rows)
    repair_rows = [row for row in corrected_rows if row["metadata"]["curriculum_role"] == "repair"]
    assert len(repair_rows) == 10
    assert all(
        [message["role"] for message in row["prompt"]][-2:] == ["assistant", "user"]
        for row in repair_rows
    )

    first_api_manifest = next(corrected_root.glob("shadow/*/.grader/public_api_manifest.json"))
    tampered = json.loads(first_api_manifest.read_text(encoding="utf-8"))
    tampered["task_id"] = "tampered"
    first_api_manifest.write_text(
        json.dumps(tampered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(PublicAPIManifestError, match="invalid public API manifest"):
        validate_corrected_exact40_dataset(corrected_root)
