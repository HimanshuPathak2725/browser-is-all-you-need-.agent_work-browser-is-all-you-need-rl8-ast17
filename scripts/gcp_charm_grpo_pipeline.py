#!/usr/bin/env python3
"""Prepare, train, and evaluate the compiler-guided CHARM GRPO pilot on GCP."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs/charm_compiler_grpo/r1.json"
DATA_ROOT = REPO_ROOT / "artifacts/charm-compiler-grpo/r1/data"
ORACLE_RECEIPT = (
    REPO_ROOT / "artifacts/charm-compiler-grpo/r1/executable-oracle-receipt.json"
)
TRAIN_IMAGE = "glm47-charm-compiler-grpo:r1"
VERIFIER_IMAGE = "glm47-charm-grpo-verifier:r1"
EVAL_IMAGE = "glm47-public-pr-gcp:a100-charm-r1"
MODEL_DIR = Path("/opt/glm47-public-pr/assets/model/GLM-4.7-Flash")
SOURCE_ADAPTER_DIR = Path("/opt/glm47-public-pr/assets/adapter")
RESULT_ROOT = Path("/opt/glm47-public-pr/results/charm-compiler-grpo")
LOCK_PATH = Path("/tmp/glm47-gpu-heavy.lock")

MODEL_REVISION = "7dd20894a642a0aa287e9827cb1a1f7f91386b67"
MODEL_MANIFEST_SHA256 = (
    "ac1c2693a8d8724a6aa359eb7a6778d5dda59743b1b4c45ff92986d2d1e6cecc"
)
SOURCE_TRAINING_RUN_ID = "glm47-synth-mem-v3-v1std-50ep-20260803T023833Z"
SOURCE_ADAPTER_SHA256 = (
    "5ca6a0cbede843e8c042ebb1004a80e85d85686974063cb9bd0540e236aab6ca"
)
SOURCE_ADAPTER_CONFIG_SHA256 = (
    "0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e"
)
DATA_MANIFEST_SHA256 = (
    "de4bd2526327dc5a222df426b9fc986a3c6bf4c051b04e767450d412fa469fbb"
)
TRAIN_JSONL_SHA256 = (
    "a4ea9d320a127b4be36ad1aaeb4054df18b73a3a0250a4c2e209f23fc0b73ca8"
)
MONITOR_JSONL_SHA256 = (
    "40340b89676fadf0c42fd0725fbce2197857fd8a269243686cc23273342fc7ef"
)
MECHANISM_MATRIX_SHA256 = (
    "c12e0a744b71b2fbd0457d7b1be5584b6890c8990e020f50305ff80df7854f40"
)
ORACLE_RECEIPT_SHA256 = (
    "dbaa7af807ba1020822f75ccc8e6b0a5ba45e8afaf9971cd9a3c712d2c175ec4"
)
R5_FMTLIB_SHA256 = (
    "9db4bbc4df06aed1cb87dca1026456f2cafa3973f15024fba41b3c912d5b22a7"
)
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular {label}: {path}")
    observed = sha256_path(path)
    if observed != expected:
        raise RuntimeError(f"{label} digest mismatch: {observed} != {expected}")


def require_marker(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or path.read_text(encoding="utf-8").strip() != expected:
        raise RuntimeError(f"{label} marker mismatch: {path}")


def docker_prefix() -> list[str]:
    if os.geteuid() == 0:
        return ["docker"]
    if shutil.which("sudo") is None:
        raise RuntimeError("docker requires root or sudo")
    return ["sudo", "docker"]


def run(command: Sequence[str], *, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(list(command), cwd=REPO_ROOT, env=env, check=True)


def output(command: Sequence[str]) -> str:
    return subprocess.check_output(list(command), cwd=REPO_ROOT, text=True).strip()


def source_commit() -> str:
    try:
        return output(["git", "rev-parse", "HEAD"])
    except (OSError, subprocess.CalledProcessError):
        marker = REPO_ROOT / "SOURCE_COMMIT"
        if marker.is_file():
            value = marker.read_text(encoding="utf-8").strip()
            if re.fullmatch(r"[0-9a-f]{40}", value):
                return value
        raise RuntimeError("source commit is neither available from git nor SOURCE_COMMIT")


def image_id(name: str) -> str:
    return output(docker_prefix() + ["image", "inspect", "--format", "{{.Id}}", name])


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    result = []
    for line in raw.splitlines():
        index, name, memory, uuid = [part.strip() for part in line.split(",", 3)]
        result.append(
            {"index": int(index), "name": name, "memory_mib": int(memory), "uuid": uuid}
        )
    return result


def require_hardware(kind: str) -> list[dict[str, Any]]:
    inventory = gpu_inventory()
    if kind == "train":
        valid = len(inventory) == 8 and all(
            "H100" in str(item["name"]) and int(item["memory_mib"]) >= 80_000
            for item in inventory
        )
        expected = "exactly eight H100 80GB GPUs"
    elif kind == "eval":
        valid = len(inventory) == 4 and all(
            "A100" in str(item["name"]) and int(item["memory_mib"]) >= 80_000
            for item in inventory
        )
        expected = "exactly four A100 80GB GPUs"
    else:  # pragma: no cover - internal programming error
        raise ValueError(kind)
    if not valid:
        found = [(item["name"], item["memory_mib"]) for item in inventory]
        raise RuntimeError(f"{kind} requires {expected}; found {found}")
    return inventory


@contextmanager
def exclusive_gpu_job(label: str) -> Iterator[None]:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(
                f"another GPU-heavy job owns {LOCK_PATH}; refusing simultaneous {label}"
            ) from exc
        handle.write(f"pid={os.getpid()} label={label} started={utc_now()}\n")
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def verify_repository_inputs() -> dict[str, Any]:
    require_hash(DATA_ROOT / "manifest.json", DATA_MANIFEST_SHA256, "data manifest")
    require_hash(DATA_ROOT / "grpo/train.jsonl", TRAIN_JSONL_SHA256, "GRPO train JSONL")
    require_hash(
        DATA_ROOT / "eval/mechanism_monitor.jsonl",
        MONITOR_JSONL_SHA256,
        "mechanism monitor JSONL",
    )
    require_hash(
        DATA_ROOT / "eval/mechanism_matrix.json",
        MECHANISM_MATRIX_SHA256,
        "mechanism matrix",
    )
    require_hash(ORACLE_RECEIPT, ORACLE_RECEIPT_SHA256, "executable oracle receipt")
    require_hash(
        REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl",
        R5_FMTLIB_SHA256,
        "held-out r5 fmtlib JSONL",
    )
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if (
        config.get("decision") != "READY_FOR_8XH100_CANARY"
        or config.get("grpo", {}).get("epochs") != 3
        or config.get("grpo", {}).get("rollout_updates") != 18
        or config.get("heldout_evaluation", {}).get("mechanism_count") != 12
        or config.get("heldout_evaluation", {}).get("r5_prompt_training_eligible") is not False
    ):
        raise RuntimeError("r1 pipeline config is not the frozen 3-epoch held-out contract")
    return config


def verify_host_assets(*, adapter: Path = SOURCE_ADAPTER_DIR, marker: bool = True) -> None:
    require_marker(MODEL_DIR / ".source-revision", MODEL_REVISION, "model revision")
    require_hash(
        MODEL_DIR / ".source-manifest.sha256",
        MODEL_MANIFEST_SHA256,
        "model source manifest",
    )
    require_hash(adapter / "adapter_model.bin", SOURCE_ADAPTER_SHA256, "source adapter")
    require_hash(
        adapter / "adapter_config.json",
        SOURCE_ADAPTER_CONFIG_SHA256,
        "source adapter config",
    )
    if marker:
        require_marker(
            adapter / ".training-run-id", SOURCE_TRAINING_RUN_ID, "source training run"
        )


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


def prepare(args: argparse.Namespace) -> None:
    config = verify_repository_inputs()
    verify_host_assets()
    docker = docker_prefix()
    env = dict(os.environ)
    env["DOCKER_BUILDKIT"] = "1"
    preflight_scratch = Path(args.receipt).resolve().parent / "preflight-scratch"
    preflight_scratch.mkdir(parents=True, exist_ok=True)
    run(
        docker
        + [
            "build",
            "--progress=plain",
            "--file",
            "docker/charm-compiler-grpo-gcp/Verifier.Dockerfile",
            "--tag",
            args.verifier_image,
            ".",
        ],
        env=env,
    )
    run(
        docker
        + [
            "build",
            "--progress=plain",
            "--file",
            "docker/charm-compiler-grpo-gcp/Dockerfile",
            "--tag",
            args.train_image,
            ".",
        ],
        env=env,
    )
    run(
        docker
        + [
            "build",
            "--progress=plain",
            "--file",
            "docker/public-pr-synthmem-gcp/Dockerfile",
            "--tag",
            args.eval_image,
            ".",
        ],
        env=env,
    )
    run(
        docker
        + [
            "run",
            "--rm",
            "--network",
            "none",
            "--env",
            f"GLM47_CPP_SANDBOX_IMAGE={args.verifier_image}",
            "--env",
            "GLM47_CPP_SANDBOX_BACKEND=docker",
            "--env",
            f"TMPDIR={preflight_scratch}",
            "--volume",
            "/var/run/docker.sock:/var/run/docker.sock",
            "--volume",
            f"{preflight_scratch}:{preflight_scratch}",
            args.train_image,
            "python3",
            "-m",
            "glm47_posttraining.integrations.miles_charm_compiler_grpo",
            "preflight",
        ]
    )
    receipt = {
        "schema_version": "charm-compiler-grpo-gcp-preparation-v1",
        "decision": "PASS",
        "created_at_utc": utc_now(),
        "source_commit": source_commit(),
        "config_sha256": sha256_path(CONFIG_PATH),
        "data_manifest_sha256": DATA_MANIFEST_SHA256,
        "oracle_receipt_sha256": ORACLE_RECEIPT_SHA256,
        "heldout_r5_fmtlib_sha256": R5_FMTLIB_SHA256,
        "images": {
            "training": {"name": args.train_image, "id": image_id(args.train_image)},
            "verifier": {
                "name": args.verifier_image,
                "id": image_id(args.verifier_image),
            },
            "heldout_eval": {"name": args.eval_image, "id": image_id(args.eval_image)},
        },
        "gpu_inventory": gpu_inventory(),
        "canonical_training_hardware": config["canonical_training_hardware"],
        "gpu_concurrency_policy": config["gpu_job_concurrency"],
    }
    atomic_json(Path(args.receipt), receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def reconstruct_adapter(args: argparse.Namespace) -> None:
    verify_repository_inputs()
    verify_host_assets()
    template = Path(args.native_template).resolve()
    output_dir = Path(args.output_adapter).resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to replace adapter output: {output_dir}")
    if not template.is_dir():
        raise FileNotFoundError(f"native template directory is missing: {template}")
    source_native_template = bool(args.source_native_template)
    if source_native_template and template != SOURCE_ADAPTER_DIR.resolve():
        raise ValueError(
            "--source-native-template requires --native-template to be the exact "
            f"source adapter directory: {SOURCE_ADAPTER_DIR}"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    template_mount = "/source-adapter" if source_native_template else "/native-template"
    command = docker_prefix() + [
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--volume",
        f"{SOURCE_ADAPTER_DIR}:/source-adapter:ro",
    ]
    if not source_native_template:
        command += ["--volume", f"{template}:/native-template:ro"]
    command += [
        "--volume",
        f"{output_dir.parent}:/adapter-output",
        args.train_image,
        "python3",
        "/opt/charm-grpo/scripts/reconstruct_megatron_lora.py",
        "/source-adapter",
        template_mount,
        f"/adapter-output/{output_dir.name}",
        "--expected-source-sha256",
        SOURCE_ADAPTER_SHA256,
        "--expert-parallel-size",
        "8",
        "--audit-report",
        f"/adapter-output/{output_dir.name}-audit.json",
    ]
    if source_native_template:
        command.append("--source-native-template")
    with exclusive_gpu_job("adapter-reconstruction"):
        run(command)
    verify_host_assets(adapter=output_dir, marker=False)
    manifest = output_dir / "native_reconstruction_manifest.json"
    require_hash(output_dir / "adapter_model.bin", SOURCE_ADAPTER_SHA256, "reconstructed adapter")
    print(f"NATIVE_RECONSTRUCTION_MANIFEST_SHA256={sha256_path(manifest)}")


def convert(args: argparse.Namespace) -> None:
    verify_repository_inputs()
    verify_host_assets()
    with exclusive_gpu_job("checkpoint-conversion"):
        require_hardware("train")
        model_parent = MODEL_DIR.parent
        run(
            docker_prefix()
            + [
                "run",
                "--rm",
                "--gpus",
                "all",
                "--network",
                "none",
                "--ipc",
                "host",
                "--shm-size",
                "256g",
                "--volume",
                f"{model_parent}:/root/models",
                "--env",
                "MILES_HF_CHECKPOINT=/root/models/GLM-4.7-Flash",
                "--env",
                "MILES_REF_LOAD_DIR=/root/models/GLM-4.7-Flash_torch_dist_tp4_pp1_ep8",
                "--env",
                "MILES_CONVERT_NPROC=8",
                args.train_image,
                "/opt/charm-grpo/scripts/convert_checkpoint.sh",
            ]
        )
    marker = model_parent / "GLM-4.7-Flash_torch_dist_tp4_pp1_ep8/latest_checkpointed_iteration.txt"
    if not marker.is_file():
        raise RuntimeError("converted TP4/PP1/EP8 checkpoint marker is missing")
    print(f"CONVERTED_CHECKPOINT_READY={marker.parent}")


def _run_id(value: str | None, prefix: str) -> str:
    result = value or f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    if RUN_ID_RE.fullmatch(result) is None:
        raise ValueError(f"invalid run ID: {result!r}")
    return result


def train(args: argparse.Namespace) -> None:
    verify_repository_inputs()
    start_adapter = Path(args.start_adapter).resolve()
    verify_host_assets(adapter=start_adapter, marker=False)
    reconstruction = start_adapter / "native_reconstruction_manifest.json"
    if not reconstruction.is_file():
        raise FileNotFoundError("training requires a proof-gated native reconstruction manifest")
    native_names = {
        f"adapter_megatron_tp{rank % 4}_pp0_ep{rank % 8}.pt" for rank in range(8)
    }
    if {path.name for path in start_adapter.glob("adapter_megatron_tp*_pp*.pt")} != native_names:
        raise RuntimeError("training requires the exact TP4/EP8 native adapter shard set")
    reconstructed_sha = sha256_path(reconstruction)
    converted = MODEL_DIR.parent / "GLM-4.7-Flash_torch_dist_tp4_pp1_ep8"
    if not (converted / "latest_checkpointed_iteration.txt").is_file():
        raise FileNotFoundError("run the convert phase on an 8xH100 host first")
    run_id = _run_id(args.run_id, "charm-compiler-grpo-r1")
    host_run_root = Path(args.result_root).resolve() / "runs" / run_id
    if host_run_root.exists():
        raise FileExistsError(f"refusing to reuse run directory: {host_run_root}")
    host_run_root.mkdir(parents=True)
    scratch = Path(args.result_root).resolve() / "reward-scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    container_run_root = f"/results/runs/{run_id}"
    env_values = {
        "TMPDIR": str(scratch),
        "MILES_RUN_ID": run_id,
        "MILES_RUN_ROOT": container_run_root,
        "MILES_CPP_DATA_DIR": f"{container_run_root}/data",
        "MILES_CPP_TASKS_DIR": "/opt/charm-grpo/data-source",
        "MILES_DATA_BUILD_MODULE": "glm47_posttraining.integrations.miles_charm_compiler_grpo",
        "MILES_CUSTOM_RM_PATH": "glm47_posttraining.integrations.miles_aider_polyglot.reward_func",
        "MILES_REWARD_PREFLIGHT_MODULE": "glm47_posttraining.integrations.miles_charm_compiler_grpo",
        "MILES_EXPECTED_DATASET_KIND": "charm-compiler-guided-cpp-grpo",
        "MILES_CPP_SORT_BY_SIZE": "0",
        "MILES_EVAL_NAME": "charm-mechanism-monitor",
        "MILES_EVAL_PROMPT_DATA": f"{container_run_root}/data/eval/mechanism_monitor.jsonl",
        "MILES_EVAL_INTERVAL": "3",
        "MILES_EVAL_N_SAMPLES_PER_PROMPT": "1",
        "MILES_NUM_ROLLOUT": "18",
        "MILES_ROLLOUT_BATCH_SIZE": "19",
        "MILES_N_SAMPLES_PER_PROMPT": "8",
        "MILES_GLOBAL_BATCH_SIZE": "152",
        "MILES_ROLLOUT_TEMPERATURE": "0.7",
        "MILES_ROLLOUT_MAX_RESPONSE_LEN": "4096",
        "MILES_EVAL_MAX_RESPONSE_LEN": "4096",
        "MILES_SAVE_INTERVAL": "1",
        "MILES_LR": "1e-6",
        "MILES_NO_REF": "1",
        "MILES_HF_CHECKPOINT": "/root/models/GLM-4.7-Flash",
        "MILES_REF_LOAD_DIR": "/root/models/GLM-4.7-Flash_torch_dist_tp4_pp1_ep8",
        "MILES_LORA_ADAPTER_PATH": "/starting-adapter",
        "MILES_GRPO_ADAPTER_DIR": f"{container_run_root}/adapter_hybrid",
        "MILES_EXPECTED_SOURCE_ADAPTER_SHA256": SOURCE_ADAPTER_SHA256,
        "MILES_EXPECTED_SOURCE_TENSORS": "9741",
        "MILES_EXPECTED_STRIPPED_TENSORS": "207",
        "MILES_NATIVE_RECONSTRUCTION_MANIFEST_PATH": "/starting-adapter/native_reconstruction_manifest.json",
        "MILES_EXPECTED_NATIVE_RECONSTRUCTION_MANIFEST_SHA256": reconstructed_sha,
        "MILES_GRPO_CONTINUATION_MODE": "none",
        "MILES_ROLLOUT_SAMPLE_FILTER_PATH": "glm47_posttraining.integrations.miles_aider_polyglot.validate_aider_rollout_batch",
        "MILES_AIDER_REWARD_MODE": "production_ast17",
        "MILES_CPP_INCLUDE_LOGS": "0",
        "GLM47_CPP_SANDBOX_BACKEND": "docker",
        "GLM47_CPP_SANDBOX_IMAGE": args.verifier_image,
        "GLM47_CPP_REWARD_WORKERS": "32",
        "GLM47_AIDER_EXPECTED_TRAIN_GROUPS": "19",
        "GLM47_AIDER_EXPECTED_SAMPLES_PER_GROUP": "8",
        "GLM47_AIDER_REQUIRE_SIGNAL": "1",
        "GLM47_AIDER_MIN_POSITIVE_GROUPS": "1",
        "GLM47_AIDER_MIN_SEMANTIC_VARIANCE_GROUPS": "2",
        "GLM47_AIDER_MIN_REWARD_VARIANCE_GROUPS": "2",
        "GLM47_AIDER_MIN_EXACT_FORMAT_RATE": "0.50",
        "GLM47_AIDER_MIN_COMPILE_RATE": "0.20",
        "GLM47_AIDER_SIGNAL_GATE_DIR": f"{container_run_root}/signal-gates",
        "WANDB_MODE": "offline",
        "WANDB_DIR": f"{container_run_root}/wandb",
        "MILES_WANDB_PROJECT": "glm47-charm-compiler-grpo",
        "MILES_WANDB_GROUP": run_id,
        "MILES_WANDB_RUN_ID": run_id,
        "GLM47_EXPERIMENT_ID": run_id,
        "GLM47_SOURCE_COMMIT": source_commit(),
    }
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
        f"{start_adapter}:/starting-adapter:ro",
        "--volume",
        f"{Path(args.result_root).resolve()}:/results",
        "--volume",
        f"{scratch}:{scratch}",
    ]
    for key, value in env_values.items():
        command += ["--env", f"{key}={value}"]
    command += [args.train_image, "/opt/charm-grpo/examples/grpo.sh"]
    with exclusive_gpu_job("grpo-training"):
        require_hardware("train")
        run(command)

    completion = host_run_root / "completion-receipt.json"
    eval_adapter = host_run_root / "eval-adapter"
    run(
        docker_prefix()
        + [
            "run",
            "--rm",
            "--network",
            "none",
            "--volume",
            f"{Path(args.result_root).resolve()}:/results",
            "--volume",
            f"{start_adapter}:/starting-adapter:ro",
            args.train_image,
            "python3",
            "-m",
            "glm47_posttraining.aider_polyglot.charm_grpo_completion",
            "--run-id",
            run_id,
            "--run-root",
            container_run_root,
            "--data-dir",
            f"{container_run_root}/data",
            "--expected-data-manifest-sha256",
            DATA_MANIFEST_SHA256,
            "--source-adapter",
            "/starting-adapter",
            "--expected-source-adapter-sha256",
            SOURCE_ADAPTER_SHA256,
            "--expected-reconstruction-manifest-sha256",
            reconstructed_sha,
            "--num-rollouts",
            "18",
            "--rollout-sample-count",
            "152",
            "--output-receipt",
            f"{container_run_root}/completion-receipt.json",
            "--eval-adapter",
            f"{container_run_root}/eval-adapter",
        ]
    )
    print(f"GRPO_COMPLETION_RECEIPT={completion}")
    print(f"EVAL_ADAPTER={eval_adapter}")


def evaluate(args: argparse.Namespace) -> None:
    verify_repository_inputs()
    eval_adapter = Path(args.eval_adapter).resolve()
    completion_path = Path(args.completion_receipt).resolve()
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    if completion.get("decision") != "PASS":
        raise RuntimeError("GRPO completion receipt is not PASS")
    expected = completion.get("eval_adapter", {})
    model_sha = str(expected.get("adapter_model_sha256", ""))
    config_sha = str(expected.get("adapter_config_sha256", ""))
    training_run_id = str(expected.get("training_run_id", ""))
    require_hash(eval_adapter / "adapter_model.bin", model_sha, "post-GRPO eval adapter")
    require_hash(eval_adapter / "adapter_config.json", config_sha, "post-GRPO eval config")
    require_marker(eval_adapter / ".training-run-id", training_run_id, "post-GRPO run")
    run_id = _run_id(args.run_id, "charm-grpo-r1-fmtlib-r5")
    result_root = Path(args.eval_result_root).resolve()
    result_root.mkdir(parents=True, exist_ok=True)
    inventory: list[dict[str, Any]]
    with exclusive_gpu_job("heldout-evaluation"):
        inventory = require_hardware("eval")
        zone = metadata_value("instance/zone")
        instance = metadata_value("instance/name")
        machine = metadata_value("instance/machine-type", "a2-ultragpu-4g")
        command = docker_prefix() + [
            "run",
            "--rm",
            "--name",
            f"public-pr-{run_id}",
            "--gpus",
            "all",
            "--network",
            "none",
            "--ipc",
            "host",
            "--shm-size",
            "128g",
            "--env",
            f"GCP_PROJECT={args.project}",
            "--env",
            f"GCP_ZONE={zone}",
            "--env",
            f"GCP_INSTANCE={instance}",
            "--env",
            f"GCP_MACHINE_TYPE={machine}",
            "--env",
            f"GCP_DLVM_IMAGE={args.dlvm_image}",
            "--env",
            f"EVAL_IMAGE_ID={image_id(args.eval_image)}",
            "--volume",
            f"{MODEL_DIR}:/models/GLM-4.7-Flash:ro",
            "--volume",
            f"{eval_adapter}:/adapter:ro",
            "--volume",
            f"{result_root}:/results",
            args.eval_image,
            "--model-path",
            "/models/GLM-4.7-Flash",
            "--expected-model-manifest-sha256",
            MODEL_MANIFEST_SHA256,
            "--adapter-path",
            "/adapter",
            "--expected-adapter-model-sha256",
            model_sha,
            "--expected-adapter-config-sha256",
            config_sha,
            "--expected-training-run-id",
            training_run_id,
            "--output-root",
            "/results",
            "--run-id",
            run_id,
            "--suite",
            "fmtlib-demo",
        ]
        run(command)
    receipt = result_root / "runs" / run_id / "run-receipt.json"
    if not receipt.is_file():
        raise RuntimeError("held-out evaluator did not produce its receipt")
    print(f"HELDOUT_EVALUATION_RECEIPT={receipt}")
    print(f"GPU_COUNT={len(inventory)}")


def inspect(_args: argparse.Namespace) -> None:
    config = verify_repository_inputs()
    inventory = gpu_inventory()
    training_supported = len(inventory) == 8 and all(
        "H100" in str(item["name"]) and int(item["memory_mib"]) >= 80_000
        for item in inventory
    )
    evaluation_supported = len(inventory) == 4 and all(
        "A100" in str(item["name"]) and int(item["memory_mib"]) >= 80_000
        for item in inventory
    )
    print(
        json.dumps(
            {
                "gpu_inventory": inventory,
                "grpo_supported": training_supported,
                "heldout_eval_supported": evaluation_supported,
                "simultaneous_gpu_heavy_jobs_supported": False,
                "concurrency_policy": config["gpu_job_concurrency"],
            },
            indent=2,
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.set_defaults(
        train_image=TRAIN_IMAGE,
        verifier_image=VERIFIER_IMAGE,
        eval_image=EVAL_IMAGE,
    )
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect").set_defaults(func=inspect)

    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument(
        "--receipt", default=str(RESULT_ROOT / "preparation-receipt.json")
    )
    prepare_parser.add_argument("--train-image", default=TRAIN_IMAGE)
    prepare_parser.add_argument("--verifier-image", default=VERIFIER_IMAGE)
    prepare_parser.add_argument("--eval-image", default=EVAL_IMAGE)
    prepare_parser.set_defaults(func=prepare)

    reconstruction = sub.add_parser("reconstruct-adapter")
    reconstruction.add_argument("--native-template", required=True)
    reconstruction.add_argument(
        "--source-native-template",
        action="store_true",
        help=(
            "prove and use the pinned source adapter's own complete unmerged "
            "TP-native shards; requires --native-template to equal the source adapter"
        ),
    )
    reconstruction.add_argument(
        "--output-adapter", default=str(RESULT_ROOT / "reconstructed-start-adapter")
    )
    reconstruction.add_argument("--train-image", default=TRAIN_IMAGE)
    reconstruction.set_defaults(func=reconstruct_adapter)

    conversion = sub.add_parser("convert")
    conversion.add_argument("--train-image", default=TRAIN_IMAGE)
    conversion.set_defaults(func=convert)

    training = sub.add_parser("train")
    training.add_argument("--start-adapter", required=True)
    training.add_argument("--run-id")
    training.add_argument("--result-root", default=str(RESULT_ROOT))
    training.add_argument("--train-image", default=TRAIN_IMAGE)
    training.add_argument("--verifier-image", default=VERIFIER_IMAGE)
    training.set_defaults(func=train)

    evaluation = sub.add_parser("eval")
    evaluation.add_argument("--eval-adapter", required=True)
    evaluation.add_argument("--completion-receipt", required=True)
    evaluation.add_argument("--run-id")
    evaluation.add_argument(
        "--eval-result-root", default="/opt/glm47-public-pr/results"
    )
    evaluation.add_argument("--eval-image", default=EVAL_IMAGE)
    evaluation.add_argument("--project", default="lifeandhalf-24122025")
    evaluation.add_argument(
        "--dlvm-image", default="common-cu129-ubuntu-2204-nvidia-580-stage"
    )
    evaluation.set_defaults(func=evaluate)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"CHARM_GRPO_PIPELINE_FAILED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
