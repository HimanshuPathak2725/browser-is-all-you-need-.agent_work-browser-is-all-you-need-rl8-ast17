from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER = REPO_ROOT / "scripts/gcp_full_v5_charm_grpo.py"
SMOKE_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-smoke.json"
FULL_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-full.json"
FOUR_TOPIC40_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-four-topic40.json"


def _render(config: Path, run_id: str) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "GLM47_FULL_V5_CONFIG_PATH": str(config),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_r6_v2_profiles_are_separate_quarantine_contracts() -> None:
    smoke = json.loads(SMOKE_CONFIG.read_text(encoding="utf-8"))
    full = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
    for profile in (smoke, full):
        assert profile["decision"] == "EXPERIMENTAL_UNADMITTED"
        assert profile["execution"]["checkpoint_disposition"] == "QUARANTINE_ONLY"
        assert profile["execution"]["charm_eligible"] is False
        assert profile["admission"]["full_training_authorized"] is False
        assert profile["admission"]["retroactive_admission_allowed"] is False
        assert profile["reward"]["implementation_mode"] == "hybrid_bipolar45"
        assert profile["reward"]["policy_version"] == "hybrid-bipolar45-v2"
        assert profile["gcp"]["provisioning_policy"] == "SPOT"
        assert profile["task_selection"] == {
            "harness_kind": "aider_cpp17",
            "ranking": "sha256-task-id-ascending-v1",
            "count": 475,
            "selected_task_ids_sha256": (
                "074b37fe2668f64bf5ceac2e70a5860716c2954fe8f5cad101471c6f3393615a"
            ),
        }
    assert smoke["full_training"]["rollout_updates"] == 1
    assert full["full_training"]["epochs"] == 3
    assert full["full_training"]["rollout_updates"] == 57


def test_r6_v2_render_uses_25_by_8_and_hybrid_reward() -> None:
    smoke = _render(SMOKE_CONFIG, "unadmitted-r6-v2-smoke-render")
    full = _render(FULL_CONFIG, "unadmitted-r6-v2-full-render")
    smoke_env = smoke["environment"]
    full_env = full["environment"]

    assert smoke_env["MILES_NUM_ROLLOUT"] == "1"
    assert full_env["MILES_NUM_ROLLOUT"] == "57"
    for environment in (smoke_env, full_env):
        assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "25"
        assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
        assert environment["MILES_GLOBAL_BATCH_SIZE"] == "200"
        assert environment["MILES_AIDER_REWARD_MODE"] == "hybrid_bipolar45"
        assert environment["GLM47_CHARM_ELIGIBLE"] == "0"
        assert environment["GLM47_CHECKPOINT_DISPOSITION"] == "QUARANTINE_ONLY"
        assert environment["GLM47_AIDER_MIN_KERNEL_VARIANCE_GROUPS"] == "2"


def test_r6_full_submit_requires_matching_v2_smoke_before_vm_start() -> None:
    text = (REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r6_v2_submit.sh").read_text(
        encoding="utf-8"
    )
    fetch = text.index('gcloud storage cp "${SMOKE_GCS}" "${SMOKE_RECEIPT}"')
    start = text.index('gcloud compute instances start "${INSTANCE}"')
    assert fetch < start
    assert "unadmitted-r6-hybrid45-v2-smoke" in text
    assert "I_AUTHORIZE_UNADMITTED_R6_HYBRID45_V2_57_UPDATE_EXPERIMENT_AND_GCP_COSTS" in text


def test_r6_v2_four_topic40_profile_is_exact_and_quarantined() -> None:
    profile = json.loads(FOUR_TOPIC40_CONFIG.read_text(encoding="utf-8"))
    selection = profile["task_selection"]
    task_ids = selection["task_ids"]
    observed_digest = hashlib.sha256(("\n".join(sorted(task_ids)) + "\n").encode()).hexdigest()

    assert profile["decision"] == "EXPERIMENTAL_UNADMITTED"
    assert profile["execution"]["checkpoint_disposition"] == "QUARANTINE_ONLY"
    assert profile["admission"]["full_training_authorized"] is False
    assert profile["full_training"]["train_targets"] == 40
    assert profile["full_training"]["epochs"] == 3
    assert profile["full_training"]["rollout_batch_size"] == 20
    assert profile["full_training"]["rollout_updates"] == 6
    assert profile["reward"]["tsan_preflight_required"] is False
    assert profile["reward"]["tsan_execution_allowed"] is False
    assert selection["ranking"] == "explicit-task-id-list-v1"
    assert len(task_ids) == len(set(task_ids)) == 40
    assert selection["topic_counts"] == {
        "clock": 10,
        "complex-numbers": 10,
        "spiral-matrix": 10,
        "zebra-puzzle": 10,
    }
    assert observed_digest == selection["selected_task_ids_sha256"]


def test_r6_v2_four_topic40_render_uses_six_20_by_8_updates() -> None:
    rendered = _render(
        FOUR_TOPIC40_CONFIG,
        "unadmitted-r6-v2-four-topic40-render",
    )
    environment = rendered["environment"]

    assert environment["MILES_NUM_ROLLOUT"] == "6"
    assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "20"
    assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert environment["MILES_GLOBAL_BATCH_SIZE"] == "160"
    assert environment["MILES_EVAL_INTERVAL"] == "6"
    assert environment["MILES_AIDER_REWARD_MODE"] == "hybrid_bipolar45"
    assert environment["GLM47_CPP_TSAN_PREFLIGHT_REQUIRED"] == "0"
    assert environment["GLM47_CPP_TSAN_EXECUTION_ALLOWED"] == "0"


def test_r6_v2_submit_routes_four_topic40_profile() -> None:
    submit = (REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r6_v2_submit.sh").read_text(
        encoding="utf-8"
    )
    headless = (REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r6_v2_headless.sh").read_text(
        encoding="utf-8"
    )

    for text in (submit, headless):
        assert "unadmitted-r6-v2-four-topic40-" in text
        assert "gcp-r6-hybrid45-v2-four-topic40.json" in text
        assert "FOUR_TOPIC40_6_UPDATE_EXPERIMENT_AND_GCP_COSTS" in text
