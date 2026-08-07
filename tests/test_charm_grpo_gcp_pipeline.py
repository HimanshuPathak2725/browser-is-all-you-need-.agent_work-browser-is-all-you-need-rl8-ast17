from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from glm47_posttraining.integrations import miles_charm_compiler_grpo


REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE = REPO_ROOT / "scripts/gcp_charm_grpo_pipeline.py"
TRAIN_DOCKERFILE = REPO_ROOT / "docker/charm-compiler-grpo-gcp/Dockerfile"


def test_pipeline_inspect_is_fail_closed_without_required_gpu_topology() -> None:
    completed = subprocess.run(
        [sys.executable, str(PIPELINE), "inspect"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    receipt = json.loads(completed.stdout)
    assert receipt["simultaneous_gpu_heavy_jobs_supported"] is False
    assert receipt["concurrency_policy"]["policy"] == "single_gpu_heavy_job_per_host"
    assert receipt["concurrency_policy"]["lock_file"] == "/tmp/glm47-gpu-heavy.lock"


def test_training_image_excludes_heldout_prompt_and_evaluator_sources() -> None:
    text = TRAIN_DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY scripts scripts" not in text
    assert "COPY src/glm47_posttraining src/glm47_posttraining" not in text
    assert "public-pr-repo-eval" not in text
    assert "private_probes" not in text
    assert "test ! -e scripts/build_public_pr_eval_v2.py" in text
    assert "test ! -e src/glm47_posttraining/public_pr_eval" in text


def test_training_image_includes_compiler_guided_candidate_entrypoint() -> None:
    text = TRAIN_DOCKERFILE.read_text(encoding="utf-8")
    assert (
        "COPY scripts/run_charm_compiler_guided.py "
        "scripts/run_charm_compiler_guided.py"
    ) in text
    package_text = (
        REPO_ROOT / "scripts/package_charm_compiler_grpo_gcp.py"
    ).read_text(encoding="utf-8")
    assert 'Path("scripts/run_charm_compiler_guided.py")' in package_text


def test_training_image_pins_and_validates_libclang_runtime() -> None:
    text = TRAIN_DOCKERFILE.read_text(encoding="utf-8")
    assert "CPLUS_INCLUDE_PATH=/usr/local/lib/clang/18/include" in text
    assert "libclang==18.1.1" in text
    assert "assert validate_libclang_runtime()" in text


def test_charm_preflight_uses_the_caller_bound_verifier_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[str] = []
    monkeypatch.setenv("GLM47_CPP_SANDBOX_IMAGE", "verifier@sha256:bound")
    monkeypatch.setattr(
        miles_charm_compiler_grpo, "run_response_contract_preflight", lambda: None
    )
    monkeypatch.setattr(
        miles_charm_compiler_grpo,
        "run_sandbox_preflight",
        lambda *, image: observed.append(image),
    )
    miles_charm_compiler_grpo.main(["preflight"])
    assert observed == ["verifier@sha256:bound"]


def test_training_driver_binds_exact_three_epoch_schedule_and_group_validator() -> None:
    text = PIPELINE.read_text(encoding="utf-8")
    expected = {
        '"MILES_NUM_ROLLOUT": "18"',
        '"MILES_ROLLOUT_BATCH_SIZE": "19"',
        '"MILES_N_SAMPLES_PER_PROMPT": "8"',
        '"MILES_GLOBAL_BATCH_SIZE": "152"',
        '"MILES_EVAL_PROMPT_DATA"',
        '"MILES_ROLLOUT_SAMPLE_FILTER_PATH"',
        '"MILES_AIDER_REWARD_MODE": "production_ast17"',
        '"GLM47_CPP_SANDBOX_BACKEND": "docker"',
        '"WANDB_MODE": "offline"',
    }
    assert all(value in text for value in expected)
    assert "require_hardware(\"train\")" in text
    assert "require_hardware(\"eval\")" in text
    assert "exclusive_gpu_job(\"grpo-training\")" in text
    assert "exclusive_gpu_job(\"heldout-evaluation\")" in text


def test_source_native_reconstruction_is_explicit_and_path_bound() -> None:
    text = PIPELINE.read_text(encoding="utf-8")
    assert 'reconstruction.add_argument(\n        "--source-native-template"' in text
    assert "template != SOURCE_ADAPTER_DIR.resolve()" in text
    assert 'command.append("--source-native-template")' in text
    assert 'template_mount = "/source-adapter"' in text
    assert 'f"{os.getuid()}:{os.getgid()}"' in text


def test_preprojected_bridge_accepts_only_generic_immutable_eval_split(
    tmp_path: Path,
) -> None:
    source = REPO_ROOT / "artifacts/charm-compiler-grpo/r1/data"
    output = tmp_path / "runtime-data"
    miles_charm_compiler_grpo.main(
        [
            "build-data",
            "--tasks-dir",
            str(source),
            "--out",
            str(output),
            "--eval-splits",
            "validation,test",
            "--force",
        ]
    )
    assert (output / "grpo/train.jsonl").is_file()
    assert (output / "eval/mechanism_monitor.jsonl").is_file()
    with pytest.raises(ValueError, match="cannot be changed"):
        miles_charm_compiler_grpo.main(
            [
                "build-data",
                "--tasks-dir",
                str(source),
                "--out",
                str(tmp_path / "bad-data"),
                "--eval-splits",
                "validation",
            ]
        )


def test_heldout_evaluator_can_bind_new_adapter_without_changing_old_defaults() -> None:
    text = (
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py"
    ).read_text(encoding="utf-8")
    assert "expected_adapter_model_sha256: str = SOURCE_ADAPTER_SHA256" in text
    assert "expected_training_run_id: str = TRAINING_RUN_ID" in text
    assert '"--expected-adapter-model-sha256"' in text
    assert '"--expected-training-run-id"' in text
    assert '"training_run_id": args.expected_training_run_id' in text


def test_shell_entrypoint_does_not_enable_errexit() -> None:
    text = (REPO_ROOT / "scripts/gcp_charm_grpo_pipeline.sh").read_text(
        encoding="utf-8"
    )
    assert "set -e" not in text
    subprocess.run(
        ["bash", "-n", str(REPO_ROOT / "scripts/gcp_charm_grpo_pipeline.sh")],
        check=True,
    )
