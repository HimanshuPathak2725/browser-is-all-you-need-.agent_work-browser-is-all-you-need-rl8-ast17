from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.create_unadmitted_grpo_smoke_receipt as smoke_module
import scripts.gcp_full_v5_charm_grpo as pipeline_module


REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER = REPO_ROOT / "scripts/gcp_full_v5_charm_grpo.py"
CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r3-unadmitted-thinking-final-v1-smoke.json"
FULL_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r3-unadmitted-thinking-final-v1.json"
SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_smoke_submit.sh"
HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_smoke_headless.sh"
FINALIZER = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_smoke_finalize.sh"
FULL_SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r3_submit.sh"
FULL_HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r3_headless.sh"
R4_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r4-unadmitted-thinking-final-pack34816-v1-smoke.json"
R4_FULL_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r4-unadmitted-thinking-final-pack34816-v1.json"
R4_SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r4_smoke_submit.sh"
R4_HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r4_smoke_headless.sh"
R4_FINALIZER = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r4_smoke_finalize.sh"
R4_FULL_SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r4_submit.sh"
R4_FULL_HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r4_headless.sh"
R5_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r5-unadmitted-thinking-final-resp16384-pack18432-v1-smoke.json"
R5_FULL_CONFIG = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r5-unadmitted-thinking-final-resp16384-pack18432-v1.json"
R5_SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r5_smoke_submit.sh"
R5_HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r5_smoke_headless.sh"
R5_FINALIZER = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r5_smoke_finalize.sh"
R5_FULL_SUBMIT = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r5_submit.sh"
R5_FULL_HEADLESS = REPO_ROOT / "scripts/gcp_full_v5_unadmitted_r5_headless.sh"


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "GLM47_FULL_V5_CONFIG_PATH": str(CONFIG),
    }


