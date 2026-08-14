from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "grpo_h100_full_v5_unadmitted_r2.yaml"
CONFIG = ROOT / "configs/full_v5_charm_grpo/gcp-r2-unadmitted-skypilot.json"
DRIVER = ROOT / "scripts/gcp_full_v5_charm_grpo.py"
TMUX_RUNNER = ROOT / "scripts/gcp_full_v5_unadmitted_tmux.sh"


def test_unadmitted_skypilot_task_is_quarantined_and_tmux_backed() -> None:
    task = yaml.safe_load(TASK.read_text(encoding="utf-8"))
    resources = task["resources"]
    mounts = task["file_mounts"]
    assert resources["cloud"] == "gcp"
    assert resources["instance_type"] == "a3-highgpu-8g"
    assert resources["accelerators"] == "H100:8"
    assert resources["use_spot"] is True
    runtime = mounts[
        "~/glm47-full-v5-assets/runtime/aider_cpp_rl_full_v5_api_contracts_r2"
    ]
    assert runtime["source"].endswith(
        "/runtime/aider_cpp_rl_full_v5_api_contracts_r2"
    )
    assert "gcp_full_v5_unadmitted_tmux.sh" in task["run"]
    assert "GLM47_HEADLESS_WAIT=1" in task["run"]
    assert "gcp-r2-unadmitted-skypilot.json" in task["run"]
    assert "I_AUTHORIZE_FULL_V5_CHARM_57_UPDATE_TRAINING" not in TASK.read_text()

    text = TMUX_RUNNER.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(TMUX_RUNNER)], check=True)
    assert "tmux new-session -d" in text
    assert "tmux has-session" in text
    assert '"${PYTHON_BIN}" "${DRIVER}" prepare' in text
    assert "--phase experimental" in text
    assert "--phase full" not in text


def test_skypilot_profile_renders_only_unadmitted_57_update_phase() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r2-skypilot-test",
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "GLM47_FULL_V5_CONFIG_PATH": str(CONFIG),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    env = json.loads(completed.stdout)["environment"]
    assert env["GLM47_PROVISIONER"] == "skypilot"
    assert env["GLM47_CHARM_ELIGIBLE"] == "0"
    assert env["GLM47_CHECKPOINT_DISPOSITION"] == "QUARANTINE_ONLY"
    assert env["MILES_NUM_ROLLOUT"] == "57"
