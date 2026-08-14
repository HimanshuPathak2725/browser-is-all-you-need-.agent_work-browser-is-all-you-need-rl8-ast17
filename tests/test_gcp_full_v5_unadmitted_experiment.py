from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER = REPO_ROOT / "scripts/gcp_full_v5_charm_grpo.py"
CONFIG = (
    REPO_ROOT
    / "configs/full_v5_charm_grpo/gcp-r2-unadmitted-experiment.json"
)
PRODUCTION_CONFIG = (
    REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r2-api-contracts.json"
)
HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_headless.sh"
SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_submit.sh"
TRAIN_LAUNCHER = REPO_ROOT / "scripts/train_grpo.sh"
AUTH_ENV = "GLM47_FULL_V5_UNADMITTED_EXPERIMENT_AUTHORIZATION"
AUTH_PHRASE = "I_AUTHORIZE_UNADMITTED_R2_57_UPDATE_EXPERIMENT_AND_GCP_COSTS"


def _env(config: Path = CONFIG) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "GLM47_FULL_V5_CONFIG_PATH": str(config),
    }


def test_profile_is_explicitly_unadmitted_and_quarantined() -> None:
    profile = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert profile["profile_id"] == (
        "aider-full-v5-experimental-unadmitted-r2-api-contracts"
    )
    assert profile["decision"] == "EXPERIMENTAL_UNADMITTED"
    assert profile["execution"]["admission_mode"] == "UNADMITTED_EXPERIMENT_ONLY"
    assert profile["execution"]["charm_eligible"] is False
    assert profile["execution"]["checkpoint_disposition"] == "QUARANTINE_ONLY"
    assert profile["gcp"]["result_destination"] == (
        "gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/"
        "unadmitted-full-v5-r2"
    )
    assert profile["training_image"]["local_name"] == (
        "glm47-full-v5-unadmitted-grpo:gcp-r2-api-contracts"
    )
    assert profile["verifier_image"]["local_name"] == (
        "glm47-full-v5-unadmitted-verifier:gcp-r2-api-contracts"
    )
    assert profile["admission"] == {
        "pretraining_receipt": "NOT_COMPLETED",
        "canary_task_manifest": "NOT_COMPLETED",
        "canary_result": "NOT_COMPLETED",
        "promotion_receipt": "NOT_COMPLETED",
        "full_training_authorized": False,
        "fixed26_role": "FROZEN_POST_TRAINING_EVALUATION_ONLY",
        "charm_eligible": False,
        "checkpoint_disposition": "QUARANTINE_ONLY",
        "retroactive_admission_allowed": False,
    }
    assert profile["experimental_contract"]["eligible_for_charm_promotion"] is False
    assert profile["experimental_contract"]["may_supply_failure_evidence_only"] is True
    assert profile["experimental_contract"]["later_charm_starting_checkpoint"] == (
        "synthmem-v1-ep50"
    )


def test_render_preserves_57_updates_but_marks_every_output_unadmitted() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r2-test-render",
        ],
        cwd=REPO_ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    environment = payload["environment"]
    assert payload["phase"] == "experimental"
    assert environment["MILES_NUM_ROLLOUT"] == "57"
    assert environment["MILES_SAVE_INTERVAL"] == "1"
    assert environment["MILES_EVAL_INTERVAL"] == "19"
    assert environment["GLM47_ADMISSION_STATUS"] == "NOT_COMPLETED"
    assert environment["GLM47_CHARM_ELIGIBLE"] == "0"
    assert environment["GLM47_CHECKPOINT_DISPOSITION"] == "QUARANTINE_ONLY"
    assert environment["GLM47_RETROACTIVE_ADMISSION_ALLOWED"] == "0"
    assert environment["TMPDIR"].endswith(
        "/runs/unadmitted-r2-test-render/runtime_state/tmp"
    )
    assert f'TMPDIR={environment["TMPDIR"]}' in payload["command"]
    host_run_root = environment["TMPDIR"].removesuffix("/runtime_state/tmp")
    assert f"{host_run_root}:{host_run_root}" in payload["command"]
    assert "unadmitted" in environment["WANDB_TAGS"]
    assert "quarantine" in environment["WANDB_TAGS"]
    assert ",charm," not in environment["WANDB_TAGS"]


def test_experiment_requires_separate_explicit_cost_authorization() -> None:
    environment = _env()
    environment.pop(AUTH_ENV, None)
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r2-missing-auth",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert AUTH_ENV in completed.stderr
    assert "quarantine-only disposition" in completed.stderr


def test_experiment_rejects_an_ambiguous_run_id_before_gpu_access() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "experimental",
            "--run-id",
            "looks-like-production",
        ],
        cwd=REPO_ROOT,
        env={**_env(), AUTH_ENV: AUTH_PHRASE},
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "must start with" in completed.stderr