def _write_checkpoint(path: Path) -> list[dict[str, object]]:
    adapter = path / "adapter"
    adapter.mkdir(parents=True)
    files = {
        "adapter_model.bin": b"updated-adapter",
        "adapter_config.json": b'{"r": 16}\n',
    }
    for rank in range(8):
        files[f"adapter_megatron_tp{rank % 4}_pp0_ep{rank}.pt"] = f"native-{rank}".encode()
        files[f"training_state_rank{rank}.pt"] = f"state-{rank}".encode()
    records: list[dict[str, object]] = []
    for name, content in sorted(files.items()):
        target = adapter / name
        target.write_bytes(content)
        records.append(
            {
                "path": f"adapter/{name}",
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return records


def test_smoke_profile_renders_exactly_one_quarantined_update() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r3-smoke-test",
        ],
        cwd=REPO_ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    environment = payload["environment"]
    profile = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert profile["full_training"]["rollout_updates"] == 1
    assert profile["full_training"]["save_interval"] == 1
    assert profile["reward"]["response_contract"] == "glm47-thinking-final-answer-v1"
    assert profile["tracking"]["sync_contract"] == "durable-marker-last-v1"
    assert environment["MILES_NUM_ROLLOUT"] == "1"
    assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "29"
    assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert environment["GLM47_CHARM_ELIGIBLE"] == "0"


def test_smoke_requires_its_distinct_cost_authorization() -> None:
    environment = _env()
    environment.pop("GLM47_FULL_V5_UNADMITTED_SMOKE_AUTHORIZATION", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r3-smoke-missing-auth",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "GLM47_FULL_V5_UNADMITTED_SMOKE_AUTHORIZATION" in completed.stderr


def test_r3_full_requires_smoke_pass_before_gpu_access() -> None:
    environment = {
        **_env(),
        "GLM47_FULL_V5_CONFIG_PATH": str(FULL_CONFIG),
        "GLM47_FULL_V5_UNADMITTED_EXPERIMENT_AUTHORIZATION": (
            "I_AUTHORIZE_UNADMITTED_R3_57_UPDATE_EXPERIMENT_AND_GCP_COSTS"
        ),
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "train",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r3-full-missing-smoke",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "requires the one-update smoke PASS receipt" in completed.stderr


def test_r3_full_pipeline_fetches_smoke_receipt_before_starting_vm() -> None:
    for path in (FULL_SUBMIT, FULL_HEADLESS):
        subprocess.run(["bash", "-n", str(path)], check=True)
    submit = FULL_SUBMIT.read_text(encoding="utf-8")
    headless = FULL_HEADLESS.read_text(encoding="utf-8")
    assert submit.index('gcloud storage cp "${SMOKE_GCS}"') < submit.index(
        "gcloud compute instances start"
    )
    assert "--smoke-receipt" in headless
    assert "--expected-smoke-receipt-sha256" in headless
    assert "unadmitted-r3-full-" in submit
    assert "unadmitted-r3-full-" in headless


def test_smoke_headless_pipeline_certifies_but_never_launches_full() -> None:
    for path in (SUBMIT, HEADLESS, FINALIZER):
        subprocess.run(["bash", "-n", str(path)], check=True)
    submit = SUBMIT.read_text(encoding="utf-8")
    headless = HEADLESS.read_text(encoding="utf-8")
    finalizer = FINALIZER.read_text(encoding="utf-8")
    assert "create_unadmitted_grpo_smoke_receipt.py" in submit
    assert "gcp_full_v5_unadmitted_smoke_finalize.sh" in headless
    assert "gcloud storage rsync" in finalizer
    assert "smoke-gate-receipt.json" in finalizer
    assert "--phase full" not in submit + headless + finalizer


def test_r4_retry_reduces_only_dynamic_pack_and_preserves_grpo_shape() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r4-smoke-test",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "GLM47_FULL_V5_CONFIG_PATH": str(R4_CONFIG),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    environment = payload["environment"]
    profile = json.loads(R4_CONFIG.read_text(encoding="utf-8"))
    assert profile["profile_id"].endswith("r4-thinking-final-pack34816-v1-smoke")
    assert profile["full_training"]["maximum_tokens_per_gpu"] == 34816
    assert environment["MILES_MAX_TOKENS_PER_GPU"] == "34816"
    assert environment["MILES_SEQ_LENGTH"] == "34816"
    assert environment["MILES_ROLLOUT_MAX_RESPONSE_LEN"] == "32768"
    assert environment["MILES_NUM_ROLLOUT"] == "1"
    assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "29"
    assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert environment["MILES_GLOBAL_BATCH_SIZE"] == "232"


def test_r4_full_is_on_demand_and_bound_to_r4_smoke() -> None:
    profile = json.loads(R4_FULL_CONFIG.read_text(encoding="utf-8"))
    assert profile["gcp"]["provisioning_policy"] == "STANDARD"
    assert profile["full_training"]["maximum_tokens_per_gpu"] == 34816
    for path in (R4_SUBMIT, R4_HEADLESS, R4_FINALIZER, R4_FULL_SUBMIT, R4_FULL_HEADLESS):
        subprocess.run(["bash", "-n", str(path)], check=True)
    submit = R4_FULL_SUBMIT.read_text(encoding="utf-8")
    finalizer = R4_FINALIZER.read_text(encoding="utf-8")
    assert submit.index('gcloud storage cp "${SMOKE_GCS}"') < submit.index(
        "gcloud compute instances start"
    )
    assert 'provisioning_model}' in submit
    assert '!= "STANDARD"' in submit
    assert "permits_r4_57_update_launch" in finalizer
    assert "--expected-profile-id" in finalizer


def test_r5_retry_caps_response_and_dynamic_pack_without_changing_batch() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(DRIVER),
            "render",
            "--phase",
            "experimental",
            "--run-id",
            "unadmitted-r5-smoke-test",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "GLM47_FULL_V5_CONFIG_PATH": str(R5_CONFIG),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    environment = payload["environment"]
    profile = json.loads(R5_CONFIG.read_text(encoding="utf-8"))
    assert profile["profile_id"].endswith(
        "r5-thinking-final-resp16384-pack18432-v1-smoke"
    )
    assert profile["full_training"]["maximum_response_length"] == 16384
    assert profile["full_training"]["maximum_tokens_per_gpu"] == 18432
    assert environment["MILES_MAX_TOKENS_PER_GPU"] == "18432"
    assert environment["MILES_SEQ_LENGTH"] == "34816"
    assert environment["MILES_EVAL_MAX_RESPONSE_LEN"] == "16384"
    assert environment["MILES_ROLLOUT_MAX_RESPONSE_LEN"] == "16384"
    assert environment["MILES_NUM_ROLLOUT"] == "1"
    assert environment["MILES_ROLLOUT_BATCH_SIZE"] == "29"
    assert environment["MILES_N_SAMPLES_PER_PROMPT"] == "8"
    assert environment["MILES_GLOBAL_BATCH_SIZE"] == "232"


def test_r5_full_is_on_demand_and_bound_to_r5_smoke() -> None:
    profile = json.loads(R5_FULL_CONFIG.read_text(encoding="utf-8"))
    assert profile["gcp"]["provisioning_policy"] == "STANDARD"
    assert profile["full_training"]["maximum_response_length"] == 16384
    assert profile["full_training"]["maximum_tokens_per_gpu"] == 18432
    for path in (
        R5_SUBMIT,
        R5_HEADLESS,
        R5_FINALIZER,
        R5_FULL_SUBMIT,
        R5_FULL_HEADLESS,
    ):
        subprocess.run(["bash", "-n", str(path)], check=True)
    submit = R5_FULL_SUBMIT.read_text(encoding="utf-8")
    finalizer = R5_FINALIZER.read_text(encoding="utf-8")
    assert submit.index('gcloud storage cp "${SMOKE_GCS}"') < submit.index(
        "gcloud compute instances start"
    )
    assert 'provisioning_model}' in submit
    assert '!= "STANDARD"' in submit
    assert "permits_r5_57_update_launch" in finalizer
    assert pipeline_module.EXPERIMENT_R5_SMOKE_PROFILE_ID in finalizer


def test_certifier_detects_memory_saver_cuda_oom() -> None:
    log = "[torch_memory_saver.cpp] CUresult error: 2 (out of memory)"
    assert smoke_module.FATAL_RUNTIME_PATTERNS["cuda_oom"].search(log)


def test_r4_smoke_receipt_binding_rejects_cross_profile_reuse(tmp_path: Path) -> None:
    receipt = {
        "schema_version": "glm47-unadmitted-grpo-smoke-v1",
        "decision": "PASS",
        "profile_id": pipeline_module.EXPERIMENT_R4_SMOKE_PROFILE_ID,
        "permits_r4_57_update_launch": True,
        "charm_eligible": False,
        "checkpoint_disposition": "QUARANTINE_ONLY",
        "retroactive_admission_allowed": False,
        "checkpoint": {"roundtrip_verified": True},
        "training": {"optimizer_updates_proven": 1},
    }
    path = tmp_path / "smoke.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    contract = pipeline_module.PROFILE_CONTRACTS[
        pipeline_module.EXPERIMENT_R4_PROFILE_ID
    ]

    observed = pipeline_module._experimental_smoke_receipt(
        str(path), digest, profile_contract=contract
    )

    assert observed["profile_id"] == pipeline_module.EXPERIMENT_R4_SMOKE_PROFILE_ID
    with pytest.raises(RuntimeError, match="complete matching PASS"):
        pipeline_module._experimental_smoke_receipt(
            str(path),
            digest,
            profile_contract=pipeline_module.PROFILE_CONTRACTS[
                pipeline_module.EXPERIMENT_R3_PROFILE_ID
            ],
        )


def test_r4_provisioning_policy_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = json.loads(R4_FULL_CONFIG.read_text(encoding="utf-8"))
    monkeypatch.setattr(pipeline_module, "metadata_value", lambda *_args: "FALSE")
    assert pipeline_module.require_provisioning_policy(profile) == {
        "provisioning_policy": "STANDARD",
        "metadata_preemptible": "FALSE",
    }
    monkeypatch.setattr(pipeline_module, "metadata_value", lambda *_args: "TRUE")
    with pytest.raises(RuntimeError, match="provisioning policy mismatch"):
        pipeline_module.require_provisioning_policy(profile)


def test_complete_marker_validates_local_and_downloaded_checkpoint(tmp_path: Path) -> None:
    local = tmp_path / "local/iter_0000000"
    recovered = tmp_path / "recovered/iter_0000000"
    files = _write_checkpoint(local)
    _write_checkpoint(recovered)
    manifest = {
        "schema_version": "glm47-gcs-checkpoint-complete-v1",
        "status": "COMPLETE",
        "iteration": 0,
        "checkpoint": "iter_0000000",
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
    }
    marker = {
        **manifest,
        "manifest_sha256": smoke_module.canonical_sha256(manifest),
        "published_at_utc": "2026-08-11T00:00:00+00:00",
        "gcs_destination": "gs://bucket/run/checkpoints/iter_0000000",
    }
    marker_path = recovered / "COMPLETE.json"
    marker_path.write_text(json.dumps(marker), encoding="utf-8")

    observed = smoke_module.validate_complete_marker(
        marker_path, local_checkpoint=local, recovered_checkpoint=recovered
    )

    assert observed["file_count"] == 18
    assert observed["total_bytes"] > 0


def test_complete_marker_rejects_roundtrip_tampering(tmp_path: Path) -> None:
    local = tmp_path / "local/iter_0000000"
    recovered = tmp_path / "recovered/iter_0000000"
    files = _write_checkpoint(local)
    _write_checkpoint(recovered)
    manifest = {
        "schema_version": "glm47-gcs-checkpoint-complete-v1",
        "status": "COMPLETE",
        "iteration": 0,
        "checkpoint": "iter_0000000",
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "files": files,
    }
    marker = {
        **manifest,
        "manifest_sha256": smoke_module.canonical_sha256(manifest),
        "gcs_destination": "gs://bucket/run/checkpoints/iter_0000000",
    }
    marker_path = recovered / "COMPLETE.json"
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    (recovered / "adapter/training_state_rank7.pt").write_bytes(b"tampered")

    with pytest.raises(RuntimeError, match="size mismatch|digest mismatch"):
        smoke_module.validate_complete_marker(
            marker_path, local_checkpoint=local, recovered_checkpoint=recovered
        )


def test_rollout_receipt_replays_post_thinking_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = (
        "draft\nCMakeLists.txt\n```cmake\nproject(unsafe)\n```\n"
        "</think>\nexample.cpp\n```cpp\nint answer(){return 42;}\n```\n"
    )
    final = raw.partition("</think>")[2]
    reward = {
        "response": raw,
        "response_contract": "glm47-thinking-final-answer-v1",
        "thinking_boundary_applied": True,
        "scored_response_sha256": hashlib.sha256(final.encode()).hexdigest(),
        "format_valid": True,
    }
    payload = {"samples": [{"response": raw, "reward": reward} for _ in range(232)]}
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(load=lambda *_args, **_kwargs: payload))
    rollout = tmp_path / "grpo_0.pt"
    rollout.write_bytes(b"rollout")

    record = smoke_module.validate_rollout(rollout)

    assert record["sample_count"] == 232
    assert record["exact_final_answer_rate"] == 1.0
    assert record["thinking_boundary_count"] == 232


def test_smoke_certifier_ignores_expected_evaluation_rollout(tmp_path: Path) -> None:
    rollout_root = tmp_path / "rollout_dumps"
    rollout_root.mkdir()
    (rollout_root / "grpo_0.pt").write_bytes(b"training")
    (rollout_root / "grpo_eval_0.pt").write_bytes(b"evaluation")
    (rollout_root / "grpo_1.pt.tmp").write_bytes(b"partial")

    observed = smoke_module.training_rollout_paths(rollout_root)

    assert [path.name for path in observed] == ["grpo_0.pt"]
