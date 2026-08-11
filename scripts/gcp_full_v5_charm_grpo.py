#!/usr/bin/env python3
"""Prepare and run admission-gated full-v5 plus CHARM GRPO on GCP."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from glm47_posttraining.aider_polyglot.full_v5_charm import (
    SCHEDULE_KIND,
    build_charm_schedule,
    sha256_path,
    validate_full_v5_package,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs/full_v5_charm_grpo/gcp-r1.json"
ASSET_ROOT = Path(
    os.environ.get("GLM47_FULL_V5_ASSET_ROOT", "/opt/glm47-full-v5/assets")
).expanduser()
MODEL_DIR = ASSET_ROOT / "model/GLM-4.7-Flash"
ADAPTER_DIR = ASSET_ROOT / "synthmem-v1-ep50/adapter"
RUNTIME_DIR = ASSET_ROOT / "runtime/aider_cpp_rl_full_v5"
RESULT_ROOT = Path(
    os.environ.get("GLM47_FULL_V5_RESULT_ROOT", "/opt/glm47-full-v5/results")
).expanduser()
LOCK_PATH = Path("/tmp/glm47-gpu-heavy.lock")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FULL_AUTHORIZATION_ENV = "GLM47_FULL_V5_CHARM_FULL_TRAINING_AUTHORIZATION"
FULL_AUTHORIZATION_PHRASE = "I_AUTHORIZE_FULL_V5_CHARM_57_UPDATE_TRAINING"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if (
        config.get("schema_version") != "glm47-full-v5-charm-gcp-profile-v1"
        or config.get("profile_id") != "aider-full-v5-production-ast17-gcp-r1"
        or config.get("modal_policy", {}).get("default") != "DENY"
        or config.get("execution", {}).get("provisioner") != "skypilot"
        or config.get("execution", {}).get("smoke_mode") != "prepare-only"
        or config.get("gcp", {}).get("gpu_count") != 8
        or config.get("gcp", {}).get("machine_type") != "a3-highgpu-8g"
        or config.get("starting_adapter", {}).get("profile")
        != "synthmem-v1-ep50"
        or config.get("starting_adapter", {}).get("checkpoint_path")
        != "checkpoints/sft_lora_r16/iter_0000649"
        or config.get("starting_adapter", {}).get("epoch") != 50
        or config.get("starting_adapter", {}).get("optimizer_iteration") != 649
        or config.get("starting_adapter", {}).get("adapter_model_sha256")
        != "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a"
        or config.get("starting_adapter", {}).get("gcp_asset_status") != "AVAILABLE"
        or config.get("canary", {}).get("task_count") != 20
        or config.get("canary", {}).get("epochs") != 5
        or config.get("canary", {}).get("matched_trials") < 4
        or config.get("full_training", {}).get("rollout_updates") != 57
        or config.get("full_training", {}).get("thinking_enabled") is not True
        or config.get("reward", {}).get("signal_gate_required") is not True
        or config.get("admission", {}).get("fixed26_role")
        != "FROZEN_POST_TRAINING_EVALUATION_ONLY"
    ):
        raise RuntimeError("GCP full-v5 CHARM profile is not the frozen production contract")
    return config


def source_commit() -> str:
    try:
        return output(["git", "rev-parse", "HEAD"])
    except (OSError, subprocess.CalledProcessError):
        marker = REPO_ROOT / "SOURCE_COMMIT"
        value = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
        if re.fullmatch(r"[0-9a-f]{40}", value):
            return value
        raise RuntimeError("source commit is unavailable")


def docker_prefix() -> list[str]:
    if os.geteuid() == 0:
        return ["docker"]
    if shutil.which("sudo"):
        return ["sudo", "docker"]
    return ["docker"]


def run(command: Sequence[str], *, env: Mapping[str, str] | None = None) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(list(command), cwd=REPO_ROOT, env=env, check=True)


def output(command: Sequence[str]) -> str:
    return subprocess.check_output(list(command), cwd=REPO_ROOT, text=True).strip()


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite receipt: {path}")
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def gpu_inventory() -> list[dict[str, Any]]:
    if shutil.which("nvidia-smi") is None:
        return []
    raw = output(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,uuid",
            "--format=csv,noheader,nounits",
        ]
    )
    inventory = []
    for line in raw.splitlines():
        index, name, memory, uuid = [part.strip() for part in line.split(",", 3)]
        inventory.append(
            {"index": int(index), "name": name, "memory_mib": int(memory), "uuid": uuid}
        )
    return inventory


def require_h100() -> list[dict[str, Any]]:
    config = load_config()["gcp"]
    inventory = gpu_inventory()
    valid = len(inventory) == int(config["gpu_count"]) and all(
        str(config["gpu_model_contains"]) in str(item["name"])
        and int(item["memory_mib"]) >= int(config["minimum_gpu_memory_mib"])
        for item in inventory
    )
    if not valid:
        found = [(item["name"], item["memory_mib"]) for item in inventory]
        raise RuntimeError(f"training requires exactly eight H100 80GB GPUs; found {found}")
    return inventory


def metadata_value(name: str, default: str = "unknown") -> str:
    request = urllib.request.Request(
        f"http://metadata.google.internal/computeMetadata/v1/{name}",
        headers={"Metadata-Flavor": "Google"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.read().decode("utf-8").strip().split("/")[-1]
    except Exception:
        return default


@contextmanager
def exclusive_gpu_job(label: str) -> Iterator[None]:
    with LOCK_PATH.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"another GPU-heavy job owns {LOCK_PATH}") from exc
        handle.write(f"pid={os.getpid()} label={label} started={utc_now()}\n")
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _sync_result_tree(local_root: Path, destination: str) -> None:
    if shutil.which("gcloud") is not None:
        run(
            [
                "gcloud",
                "storage",
                "rsync",
                "--recursive",
                str(local_root),
                destination,
            ]
        )
        return
    if shutil.which("gsutil") is not None:
        run(["gsutil", "-m", "rsync", "-r", str(local_root), destination])
        return
    raise RuntimeError(
        "gcloud or gsutil is required for durable GCS result synchronization"
    )


@contextmanager
def periodic_result_sync(
    local_root: Path,
    destination: str,
    *,
    interval_seconds: int,
) -> Iterator[dict[str, Any]]:
    """Continuously copy run artifacts to GCS and always attempt a final sync."""

    if interval_seconds < 30:
        raise ValueError("result sync interval must be at least 30 seconds")
    state: dict[str, Any] = {
        "destination": destination,
        "interval_seconds": interval_seconds,
        "periodic_failures": [],
        "final_status": "not_completed",
    }
    _sync_result_tree(local_root, destination)
    stop = threading.Event()

    def worker() -> None:
        while not stop.wait(interval_seconds):
            try:
                _sync_result_tree(local_root, destination)
            except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
                state["periodic_failures"].append(f"{type(exc).__name__}: {exc}")

    thread = threading.Thread(
        target=worker,
        name="full-v5-charm-gcs-sync",
        daemon=True,
    )
    thread.start()
    try:
        yield state
    finally:
        stop.set()
        thread.join(timeout=10)
        try:
            _sync_result_tree(local_root, destination)
            state["final_status"] = "passed"
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            state["final_status"] = "failed"
            state["final_error"] = f"{type(exc).__name__}: {exc}"


def _require_hash(path: Path, expected: str, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular {label}: {path}")
    observed = sha256_path(path)
    if observed != expected:
        raise RuntimeError(f"{label} SHA-256 mismatch: {observed} != {expected}")


def _require_marker(path: Path, expected: str, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular {label}: {path}")
    if path.read_text(encoding="utf-8").strip() != expected:
        raise RuntimeError(f"{label} mismatch: {path}")


def _verify_sha256_manifest(path: Path) -> None:
    """Verify every file in a caller-bound GNU sha256sum manifest."""

    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular SHA-256 manifest: {path}")
    subprocess.run(
        ["sha256sum", "--check", "--quiet", "--strict", path.name],
        cwd=path.parent,
        check=True,
    )


def verify_assets() -> dict[str, Any]:
    config = load_config()
    model = config["model"]
    adapter = config["starting_adapter"]
    runtime = config["full_v5_runtime"]
    _require_marker(MODEL_DIR / ".source-revision", model["revision"], "model revision")
    _require_hash(
        MODEL_DIR / ".source-manifest.sha256",
        model["manifest_sha256"],
        "model source manifest",
    )
    _verify_sha256_manifest(MODEL_DIR / ".source-manifest.sha256")
    _require_marker(
        ADAPTER_DIR / ".training-run-id",
        adapter["training_run_id"],
        "SynthMem-v1 training run ID",
    )
    _require_hash(
        ADAPTER_DIR / "adapter_model.bin",
        adapter["adapter_model_sha256"],
        "SynthMem-v1 ep50 adapter",
    )
    _require_hash(
        ADAPTER_DIR / "adapter_config.json",
        adapter["adapter_config_sha256"],
        "SynthMem-v1 ep50 adapter config",
    )
    reconstruction_path = ADAPTER_DIR / "native_reconstruction_manifest.json"
    _require_hash(
        reconstruction_path,
        adapter["native_reconstruction_manifest_sha256"],
        "SynthMem-v1 ep50 native reconstruction manifest",
    )
    adapter_config = json.loads(
        (ADAPTER_DIR / "adapter_config.json").read_text(encoding="utf-8")
    )
    if (
        int(adapter_config.get("r", -1)) != int(adapter["lora_rank"])
        or int(adapter_config.get("lora_alpha", -1)) != int(adapter["lora_alpha"])
    ):
        raise RuntimeError("SynthMem-v1 ep50 adapter LoRA configuration mismatch")

    reconstruction = json.loads(reconstruction_path.read_text(encoding="utf-8"))
    source = reconstruction.get("source", {})
    mapping = reconstruction.get("mapping", {})
    roundtrip = mapping.get("source_hf_roundtrip", {})
    native_outputs = reconstruction.get("outputs", {}).get("native_shards", {})
    if (
        reconstruction.get("status") != "passed"
        or reconstruction.get("kind")
        != "glm47-hf-to-megatron-tp-native-reconstruction"
        or source.get("adapter_model_sha256") != adapter["adapter_model_sha256"]
        or source.get("adapter_config_sha256") != adapter["adapter_config_sha256"]
        or source.get("tensor_content_sha256")
        != adapter["source_tensor_content_sha256"]
        or source.get("tensor_count") != int(adapter["source_tensor_count"])
        or roundtrip.get("status") != "passed"
        or roundtrip.get("coverage_fraction") != 1.0
        or roundtrip.get("all_source_hf_tensors_value_exact") is not True
        or roundtrip.get("all_source_hf_tensor_bytes_exact") is not True
        or roundtrip.get("source_hf_tensor_bytes")
        != int(adapter["source_tensor_bytes"])
        or roundtrip.get("native_shard_count")
        != int(adapter["expected_native_shards"])
        or not isinstance(native_outputs, dict)
        or len(native_outputs) != int(adapter["expected_native_shards"])
    ):
        raise RuntimeError("SynthMem-v1 ep50 native reconstruction proof mismatch")

    native_names = set(native_outputs)
    observed_native = {
        path.name for path in ADAPTER_DIR.glob("adapter_megatron_tp*_pp*.pt")
    }
    if observed_native != native_names:
        raise RuntimeError("SynthMem-v1 ep50 adapter lacks its exact TP4/EP8 shard set")
    for name, metadata in native_outputs.items():
        if not isinstance(metadata, dict) or SHA256_RE.fullmatch(
            str(metadata.get("sha256", ""))
        ) is None:
            raise RuntimeError(f"invalid native-shard receipt for {name}")
        _require_hash(ADAPTER_DIR / name, metadata["sha256"], f"native shard {name}")

    runtime_receipt = validate_full_v5_package(
        RUNTIME_DIR,
        expected_manifest_sha256=runtime["manifest_sha256"],
        expected_tree_sha256=runtime["tree_sha256"],
    )
    return {
        "status": "passed",
        "model_revision": model["revision"],
        "model_manifest_sha256": model["manifest_sha256"],
        "checkpoint_profile": adapter["profile"],
        "checkpoint_path": adapter["checkpoint_path"],
        "epoch": adapter["epoch"],
        "optimizer_iteration": adapter["optimizer_iteration"],
        "adapter_model_sha256": adapter["adapter_model_sha256"],
        "native_reconstruction_manifest_sha256": adapter[
            "native_reconstruction_manifest_sha256"
        ],
        "native_shards": sorted(native_names),
        "runtime": runtime_receipt,
    }


def _pass_receipt(
    path: Path,
    *,
    expected_sha256: str,
    expected_stage: str,
) -> dict[str, Any]:
    if SHA256_RE.fullmatch(expected_sha256) is None:
        raise ValueError(f"invalid expected {expected_stage} receipt SHA-256")
    _require_hash(path, expected_sha256, f"{expected_stage} receipt")
    payload = json.loads(path.read_text(encoding="utf-8"))
    status = str(payload.get("decision", payload.get("status", ""))).upper()
    stage = str(
        payload.get("stage", payload.get("requested_stage", payload.get("validation_stage", "")))
    ).lower()
    if status not in {"PASS", "PASSED"} or stage != expected_stage:
        raise RuntimeError(f"{expected_stage} receipt is not a matching PASS")
    return payload


def _canary_tasks(path: Path, expected_sha256: str, config: Mapping[str, Any]) -> list[str]:
    _require_hash(path, expected_sha256, "canary task manifest")
    payload = json.loads(path.read_text(encoding="utf-8"))
    task_ids = payload.get("task_ids")
    trial_ids = payload.get("trial_ids")
    if (
        payload.get("profile_id") != config["profile_id"]
        or payload.get("source_manifest_sha256")
        != config["full_v5_runtime"]["manifest_sha256"]
        or not isinstance(task_ids, list)
        or len(task_ids) != 20
        or len(set(task_ids)) != 20
        or not all(isinstance(value, str) and value for value in task_ids)
        or not isinstance(trial_ids, list)
        or len(set(str(value) for value in trial_ids)) < 4
    ):
        raise RuntimeError("canary manifest is not the frozen 20-task/four-trial contract")
    return task_ids


def build_training_env(
    *,
    phase: str,
    run_id: str,
    container_run_root: str,
    verifier_image: str,
    config: Mapping[str, Any],
) -> dict[str, str]:
    if phase not in {"canary", "full"}:
        raise ValueError(f"unsupported phase: {phase}")
    phase_config = config["canary"] if phase == "canary" else config["full_training"]
    signal = config["reward"]["signal_thresholds"]
    num_rollout = int(phase_config["rollout_updates"])
    rollout_batch = int(phase_config["rollout_batch_size"])
    global_batch = int(phase_config["global_batch_size"])
    save_interval = 1 if phase == "canary" else int(phase_config["save_interval"])
    eval_interval = 1 if phase == "canary" else int(phase_config["full_development_interval"])
    return {
        "TMPDIR": f"{container_run_root}/runtime_state/tmp",
        "MILES_RUN_ID": run_id,
        "MILES_RUN_ROOT": container_run_root,
        "MILES_CPP_DATA_DIR": f"{container_run_root}/data",
        "MILES_CPP_TASKS_DIR": f"{container_run_root}/data/tasks",
        "MILES_DATA_BUILD_MODULE": "glm47_posttraining.integrations.miles_aider_polyglot",
        "MILES_CUSTOM_RM_PATH": "glm47_posttraining.integrations.miles_aider_polyglot.reward_func",
        "MILES_REWARD_PREFLIGHT_MODULE": "glm47_posttraining.integrations.miles_aider_polyglot",
        "MILES_SKIP_RUNTIME_PREFLIGHT": "0",
        "MILES_EXPECTED_DATASET_KIND": SCHEDULE_KIND,
        "MILES_CPP_SORT_BY_SIZE": "0",
        "MILES_EVAL_NAME": "full-v5-development",
        "MILES_EVAL_PROMPT_DATA": f"{container_run_root}/data/eval/development.jsonl",
        "MILES_EVAL_INTERVAL": str(eval_interval),
        "MILES_EVAL_N_SAMPLES_PER_PROMPT": "1",
        "MILES_EVAL_MAX_RESPONSE_LEN": "32768",
        "MILES_NUM_ROLLOUT": str(num_rollout),
        "MILES_ROLLOUT_BATCH_SIZE": str(rollout_batch),
        "MILES_N_SAMPLES_PER_PROMPT": str(phase_config["samples_per_prompt"]),
        "MILES_GLOBAL_BATCH_SIZE": str(global_batch),
        "MILES_ROLLOUT_TEMPERATURE": "0.7",
        "MILES_ROLLOUT_MAX_RESPONSE_LEN": "32768",
        "MILES_ROLLOUT_SKIP_SPECIAL_TOKENS": "1",
        "MILES_ROLLOUT_STOP_TOKEN_IDS": "154820 154827 154829",
        "MILES_SAVE_INTERVAL": str(save_interval),
        "MILES_LR": "5e-7",
        "MILES_NO_REF": "0",
        "MILES_USE_KL_LOSS": "1",
        "MILES_KL_LOSS_COEF": "0.02",
        "MILES_APPLY_CHAT_TEMPLATE_KWARGS": '{"enable_thinking": true}',
        "MILES_SEQ_LENGTH": "34816",
        "MILES_MAX_TOKENS_PER_GPU": "49152",
        "MILES_RECOMPUTE_GRANULARITY": "full",
        "MILES_GPUS_PER_NODE": "8",
        "MILES_TENSOR_MODEL_PARALLEL_SIZE": "4",
        "MILES_PIPELINE_MODEL_PARALLEL_SIZE": "1",
        "MILES_CONTEXT_PARALLEL_SIZE": "1",
        "MILES_EXPERT_MODEL_PARALLEL_SIZE": "8",
        "MILES_EXPERT_TENSOR_PARALLEL_SIZE": "1",
        "MILES_EXPECTED_NATIVE_SHARDS": "8",
        "MILES_HF_CHECKPOINT": "/root/models/GLM-4.7-Flash",
        "MILES_REF_LOAD_DIR": "/root/models/GLM-4.7-Flash_torch_dist_tp4_pp1_ep8",
        "MILES_LORA_ADAPTER_PATH": "/starting-adapter",
        "MILES_GRPO_ADAPTER_DIR": f"{container_run_root}/adapter_hybrid",
        "MILES_EXPECTED_SOURCE_ADAPTER_SHA256": config["starting_adapter"][
            "adapter_model_sha256"
        ],
        "MILES_EXPECTED_SOURCE_TENSORS": str(
            config["starting_adapter"]["source_tensor_count"]
        ),
        "MILES_EXPECTED_STRIPPED_TENSORS": str(
            config["starting_adapter"]["stripped_mtp_tensor_count"]
        ),
        "MILES_NATIVE_RECONSTRUCTION_MANIFEST_PATH": (
            "/starting-adapter/native_reconstruction_manifest.json"
        ),
        "MILES_EXPECTED_NATIVE_RECONSTRUCTION_MANIFEST_SHA256": config[
            "starting_adapter"
        ]["native_reconstruction_manifest_sha256"],
        "MILES_LORA_RANK": str(config["starting_adapter"]["lora_rank"]),
        "MILES_LORA_ALPHA": str(config["starting_adapter"]["lora_alpha"]),
        "MILES_ROLLOUT_SAMPLE_FILTER_PATH": (
            "glm47_posttraining.integrations.miles_aider_polyglot."
            "validate_aider_rollout_batch"
        ),
        "MILES_AIDER_REWARD_MODE": "production_ast17",
        "MILES_CPP_INCLUDE_LOGS": "0",
        "GLM47_CPP_SANDBOX_BACKEND": "docker",
        "GLM47_CPP_SANDBOX_IMAGE": verifier_image,
        "GLM47_CPP_SANDBOX_UNSHARE_NET": "1",
        "GLM47_CPP_REWARD_WORKERS": str(config["reward"]["workers"]),
        "GLM47_AIDER_EXPECTED_TRAIN_GROUPS": str(rollout_batch),
        "GLM47_AIDER_EXPECTED_SAMPLES_PER_GROUP": str(
            phase_config["samples_per_prompt"]
        ),
        "GLM47_AIDER_REQUIRE_UNIQUE_TASK_GROUPS": "1",
        "GLM47_AIDER_REQUIRE_SIGNAL": "1",
        "GLM47_AIDER_MIN_POSITIVE_GROUPS": str(signal["minimum_positive_groups"]),
        "GLM47_AIDER_MIN_SEMANTIC_VARIANCE_GROUPS": str(
            signal["minimum_semantic_variance_groups"]
        ),
        "GLM47_AIDER_MIN_REWARD_VARIANCE_GROUPS": str(
            signal["minimum_reward_variance_groups"]
        ),
        "GLM47_AIDER_MIN_EXACT_FORMAT_RATE": str(signal["minimum_exact_format_rate"]),
        "GLM47_AIDER_MIN_COMPILE_RATE": str(signal["minimum_compile_rate"]),
        "GLM47_AIDER_SIGNAL_GATE_DIR": f"{container_run_root}/signal-gates",
        "WANDB_MODE": config["tracking"]["wandb_mode"],
        "WANDB_DIR": f"{container_run_root}/wandb",
        "MILES_WANDB_PROJECT": config["tracking"]["wandb_project"],
        "MILES_WANDB_GROUP": run_id,
        "MILES_WANDB_RUN_ID": run_id,
        "MILES_WANDB_JOB_TYPE": f"grpo-{phase}",
        "WANDB_TAGS": f"gcp,full-v5,charm,production-ast17,thinking,{phase}",
        "GLM47_EXPERIMENT_ID": run_id,
        "GLM47_SOURCE_COMMIT": source_commit(),
        "GLM47_FULL_V5_CHARM_PROFILE": config["profile_id"],
        "GLM47_EXECUTION_PROFILE": config["execution"]["profile"],
        "GLM47_PROVISIONER": config["execution"]["provisioner"],
        "GLM47_SKYPILOT_TASK_ID": os.environ.get("SKYPILOT_TASK_ID", "unknown"),
    }


def _docker_training_command(
    *,
    run_id: str,
    result_root: Path,
    train_image: str,
    env_values: Mapping[str, str],
) -> list[str]:
    command = docker_prefix() + [
        "run",
        "--rm",
        "--name",
        run_id,
        "--gpus",
        "all",
        "--network",
        "none",
        "--ipc",
        "host",
        "--shm-size",
        "256g",
        "--volume",
        "/var/run/docker.sock:/var/run/docker.sock",
        "--volume",
        f"{MODEL_DIR.parent}:/root/models:ro",
        "--volume",
        f"{ADAPTER_DIR}:/starting-adapter:ro",
        "--volume",
        f"{result_root}:/results",
    ]
    for key, value in sorted(env_values.items()):
        command += ["--env", f"{key}={value}"]
    command += [train_image, "/opt/full-v5-charm/examples/grpo.sh"]
    return command


def inspect(_args: argparse.Namespace) -> None:
    config = load_config()
    inventory = gpu_inventory()
    payload = {
        "profile_id": config["profile_id"],
        "execution": config["execution"],
        "decision": config["decision"],
        "source_commit": source_commit(),
        "config_sha256": sha256_path(CONFIG_PATH),
        "modal_default": config["modal_policy"]["default"],
        "gpu_inventory": inventory,
        "h100_ready": len(inventory) == 8
        and all("H100" in str(item["name"]) for item in inventory),
        "gcp_metadata": {
            "instance": metadata_value("instance/name"),
            "zone": metadata_value("instance/zone"),
            "machine_type": metadata_value("instance/machine-type"),
        },
        "paths": {
            "model": str(MODEL_DIR),
            "adapter": str(ADAPTER_DIR),
            "runtime": str(RUNTIME_DIR),
            "results": str(RESULT_ROOT),
        },
        "gates": config["admission"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def render(args: argparse.Namespace) -> None:
    config = load_config()
    run_id = args.run_id or f"render-{args.phase}"
    env = build_training_env(
        phase=args.phase,
        run_id=run_id,
        container_run_root=f"/results/runs/{run_id}",
        verifier_image=config["verifier_image"]["local_name"],
        config=config,
    )
    print(
        json.dumps(
            {
                "phase": args.phase,
                "run_id": run_id,
                "environment": env,
                "command": _docker_training_command(
                    run_id=run_id,
                    result_root=RESULT_ROOT,
                    train_image=config["training_image"]["local_name"],
                    env_values=env,
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def host_check(_args: argparse.Namespace) -> None:
    config = load_config()
    inventory = require_h100()
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed")
    run(docker_prefix() + ["info"])
    free_gib = shutil.disk_usage("/opt" if Path("/opt").exists() else "/").free // (1024**3)
    if free_gib < 250:
        raise RuntimeError(f"at least 250 GiB free storage is required; found {free_gib}")
    print(
        json.dumps(
            {
                "status": "passed",
                "profile_id": config["profile_id"],
                "execution": config["execution"],
                "gpu_inventory": inventory,
                "free_storage_gib": free_gib,
                "instance": metadata_value("instance/name"),
                "zone": metadata_value("instance/zone"),
                "machine_type": metadata_value("instance/machine-type"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def prepare(args: argparse.Namespace) -> None:
    config = load_config()
    inventory = require_h100()
    assets = verify_assets()
    env = dict(os.environ)
    env["DOCKER_BUILDKIT"] = "1"
    for dockerfile, image in (
        (config["verifier_image"]["dockerfile"], args.verifier_image),
        (config["training_image"]["dockerfile"], args.train_image),
    ):
        run(
            docker_prefix()
            + [
                "build",
                "--progress=plain",
                "--file",
                dockerfile,
                "--tag",
                image,
                ".",
            ],
            env=env,
        )
    scratch = Path(args.result_root).resolve() / "preflight-scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    run(
        docker_prefix()
        + [
            "run",
            "--rm",
            "--network",
            "none",
            "--volume",
            "/var/run/docker.sock:/var/run/docker.sock",
            "--volume",
            f"{scratch}:{scratch}",
            "--env",
            f"TMPDIR={scratch}",
            "--env",
            "GLM47_CPP_SANDBOX_BACKEND=docker",
            "--env",
            f"GLM47_CPP_SANDBOX_IMAGE={args.verifier_image}",
            args.train_image,
            "python3",
            "-m",
            "glm47_posttraining.integrations.miles_aider_polyglot",
            "preflight",
        ]
    )
    receipt = {
        "schema_version": "glm47-full-v5-charm-gcp-preparation-v1",
        "status": "passed",
        "created_at_utc": utc_now(),
        "profile_id": config["profile_id"],
        "execution": config["execution"],
        "source_commit": source_commit(),
        "config_sha256": sha256_path(CONFIG_PATH),
        "assets": assets,
        "gpu_inventory": inventory,
        "images": {"training": args.train_image, "verifier": args.verifier_image},
    }
    atomic_json(Path(args.receipt), receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def train(args: argparse.Namespace) -> None:
    config = load_config()
    run_id = args.run_id
    if RUN_ID_RE.fullmatch(run_id) is None:
        raise ValueError(f"invalid run ID: {run_id!r}")
    if args.phase == "canary":
        admission = _pass_receipt(
            Path(args.pretraining_receipt),
            expected_sha256=args.expected_pretraining_sha256,
            expected_stage="pre-training",
        )
        task_ids = _canary_tasks(
            Path(args.canary_task_manifest),
            args.expected_canary_task_manifest_sha256,
            config,
        )
        promotion = None
    else:
        if os.environ.get(FULL_AUTHORIZATION_ENV) != FULL_AUTHORIZATION_PHRASE:
            raise RuntimeError(
                "full training is not authorized; set "
                f"{FULL_AUTHORIZATION_ENV}={FULL_AUTHORIZATION_PHRASE} only after "
                "the exact CHARM canary promotion PASS"
            )
        admission = None
        task_ids = None
        promotion = _pass_receipt(
            Path(args.promotion_receipt),
            expected_sha256=args.expected_promotion_sha256,
            expected_stage="promotion",
        )
    with exclusive_gpu_job(f"full-v5-charm-{args.phase}"):
        inventory = require_h100()
        assets = verify_assets()
        result_root = Path(args.result_root).resolve()
        host_run_root = result_root / "runs" / run_id
        if host_run_root.exists() or host_run_root.is_symlink():
            raise FileExistsError(f"refusing to reuse run root: {host_run_root}")
        host_run_root.mkdir(parents=True)
        phase_config = config["canary"] if args.phase == "canary" else config["full_training"]
        schedule = build_charm_schedule(
            RUNTIME_DIR,
            host_run_root / "data",
            epochs=int(phase_config["epochs"]),
            rollout_batch_size=int(phase_config["rollout_batch_size"]),
            expected_manifest_sha256=config["full_v5_runtime"]["manifest_sha256"],
            expected_tree_sha256=config["full_v5_runtime"]["tree_sha256"],
            selected_task_ids=task_ids,
        )
        container_run_root = f"/results/runs/{run_id}"
        env_values = build_training_env(
            phase=args.phase,
            run_id=run_id,
            container_run_root=container_run_root,
            verifier_image=args.verifier_image,
            config=config,
        )
        launch = {
            "schema_version": "glm47-full-v5-charm-launch-v1",
            "status": "authorized",
            "created_at_utc": utc_now(),
            "profile_id": config["profile_id"],
            "execution": config["execution"],
            "phase": args.phase,
            "run_id": run_id,
            "source_commit": source_commit(),
            "config_sha256": sha256_path(CONFIG_PATH),
            "gpu_inventory": inventory,
            "assets": assets,
            "schedule": schedule,
            "result_sync": {
                "destination": f'{config["gcp"]["result_destination"].rstrip("/")}/{run_id}',
                "interval_seconds": int(config["tracking"]["result_sync_interval_seconds"]),
            },
            "pretraining_receipt_sha256": args.expected_pretraining_sha256
            if admission
            else None,
            "promotion_receipt_sha256": args.expected_promotion_sha256
            if promotion
            else None,
            "environment": env_values,
        }
        atomic_json(host_run_root / "launch-contract.json", launch)
        result_destination = launch["result_sync"]["destination"]
        sync_state: dict[str, Any] = {"final_status": "not_started"}
        try:
            with periodic_result_sync(
                host_run_root,
                result_destination,
                interval_seconds=launch["result_sync"]["interval_seconds"],
            ) as sync_state:
                run(
                    _docker_training_command(
                        run_id=run_id,
                        result_root=result_root,
                        train_image=args.train_image,
                        env_values=env_values,
                    )
                )
            receipt = host_run_root / "grpo_lora_r16/run_receipt.txt"
            if not receipt.is_file() or "status=success" not in receipt.read_text(
                encoding="utf-8"
            ):
                raise RuntimeError("Miles training did not produce a successful run receipt")
            if sync_state["final_status"] != "passed":
                raise RuntimeError(
                    f"final GCS result sync failed: {sync_state.get('final_error', 'unknown')}"
                )
        except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
            pre_receipt_sync_error = None
            try:
                _sync_result_tree(host_run_root, result_destination)
            except (OSError, RuntimeError, subprocess.CalledProcessError) as sync_exc:
                pre_receipt_sync_error = f"{type(sync_exc).__name__}: {sync_exc}"
            failure = {
                "schema_version": "glm47-full-v5-charm-execution-v1",
                "status": "failed",
                "completed_at_utc": utc_now(),
                "profile_id": config["profile_id"],
                "execution": config["execution"],
                "phase": args.phase,
                "run_id": run_id,
                "source_commit": source_commit(),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "result_sync": sync_state,
                "pre_receipt_sync_error": pre_receipt_sync_error,
            }
            atomic_json(host_run_root / "execution-receipt.json", failure)
            try:
                _sync_result_tree(host_run_root, result_destination)
            except (OSError, RuntimeError, subprocess.CalledProcessError):
                pass
            raise
        completion = {
            "schema_version": "glm47-full-v5-charm-execution-v1",
            "status": "passed",
            "completed_at_utc": utc_now(),
            "profile_id": config["profile_id"],
            "execution": config["execution"],
            "phase": args.phase,
            "run_id": run_id,
            "source_commit": source_commit(),
            "result_sync": sync_state,
        }
        atomic_json(host_run_root / "execution-receipt.json", completion)
        _sync_result_tree(host_run_root, result_destination)
        print(f"FULL_V5_CHARM_RUN_ROOT={host_run_root}")


def parser() -> argparse.ArgumentParser:
    config = load_config()
    result = argparse.ArgumentParser(description=__doc__)
    result.set_defaults(
        train_image=config["training_image"]["local_name"],
        verifier_image=config["verifier_image"]["local_name"],
    )
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect").set_defaults(func=inspect)
    sub.add_parser("host-check").set_defaults(func=host_check)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--phase", choices=("canary", "full"), required=True)
    render_parser.add_argument("--run-id")
    render_parser.set_defaults(func=render)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--result-root", default=str(RESULT_ROOT))
    prepare_parser.add_argument(
        "--receipt", default=str(RESULT_ROOT / "preparation-receipt.json")
    )
    prepare_parser.add_argument("--train-image", default=config["training_image"]["local_name"])
    prepare_parser.add_argument("--verifier-image", default=config["verifier_image"]["local_name"])
    prepare_parser.set_defaults(func=prepare)
    train_parser = sub.add_parser("train")
    train_parser.add_argument("--phase", choices=("canary", "full"), required=True)
    train_parser.add_argument("--run-id", required=True)
    train_parser.add_argument("--result-root", default=str(RESULT_ROOT))
    train_parser.add_argument("--train-image", default=config["training_image"]["local_name"])
    train_parser.add_argument("--verifier-image", default=config["verifier_image"]["local_name"])
    train_parser.add_argument("--pretraining-receipt")
    train_parser.add_argument("--expected-pretraining-sha256", default="")
    train_parser.add_argument("--canary-task-manifest")
    train_parser.add_argument("--expected-canary-task-manifest-sha256", default="")
    train_parser.add_argument("--promotion-receipt")
    train_parser.add_argument("--expected-promotion-sha256", default="")
    train_parser.set_defaults(func=train)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "train" and args.phase == "canary":
            if not args.pretraining_receipt or not args.canary_task_manifest:
                raise ValueError(
                    "canary requires --pretraining-receipt and --canary-task-manifest"
                )
        if args.command == "train" and args.phase == "full" and not args.promotion_receipt:
            raise ValueError("full training requires --promotion-receipt")
        args.func(args)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FULL_V5_CHARM_GCP_FAILED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
