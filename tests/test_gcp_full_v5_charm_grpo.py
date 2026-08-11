from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE = REPO_ROOT / "scripts/gcp_full_v5_charm_grpo.py"
CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r1.json"
TRAIN_DOCKERFILE = REPO_ROOT / "docker/full-v5-charm-grpo-gcp/Dockerfile"


def _render(phase: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(PIPELINE), "render", "--phase", phase],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_profile_is_gcp_only_and_fail_closed() -> None:
    profile = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert profile["profile_id"] == "aider-full-v5-production-ast17-gcp-r1"
    assert profile["decision"] == "NOT_COMPLETED"
    assert profile["modal_policy"]["default"] == "DENY"
    assert profile["gcp"]["machine_type"] == "a3-highgpu-8g"
    assert profile["gcp"]["gpu_count"] == 8
    assert profile["gcp"]["gpu_model_contains"] == "H100"
    adapter = profile["starting_adapter"]
    assert adapter["profile"] == "synthmem-v1-ep50"
    assert adapter["checkpoint_path"] == "checkpoints/sft_lora_r16/iter_0000649"
    assert adapter["epoch"] == 50
    assert adapter["optimizer_iteration"] == 649
    assert (
        adapter["adapter_model_sha256"]
        == "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a"
    )
    assert adapter["gcp_asset_status"] == "AVAILABLE"
    profile_text = CONFIG.read_text(encoding="utf-8")
    assert "iter_0001299" not in profile_text
    assert "5ca6a0cbede843e8c042ebb1004a80e85d85686974063cb9bd0540e236aab6ca" not in profile_text
    assert "bdd808bf98d26b467af7fec1a20d7ed6502bac0ffd50eae9cb6a1e702613daaa" not in profile_text
    assert profile["admission"]["full_training_authorized"] is False
    assert (
        profile["admission"]["fixed26_role"]
        == "FROZEN_POST_TRAINING_EVALUATION_ONLY"
    )


def test_canary_contract_is_exact_charm_promotion_canary() -> None:
    profile = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert profile["canary"] == {
        "task_count": 20,
        "epochs": 5,
        "rollout_batch_size": 20,
        "samples_per_prompt": 8,
        "global_batch_size": 160,
        "rollout_updates": 5,
        "matched_trials": 4,
        "selection_policy": {
            "compile_rate_weight": 0.4,
            "hidden_test_rate_weight": 0.4,
            "validation_loss_weight": 0.2,
            "always_final": False,
        },
        "requires_pretraining_admission_pass": True,
    }
    env = _render("canary")["environment"]
    assert env["MILES_NUM_ROLLOUT"] == "5"
    assert env["MILES_ROLLOUT_BATCH_SIZE"] == "20"
    assert env["MILES_GLOBAL_BATCH_SIZE"] == "160"
    assert env["MILES_SAVE_INTERVAL"] == "1"


