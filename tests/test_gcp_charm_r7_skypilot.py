from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO / "configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87.json"
SKY_CONFIG = (
    REPO
    / "configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87-skypilot.json"
)
TASK = REPO / "grpo_h100_full_v5_charm_r7.yaml"
RUNNER = REPO / "scripts/gcp_full_v5_charm_r7_skypilot.sh"
DRIVER = REPO / "scripts/gcp_full_v5_charm_grpo.py"


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
            f"charm-r7-r87-skypilot-{phase}-render",
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": f"{REPO / 'src'}:{REPO}",
            "GLM47_FULL_V5_CONFIG_PATH": str(SKY_CONFIG),
            "SKYPILOT_TASK_ID": "sky-r7-test-task",
        },
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_r7_skypilot_overlay_binds_frozen_base_and_changes_only_execution() -> None:
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    overlay = json.loads(SKY_CONFIG.read_text(encoding="utf-8"))

    assert overlay["base_config_sha256"] == _sha256(BASE_CONFIG)
    assert overlay["profile_id"] == (
        "aider-charm-r7-admitted-mef-exact40-r87-skypilot"
    )
    assert overlay["execution"] == {
        "profile": "gcp-skypilot-h100-tp4-ep8-dp8-admitted-r7-mef-r87",
        "provisioner": "skypilot",
        "task_yaml": "grpo_h100_full_v5_charm_r7.yaml",
        "smoke_mode": "prepare-only",
        "smoke_optimizer_updates": 0,
        "canary_launcher": "managed-jobs",
        "admission_mode": "PRETRAINING_PASS_CANARY_REQUIRED",
        "checkpoint_disposition": "GATED",
        "charm_eligible": True,
    }
    assert base["reward"]["policy_version"] == "hybrid-bipolar45-mef-v1"
    assert base["reward"]["repair_bonus"] is False


def test_r7_skypilot_render_preserves_exact_training_and_reward_contract() -> None:
    rendered = _render("canary")
    environment = rendered["environment"]

    assert environment["GLM47_PROFILE_ID"] == (
        "aider-charm-r7-admitted-mef-exact40-r87-skypilot"
    )
    assert environment["GLM47_PROVISIONER"] == "skypilot"
    assert environment["GLM47_EXECUTION_PROFILE"] == (
        "gcp-skypilot-h100-tp4-ep8-dp8-admitted-r7-mef-r87"
    )
    assert environment["MILES_AIDER_REWARD_MODE"] == "hybrid_bipolar45_mef"
    assert environment["MILES_NUM_ROLLOUT"] == "5"
    assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "20"
    assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert environment["MILES_GRPO_ROLLOUT_SHUFFLE"] == "0"


def test_r7_skypilot_task_is_managed_spot_and_mounts_only_frozen_assets() -> None:
    task = yaml.safe_load(TASK.read_text(encoding="utf-8"))
    resources = task["resources"]
    mounts = task["file_mounts"]

    assert resources["cloud"] == "gcp"
    assert resources["region"] == "us-central1"
    assert resources["instance_type"] == "a3-highgpu-8g"
    assert resources["accelerators"] == "H100:8"
    assert resources["use_spot"] is True
    assert resources["job_recovery"] == {
        "strategy": "FAILOVER",
        "max_restarts_on_errors": 0,
    }
    assert resources["autostop"] == {"idle_minutes": 10, "down": True}
    runtime_mount = (
        "~/glm47-full-v5-assets/runtime/"
        "charm-r7-admitted-mef-exact40-r87-20260812T190000Z"
    )
    assert mounts[runtime_mount]["mode"] == "COPY"
    assert mounts[runtime_mount]["source"].endswith(
        "/charm-r7-admitted-mef-exact40-r87-20260812T190000Z"
    )
    assert "gcp_full_v5_charm_r7_skypilot.sh" in task["run"]
    assert "gcp-r7-admitted-mef-exact40-r87-skypilot.json" in task["run"]


def test_r7_skypilot_runner_fails_closed_for_canary_and_full() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(RUNNER)], check=True)

    assert 'MODE="${GLM47_SKYPILOT_MODE:-smoke}"' in text
    assert "gcloud compute" not in text
    assert "gcloud compute ssh" not in text
    assert "tmux" not in text
    assert "--phase canary" in text
    assert "--phase full" in text
    assert "PRETRAINING_RECEIPT_SHA256" in text
    assert "CANARY_TASK_MANIFEST_SHA256" in text
    assert "PROMOTION_RECEIPT_SHA256" in text
    assert "GLM47_CHARM_R7_FULL_TRAINING_AUTHORIZATION" in text


def test_skyignore_excludes_private_task_and_receipt_trees() -> None:
    patterns = (REPO / ".skyignore").read_text(encoding="utf-8").splitlines()
    for private_pattern in (
        "/dataset/jsonls/",
        "/dataset/registry/",
        "/dataset/reports/",
        "/dataset/tasks/",
        "/artifacts/",
        "/updated task/",
        "/.agents/",
    ):
        assert private_pattern in patterns
    assert "/dataset/configs/*" in patterns
    assert "!/dataset/configs/glm47-flash-tokenizer-manifest.json" in patterns
    assert "!/dataset/configs/glm47-flash-chat-template.jinja" in patterns