def test_production_profile_cannot_use_experimental_phase() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r2-wrong-profile",
        ],
        cwd=REPO_ROOT,
        env={**_env(PRODUCTION_CONFIG), AUTH_ENV: AUTH_PHRASE},
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "requires the quarantined unadmitted profile" in completed.stderr


def test_unadmitted_profile_cannot_use_production_full_phase() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "full",
            "--run-id",
            "unadmitted-r2-production-attempt",
            "--promotion-receipt",
            "/does/not/exist.json",
        ],
        cwd=REPO_ROOT,
        env=_env(),
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "cannot run production full" in completed.stderr


def test_miles_rejects_inconsistent_quarantine_labels_before_runtime_access() -> None:
    completed = subprocess.run(
        ["bash", str(TRAIN_LAUNCHER)],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "MILES_RUN_ID": "looks-like-production",
            "GLM47_ADMISSION_STATUS": "NOT_COMPLETED",
            "GLM47_CHARM_ELIGIBLE": "0",
            "GLM47_CHECKPOINT_DISPOSITION": "QUARANTINE_ONLY",
            "GLM47_RETROACTIVE_ADMISSION_ALLOWED": "0",
            "MILES_ROOT": "/does/not/exist",
        },
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "quarantine-only runs require" in completed.stderr
    assert "Missing Miles root" not in completed.stderr


def test_miles_accepts_only_frozen_unadmitted_quarantine_prefixes_before_runtime_access() -> None:
    for run_id in (
        "unadmitted-r2-contract",
        "unadmitted-r3-smoke-contract",
        "unadmitted-r3-full-contract",
        "unadmitted-r4-smoke-contract",
        "unadmitted-r4-full-contract",
        "unadmitted-r5-smoke-contract",
        "unadmitted-r5-full-contract",
        "unadmitted-r6-v2-smoke-contract",
        "unadmitted-r6-v2-four-topic40-contract",
        "unadmitted-r6-v2-full-contract",
        "unadmitted-r8-r87-20260813T182102Z-attempt-20260813T183109Z-8c8324c2",
    ):
        completed = subprocess.run(
            ["bash", str(TRAIN_LAUNCHER)],
            cwd=REPO_ROOT,
            env={
                **os.environ,
                "MILES_RUN_ID": run_id,
                "GLM47_ADMISSION_STATUS": "NOT_COMPLETED",
                "GLM47_CHARM_ELIGIBLE": "0",
                "GLM47_CHECKPOINT_DISPOSITION": "QUARANTINE_ONLY",
                "GLM47_RETROACTIVE_ADMISSION_ALLOWED": "0",
                "MILES_ROOT": "/does/not/exist",
            },
            text=True,
            capture_output=True,
        )
        assert completed.returncode == 2
        output = completed.stdout + completed.stderr
        assert "Missing Miles root" in output
        assert "quarantine-only runs require" not in output


def test_headless_pipeline_is_detached_and_never_invokes_production_full() -> None:
    for path in (HEADLESS, SUBMIT):
        subprocess.run(["bash", "-n", str(path)], check=True)
    headless = HEADLESS.read_text(encoding="utf-8")
    submit = SUBMIT.read_text(encoding="utf-8")
    assert "nohup" in headless
    assert '"${PYTHON_BIN}" "${DRIVER}" prepare' in headless
    assert "--phase experimental" in headless
    assert "--phase full" not in headless
    assert "scripts/train_grpo.sh" in headless
    assert "scripts/train_grpo.sh" in submit
    assert "QUARANTINE" not in submit or "unadmitted" in submit
    assert "gcp_full_v5_unadmitted_headless.sh" in submit
    assert "gcloud compute instances start" in submit
    assert "remote staged build-context hash does not match local bytes" in submit
    assert 'REMOTE_ROOT_BASE="browser-is-all-you-need-staging"' in submit
    assert "src/glm47_posttraining/integrations" in submit
    assert "docker/full-v5-charm-grpo-gcp/Dockerfile" in submit
    assert "GLM47_SOURCE_COMMIT=${SOURCE_COMMIT}" in submit
    assert "I_AUTHORIZE_FULL_V5_CHARM_57_UPDATE_TRAINING" not in headless
    assert "I_AUTHORIZE_FULL_V5_CHARM_57_UPDATE_TRAINING" not in submit


def test_source_commit_override_supports_fresh_remote_staging() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r2-source-commit-override",
        ],
        cwd=REPO_ROOT,
        env={**_env(), "GLM47_SOURCE_COMMIT": "a" * 40},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["environment"]["GLM47_SOURCE_COMMIT"] == "a" * 40
