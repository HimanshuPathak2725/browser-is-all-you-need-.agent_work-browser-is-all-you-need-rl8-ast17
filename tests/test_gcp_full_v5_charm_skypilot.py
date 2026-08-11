from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = REPO_ROOT / "grpo_h100_full_v5_charm.yaml"
RUNNER_PATH = REPO_ROOT / "scripts/gcp_full_v5_charm_skypilot.sh"
DRIVER_PATH = REPO_ROOT / "scripts/gcp_full_v5_charm_grpo.py"
CONFIG_PATH = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r1.json"


def test_skypilot_task_is_the_exact_gcp_h100_grpo_profile() -> None:
    task = yaml.safe_load(TASK_PATH.read_text(encoding="utf-8"))
    resources = task["resources"]
    mounts = task["file_mounts"]

    assert task["name"] == "glm47-full-v5-charm-grpo"
    assert resources["cloud"] == "gcp"
    assert resources["region"] == "us-central1"
    assert resources["instance_type"] == "a3-highgpu-8g"
    assert resources["accelerators"] == "H100:8"
    assert resources["network_tier"] == "best"
    assert resources["disk_size"] == 500
    assert resources["disk_tier"] == "high"
    assert resources["use_spot"] is True
    assert resources["autostop"] == {"idle_minutes": 10, "down": True}

    assert mounts["~/glm47-full-v5-assets/model/GLM-4.7-Flash"] == {
        "source": (
            "gs://lifeandhalf-24122025-w8-biayn/glm47-public-pr-eval/"
            "assets/model/GLM-4.7-Flash"
        ),
        "mode": "COPY",
    }
    assert mounts["~/glm47-full-v5-assets/synthmem-v1-ep50/adapter"] == {
        "source": (
            "gs://lifeandhalf-24122025-w8-biayn/glm47-full-v5/"
            "assets/synthmem-v1-ep50-grpo-adapter"
        ),
        "mode": "COPY",
    }
    assert mounts["~/glm47-full-v5-assets/runtime/aider_cpp_rl_full_v5"][
        "mode"
    ] == "COPY"
    assert mounts["~/glm47-results-store"] == {
        "source": "gs://lifeandhalf-24122025-w8-biayn",
        "mode": "MOUNT",
    }

    setup = task["setup"]
    run = task["run"]
    assert "EXPECTED_GPU_COUNT=8" in setup
    assert "EXPECTED_GPU_MODEL=H100" in setup
    assert run.count("gcp_full_v5_charm_skypilot.sh") == 1
    assert 'GLM47_EXECUTION_PROFILE="gcp-skypilot-h100-tp4-ep8-dp8"' in run
    assert 'GLM47_PROVISIONER="skypilot"' in run


def test_skypilot_runner_is_smoke_first_and_cannot_start_full_training() -> None:
    text = RUNNER_PATH.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(RUNNER_PATH)], check=True)

    assert 'MODE="${GLM47_SKYPILOT_MODE:-smoke}"' in text
    assert text.count('python3 "${DRIVER}" prepare') == 1
    assert text.count('python3 "${DRIVER}" train') == 1
    assert "--phase canary" in text
    assert "--phase full" not in text
    assert "full training is not exposed here" in text
    assert "GLM47_FULL_V5_CHARM_FULL_TRAINING_AUTHORIZATION" not in text
    assert "PRETRAINING_RECEIPT_SHA256" in text
    assert "CANARY_TASK_MANIFEST_SHA256" in text
    assert "FULL_V5_CHARM_SKYPILOT_SMOKE=passed" in text


def test_profile_binds_skypilot_without_changing_grpo_parallelism() -> None:
    profile = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert profile["execution"] == {
        "profile": "gcp-skypilot-h100-tp4-ep8-dp8",
        "provisioner": "skypilot",
        "task_yaml": "grpo_h100_full_v5_charm.yaml",
        "smoke_mode": "prepare-only",
        "smoke_optimizer_updates": 0,
        "canary_launcher": "managed-jobs",
    }
    assert profile["parallelism"] == {
        "tensor": 4,
        "pipeline": 1,
        "context": 1,
        "expert": 8,
        "expert_tensor": 1,
        "sglang_data_parallel": 8,
    }


def test_driver_accepts_ephemeral_skypilot_asset_and_result_roots() -> None:
    asset_root = "/tmp/glm47-skypilot-test-assets"
    result_root = "/tmp/glm47-skypilot-test-results"
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER_PATH),
            "render",
            "--phase",
            "canary",
            "--run-id",
            "skypilot-render-test",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "GLM47_FULL_V5_ASSET_ROOT": asset_root,
            "GLM47_FULL_V5_RESULT_ROOT": result_root,
            "SKYPILOT_TASK_ID": "sky-test-task",
        },
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    command = payload["command"]
    environment = payload["environment"]

    assert f"{asset_root}/model:/root/models:ro" in command
    assert f"{asset_root}/synthmem-v1-ep50/adapter:/starting-adapter:ro" in command
    assert f"{result_root}:/results" in command
    assert environment["GLM47_PROVISIONER"] == "skypilot"
    assert environment["GLM47_EXECUTION_PROFILE"] == (
        "gcp-skypilot-h100-tp4-ep8-dp8"
    )
    assert environment["GLM47_SKYPILOT_TASK_ID"] == "sky-test-task"
