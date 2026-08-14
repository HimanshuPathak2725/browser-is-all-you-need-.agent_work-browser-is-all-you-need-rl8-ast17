from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import scripts.gcp_full_v5_charm_grpo as pipeline


REPO = Path(__file__).resolve().parents[1]
DRIVER = REPO / "scripts/gcp_full_v5_charm_grpo.py"
CONFIG = REPO / "configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87.json"
CANARY = REPO / "configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-canary.json"
RUNTIME = REPO / "artifacts/charm-r7-admitted-mef-exact40-r87-20260812T190000Z"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(phase: str) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            phase,
            "--run-id",
            f"charm-r7-r87-{phase}-render",
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
            "GLM47_FULL_V5_CONFIG_PATH": str(CONFIG),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_admitted_r7_profile_binds_pretraining_runtime_and_pending_canary() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = pipeline.PROFILE_CONTRACTS[config["profile_id"]]
    assert config["decision"] == "ADMITTED_CANARY"
    assert config["execution"]["admission_mode"] == "PRETRAINING_PASS_CANARY_REQUIRED"
    assert config["admission"]["pretraining_receipt"]["sha256"] == (
        "f129fb2c953e7c87fae3f796c9c04c546943f0ad8518c0cfc795a85c1c4218e0"
    )
    assert config["admission"]["canary_result"] == "NOT_COMPLETED"
    assert config["admission"]["full_training_authorized"] is False
    assert config["full_v5_runtime"]["manifest_sha256"] == _sha256(
        RUNTIME / "manifest.json"
    )
    assert config["full_v5_runtime"]["tree_sha256"] == pipeline.tree_sha256(RUNTIME)
    assert config["full_v5_runtime"]["oracle_receipt_sha256"] == _sha256(
        RUNTIME / "oracle-verification-receipt.json"
    )
    assert config["admission"]["canary_task_manifest"]["sha256"] == _sha256(CANARY)
    pipeline._validate_admitted_r7_config(config, contract)


def test_admitted_r7_canary_render_is_exact_five_by_twenty_mef() -> None:
    rendered = _render("canary")
    env = rendered["environment"]
    assert env["MILES_NUM_ROLLOUT"] == "5"
    assert env["MILES_ROLLOUT_BATCH_SIZE"] == "20"
    assert env["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert env["MILES_GLOBAL_BATCH_SIZE"] == "160"
    assert env["MILES_GRPO_ROLLOUT_SHUFFLE"] == "0"
    assert env["MILES_AIDER_REWARD_MODE"] == "hybrid_bipolar45_mef"
    assert env["MILES_EXPECTED_DATASET_KIND"] == "charm-r7-admitted-mef-exact40"
    assert env["MILES_GRPO_PROMPT_DATA"].endswith(
        "/data/grpo/canary-5ep-train.jsonl"
    )
    assert env["MILES_EVAL_PROMPT_DATA"].endswith(
        "/data/eval/task_disjoint_monitor.jsonl"
    )
    assert env["GLM47_AIDER_REQUIRE_UNIQUE_TASK_GROUPS"] == "1"
    assert env["GLM47_CPP_TSAN_PREFLIGHT_REQUIRED"] == "0"
    assert env["GLM47_CPP_TSAN_EXECUTION_ALLOWED"] == "0"


def test_admitted_r7_full_render_preserves_epoch_batch_boundaries() -> None:
    rendered = _render("full")
    env = rendered["environment"]
    assert env["MILES_ROLLOUT_BATCH_SIZE"] == "20"
    assert env["MILES_GRPO_ROLLOUT_SHUFFLE"] == "0"
    assert env["MILES_GRPO_PROMPT_DATA"].endswith(
        "/data/grpo/full-3ep-train.jsonl"
    )


def test_r7_schedule_staging_expands_every_epoch_at_exact_25_percent_repair(
    tmp_path: Path,
) -> None:
    canary = json.loads(CANARY.read_text(encoding="utf-8"))["task_ids"]
    staged = pipeline.stage_r7_training_data(
        RUNTIME, tmp_path / "data", phase="canary", canary_task_ids=canary
    )
    rows = pipeline.read_jsonl(tmp_path / "data" / staged["prompt_data"])
    assert staged["unique_tasks"] == 20
    assert staged["rows"] == 100
    for epoch in range(1, 6):
        epoch_rows = [row for row in rows if row["metadata"]["schedule_epoch"] == epoch]
        assert len(epoch_rows) == 20
        assert len({row["metadata"]["base_task_id"] for row in epoch_rows}) == 20
        assert sum(
            row["metadata"]["curriculum_role"] == "repair" for row in epoch_rows
        ) == 5


def test_train_runner_accepts_explicit_phase_schedule_without_changing_default() -> None:
    text = (REPO / "scripts/train_grpo.sh").read_text(encoding="utf-8")
    assert 'GRPO_PROMPT_DATA="${MILES_GRPO_PROMPT_DATA:-${DATA_DIR}/grpo/train.jsonl}"' in text
    assert '--prompt-data "${GRPO_PROMPT_DATA}"' in text