def test_full_contract_preserves_full_v5_schedule_and_charm_controls() -> None:
    payload = _render("full")
    env = payload["environment"]
    assert env["MILES_NUM_ROLLOUT"] == "57"
    assert env["MILES_ROLLOUT_BATCH_SIZE"] == "29"
    assert env["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert env["MILES_GLOBAL_BATCH_SIZE"] == "232"
    assert env["MILES_APPLY_CHAT_TEMPLATE_KWARGS"] == '{"enable_thinking": true}'
    assert env["MILES_SEQ_LENGTH"] == "34816"
    assert env["MILES_ROLLOUT_MAX_RESPONSE_LEN"] == "32768"
    assert env["MILES_MAX_TOKENS_PER_GPU"] == "49152"
    assert env["MILES_LR"] == "5e-7"
    assert env["MILES_NO_REF"] == "0"
    assert env["MILES_USE_KL_LOSS"] == "1"
    assert env["MILES_KL_LOSS_COEF"] == "0.02"
    assert env["MILES_SAVE_INTERVAL"] == "1"
    assert env["MILES_TENSOR_MODEL_PARALLEL_SIZE"] == "4"
    assert env["MILES_EXPERT_MODEL_PARALLEL_SIZE"] == "8"
    assert env["MILES_AIDER_REWARD_MODE"] == "production_ast17"
    assert env["MILES_SKIP_RUNTIME_PREFLIGHT"] == "0"
    assert env["GLM47_CPP_SANDBOX_BACKEND"] == "docker"
    assert env["GLM47_CPP_SANDBOX_UNSHARE_NET"] == "1"
    assert env["GLM47_AIDER_REQUIRE_UNIQUE_TASK_GROUPS"] == "1"
    assert (
        env["MILES_EXPECTED_SOURCE_ADAPTER_SHA256"]
        == "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a"
    )
    assert env["MILES_EXPECTED_SOURCE_TENSORS"] == "9741"
    assert env["MILES_EXPECTED_STRIPPED_TENSORS"] == "207"
    assert (
        env["MILES_NATIVE_RECONSTRUCTION_MANIFEST_PATH"]
        == "/starting-adapter/native_reconstruction_manifest.json"
    )
    assert len(env["MILES_EXPECTED_NATIVE_RECONSTRUCTION_MANIFEST_SHA256"]) == 64
    assert env["GLM47_AIDER_REQUIRE_SIGNAL"] == "1"
    assert "--network" in payload["command"]
    assert "none" in payload["command"]


def test_full_training_requires_promotion_and_explicit_cost_authorization() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(PIPELINE),
            "train",
            "--phase",
            "full",
            "--run-id",
            "authorization-test",
            "--promotion-receipt",
            "/does/not/exist.json",
        ],
        cwd=REPO_ROOT,
        env={
            key: value
            for key, value in {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}.items()
            if key != "GLM47_FULL_V5_CHARM_FULL_TRAINING_AUTHORIZATION"
        },
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "full training is not authorized" in completed.stderr


def test_training_image_excludes_modal_and_fixed26_evaluator_sources() -> None:
    text = TRAIN_DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY scripts scripts" not in text
    assert "COPY src/glm47_posttraining src/glm47_posttraining" not in text
    assert "COPY examples/modal" not in text
    assert "public-pr-repo-eval" not in text
    assert "test ! -e examples/modal" in text
    assert "test ! -e src/glm47_posttraining/public_pr_eval" in text
    assert 'glm47.modal.policy="denied"' in text


def test_full_v5_aider_cpp17_descriptor_contract_is_schema_compatible() -> None:
    task = AiderPolyglotTask.model_validate(
        {
            "task_id": "full-v5-schema-probe",
            "exercise": "schema-probe",
            "split": "train",
            "harness_kind": "aider_cpp17",
            "exercise_dir": "environments/schema-probe",
            "editable_files": ["answer.cpp"],
            "prompt": [{"role": "user", "content": "Implement answer.cpp."}],
            "prompt_contract": "sft-v5-user-v1",
            "response_contract": "aider-whole-file-v1",
            "reward_contract": "dense-semantic-v2",
        }
    )
    assert task.harness_kind == "aider_cpp17"
    assert task.prompt_contract == "sft-v5-user-v1"


def test_asset_verification_checks_manifest_and_every_listed_model_file() -> None:
    text = PIPELINE.read_text(encoding="utf-8")
    assert '_require_hash(\n        MODEL_DIR / ".source-manifest.sha256"' in text
    assert 'ADAPTER_DIR / ".training-run-id"' in text
    assert 'ADAPTER_DIR / "native_reconstruction_manifest.json"' in text
    assert 'roundtrip.get("all_source_hf_tensor_bytes_exact") is not True' in text
    assert (
        '_require_hash(ADAPTER_DIR / name, metadata["sha256"], f"native shard {name}")'
        in text
    )
    assert '["sha256sum", "--check", "--quiet", "--strict", path.name]' in text


def test_spot_run_artifacts_are_periodically_and_finally_synced_to_gcs() -> None:
    profile = json.loads(CONFIG.read_text(encoding="utf-8"))
    text = PIPELINE.read_text(encoding="utf-8")
    assert profile["tracking"]["result_sync_interval_seconds"] == 60
    assert '"gcloud",\n                "storage",\n                "rsync"' in text
    assert '["gsutil", "-m", "rsync", "-r"' in text
    assert "with periodic_result_sync(" in text
    assert "def prepare(args: argparse.Namespace)" in text
    assert "inventory = require_h100()" in text
    assert '"status": "failed"' in text
    assert 'host_run_root / "execution-receipt.json"' in text
