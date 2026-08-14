#!/usr/bin/env python3
"""Certify a quarantined one-update GRPO smoke and GCS round-trip."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from glm47_posttraining.aider_polyglot.parser import segment_glm47_response
from glm47_posttraining.aider_polyglot.hybrid45 import validate_hybrid45_receipt


DEFAULT_PROFILE_ID = "aider-full-v5-experimental-unadmitted-r3-thinking-final-v1-smoke"
DEFAULT_RUN_ID_PREFIX = "unadmitted-r3-smoke-"
DEFAULT_PERMIT_FIELD = "permits_r3_57_update_launch"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPECTED_NATIVE = {
    f"adapter/adapter_megatron_tp{rank % 4}_pp0_ep{rank}.pt" for rank in range(8)
}
EXPECTED_TRAINING_STATE = {
    f"adapter/training_state_rank{rank}.pt" for rank in range(8)
}
FATAL_RUNTIME_PATTERNS = {
    "cuda_oom": re.compile(
        r"CUDA out of memory|OutOfMemoryError|CUresult error:\s*2\s*\(out of memory\)",
        re.IGNORECASE,
    ),
    "gpu_xid": re.compile(r"NVRM:\s*Xid|Xid\s*\(", re.IGNORECASE),
    "nccl_failure": re.compile(
        r"NCCL error|ncclUnhandled|DistBackendError|Watchdog caught collective",
        re.IGNORECASE,
    ),
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def training_rollout_paths(rollout_root: Path) -> list[Path]:
    return sorted(
        path
        for path in rollout_root.glob("grpo_*.pt")
        if re.fullmatch(r"grpo_[0-9]+\.pt", path.name)
    )


def require_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular JSON artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON artifact must contain an object: {path}")
    return payload


def parse_key_value(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular run receipt: {path}")
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def validate_complete_marker(
    marker_path: Path,
    *,
    local_checkpoint: Path,
    recovered_checkpoint: Path,
) -> dict[str, Any]:
    marker = require_json(marker_path)
    manifest_keys = (
        "schema_version",
        "status",
        "iteration",
        "checkpoint",
        "file_count",
        "total_bytes",
        "files",
    )
    manifest = {key: marker.get(key) for key in manifest_keys}
    if (
        manifest["schema_version"] != "glm47-gcs-checkpoint-complete-v1"
        or manifest["status"] != "COMPLETE"
        or marker.get("manifest_sha256") != canonical_sha256(manifest)
        or not isinstance(manifest["files"], list)
        or manifest["file_count"] != len(manifest["files"])
    ):
        raise RuntimeError("GCS checkpoint COMPLETE marker is invalid")

    observed_native: set[str] = set()
    observed_training: set[str] = set()
    total_bytes = 0
    for item in manifest["files"]:
        if not isinstance(item, Mapping):
            raise TypeError("checkpoint manifest file record is not a mapping")
        relative = item.get("path")
        expected_size = item.get("size_bytes")
        expected_sha256 = item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative.startswith("/")
            or ".." in Path(relative).parts
            or isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size <= 0
            or not isinstance(expected_sha256, str)
            or SHA256_RE.fullmatch(expected_sha256) is None
        ):
            raise RuntimeError(f"invalid checkpoint manifest file record: {item}")
        local = local_checkpoint / relative
        recovered = recovered_checkpoint / relative
        for candidate, label in ((local, "local"), (recovered, "recovered")):
            if candidate.is_symlink() or not candidate.is_file():
                raise FileNotFoundError(f"missing {label} checkpoint file: {candidate}")
            if candidate.stat().st_size != expected_size:
                raise RuntimeError(f"{label} checkpoint size mismatch: {candidate}")
            if sha256_path(candidate) != expected_sha256:
                raise RuntimeError(f"{label} checkpoint digest mismatch: {candidate}")
        total_bytes += expected_size
        if relative.startswith("adapter/adapter_megatron_"):
            observed_native.add(relative)
        if relative.startswith("adapter/training_state_rank"):
            observed_training.add(relative)
    if observed_native != EXPECTED_NATIVE:
        raise RuntimeError("checkpoint does not contain the exact eight native shards")
    if observed_training != EXPECTED_TRAINING_STATE:
        raise RuntimeError("checkpoint does not contain the exact eight training states")
    if total_bytes != manifest["total_bytes"]:
        raise RuntimeError("checkpoint total byte count differs from COMPLETE marker")
    return marker


def validate_rollout(
    path: Path,
    *,
    expected_group_count: int = 29,
    expected_reward_mode: str | None = None,
) -> dict[str, Any]:
    import torch

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:  # pragma: no cover - older training torch
        payload = torch.load(path, map_location="cpu")
    samples = payload.get("samples") if isinstance(payload, Mapping) else None
    expected_sample_count = expected_group_count * 8
    if not isinstance(samples, list) or len(samples) != expected_sample_count:
        raise RuntimeError(
            "smoke rollout sample count mismatch: "
            f"{len(samples) if isinstance(samples, list) else 'invalid'} "
            f"!= {expected_group_count} groups x 8 samples"
        )
    exact = 0
    thinking_boundaries = 0
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping) or not isinstance(sample.get("reward"), Mapping):
            raise RuntimeError(f"rollout sample {index} has no reward mapping")
        reward = sample["reward"]
        if (
            expected_reward_mode is not None
            and reward.get("reward_mode") != expected_reward_mode
        ):
            raise RuntimeError(f"rollout sample {index} has the wrong reward mode")
        if expected_reward_mode == "hybrid_bipolar45":
            hybrid45 = reward.get("hybrid45")
            if not isinstance(hybrid45, Mapping):
                raise RuntimeError(f"rollout sample {index} lacks a Hybrid45 V2 receipt")
            receipt = validate_hybrid45_receipt(hybrid45)
            if receipt.optimizer_score != reward.get("score"):
                raise RuntimeError(
                    f"rollout sample {index} score differs from Hybrid45 projection"
                )
        raw_response = str(sample.get("response") or reward.get("response") or "")
        segments = segment_glm47_response(raw_response)
        if (
            reward.get("response") != raw_response
            or reward.get("response_contract") != "glm47-thinking-final-answer-v1"
            or reward.get("thinking_boundary_applied")
            is not segments.thinking_boundary_applied
            or reward.get("scored_response_sha256")
            != hashlib.sha256(segments.final_answer.encode("utf-8")).hexdigest()
        ):
            raise RuntimeError(f"rollout sample {index} violates the response boundary receipt")
        exact += int(reward.get("format_valid") is True)
        thinking_boundaries += int(segments.thinking_boundary_applied)
    return {
        "path": str(path),
        "sha256": sha256_path(path),
        "sample_count": len(samples),
        "exact_final_answer_count": exact,
        "exact_final_answer_rate": exact / len(samples),
        "thinking_boundary_count": thinking_boundaries,
    }


def certify(
    run_id: str,
    run_root: Path,
    recovered_root: Path,
    *,
    expected_profile_id: str = DEFAULT_PROFILE_ID,
    run_id_prefix: str = DEFAULT_RUN_ID_PREFIX,
    permit_field: str = DEFAULT_PERMIT_FIELD,
    expected_group_count: int = 29,
    expected_reward_mode: str = "production_ast17",
) -> dict[str, Any]:
    if (
        RUN_ID_RE.fullmatch(run_id) is None
        or not run_id.startswith(run_id_prefix)
        or run_root.name != run_id
        or not expected_profile_id
        or not re.fullmatch(r"permits_r[0-9]+(?:_v[0-9]+)?_57_update_launch", permit_field)
        or expected_group_count <= 0
        or expected_reward_mode not in {"production_ast17", "hybrid_bipolar45"}
    ):
        raise ValueError("smoke run ID or run root is invalid")
    launch = require_json(run_root / "launch-contract.json")
    execution = require_json(run_root / "execution-receipt.json")
    environment = launch.get("environment", {})
    images = launch.get("images", {})
    if (
        launch.get("status") != "authorized"
        or launch.get("profile_id") != expected_profile_id
        or launch.get("phase") != "experimental"
        or launch.get("charm_eligible") is not False
        or launch.get("checkpoint_disposition") != "QUARANTINE_ONLY"
        or execution.get("status") != "passed"
        or execution.get("profile_id") != expected_profile_id
        or execution.get("charm_eligible") is not False
        or environment.get("MILES_NUM_ROLLOUT") != "1"
        or environment.get("MILES_ROLLOUT_BATCH_SIZE") != str(expected_group_count)
        or environment.get("MILES_N_SAMPLES_PER_PROMPT") != "8"
        or environment.get("MILES_SAVE_INTERVAL") != "1"
        or environment.get("MILES_AIDER_REWARD_MODE") != expected_reward_mode
        or environment.get("GLM47_CHARM_ELIGIBLE") != "0"
    ):
        raise RuntimeError("smoke launch/execution quarantine contract is invalid")
    for image in (images.get("training"), images.get("verifier")):
        if not isinstance(image, Mapping) or IMAGE_ID_RE.fullmatch(
            str(image.get("image_id", ""))
        ) is None:
            raise RuntimeError("smoke launch does not bind immutable Docker image IDs")

    sync = execution.get("result_sync", {})
    if (
        sync.get("final_status") != "passed"
        or int(sync.get("consecutive_successes", 0)) < 2
        or sync.get("periodic_failures") != []
        or len(sync.get("published_checkpoints", {})) != 1
    ):
        raise RuntimeError("smoke durable GCS synchronization gate did not pass")

    failed_signals = list((run_root / "signal-gates").glob("signal_gate_failed_*.json"))
    passed_signals = list((run_root / "signal-gates").glob("signal_gate_passed_*.json"))
    if failed_signals or len(passed_signals) != 1:
        raise RuntimeError("smoke must contain exactly one passing signal gate")
    signal = require_json(passed_signals[0])
    if (
        signal.get("status") != "passed"
        or signal.get("signal_requirements_applied") is not True
        or signal.get("group_count") != expected_group_count
        or signal.get("samples_per_group") != 8
        or signal.get("positive_groups", 0) < 1
        or signal.get("semantic_variance_groups", 0) < 2
        or signal.get("reward_variance_groups", 0) < 2
        or signal.get("exact_format_rate", 0.0) < 0.5
        or signal.get("compile_rate", 0.0) < 0.2
        or (
            expected_reward_mode == "hybrid_bipolar45"
            and (
                signal.get("hybrid45_groups") != expected_group_count
                or signal.get("kernel_variance_groups", 0) < 2
            )
        )
    ):
        raise RuntimeError("smoke pre-optimizer signal gate evidence is insufficient")

    runner = parse_key_value(run_root / "grpo_lora_r16/run_receipt.txt")
    if (
        runner.get("status") != "success"
        or runner.get("ray_status") != "0"
        or runner.get("num_rollout") != "1"
        or runner.get("rollout_batch_size") != str(expected_group_count)
        or runner.get("n_samples_per_prompt") != "8"
        or runner.get("checkpoint_disposition") != "QUARANTINE_ONLY"
    ):
        raise RuntimeError("Miles one-update run receipt did not pass")

    log_path = run_root / "grpo_lora_r16/run.log"
    if log_path.is_symlink() or not log_path.is_file():
        raise FileNotFoundError(f"missing Miles run log: {log_path}")
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    runtime_errors = [name for name, pattern in FATAL_RUNTIME_PATTERNS.items() if pattern.search(log_text)]
    if runtime_errors:
        raise RuntimeError(f"fatal GPU/distributed errors found in run log: {runtime_errors}")

    local_checkpoints = sorted((run_root / "checkpoints/grpo_lora_r16").glob("iter_*"))
    recovered_checkpoints = sorted(
        (recovered_root / "checkpoints/grpo_lora_r16").glob("iter_*")
    )
    if len(local_checkpoints) != 1 or len(recovered_checkpoints) != 1:
        raise RuntimeError("smoke requires exactly one local and recovered checkpoint")
    local_checkpoint = local_checkpoints[0]
    recovered_checkpoint = recovered_checkpoints[0]
    if local_checkpoint.name != recovered_checkpoint.name:
        raise RuntimeError("local and recovered checkpoint slots differ")
    marker = validate_complete_marker(
        recovered_checkpoint / "COMPLETE.json",
        local_checkpoint=local_checkpoint,
        recovered_checkpoint=recovered_checkpoint,
    )
    local_marker = require_json(
        run_root / f"sync_receipts/checkpoints/{local_checkpoint.name}.COMPLETE.json"
    )
    if local_marker != marker:
        raise RuntimeError("local and GCS-recovered completion markers differ")

    adapter_sha256 = sha256_path(local_checkpoint / "adapter/adapter_model.bin")
    starting_sha256 = str(launch.get("assets", {}).get("adapter_model_sha256", ""))
    if SHA256_RE.fullmatch(starting_sha256) is None or adapter_sha256 == starting_sha256:
        raise RuntimeError("smoke checkpoint does not prove an optimizer weight update")
    rollout_paths = training_rollout_paths(run_root / "rollout_dumps")
    if len(rollout_paths) != 1:
        raise RuntimeError("smoke requires exactly one durable rollout dump")
    rollout = validate_rollout(
        rollout_paths[0],
        expected_group_count=expected_group_count,
        expected_reward_mode=expected_reward_mode,
    )
    if rollout["exact_final_answer_rate"] < 0.5:
        raise RuntimeError("replayed post-thinking exact-format rate is below 50%")

    return {
        "schema_version": "glm47-unadmitted-grpo-smoke-v1",
        "decision": "PASS",
        "completed_at_utc": execution.get("completed_at_utc"),
        "run_id": run_id,
        "profile_id": expected_profile_id,
        "reward_mode": expected_reward_mode,
        "charm_eligible": False,
        "checkpoint_disposition": "QUARANTINE_ONLY",
        "retroactive_admission_allowed": False,
        permit_field: True,
        "launch_contract_sha256": sha256_path(run_root / "launch-contract.json"),
        "execution_receipt_sha256": sha256_path(run_root / "execution-receipt.json"),
        "signal_gate": {
            "sha256": sha256_path(passed_signals[0]),
            "group_count": signal["group_count"],
            "samples_per_group": signal["samples_per_group"],
            "positive_groups": signal["positive_groups"],
            "semantic_variance_groups": signal["semantic_variance_groups"],
            "reward_variance_groups": signal["reward_variance_groups"],
            "kernel_variance_groups": signal.get("kernel_variance_groups", 0),
            "hybrid45_groups": signal.get("hybrid45_groups", 0),
            "exact_format_rate": signal["exact_format_rate"],
            "compile_rate": signal["compile_rate"],
        },
        "training": {
            "ray_status": 0,
            "optimizer_updates_proven": 1,
            "starting_adapter_sha256": starting_sha256,
            "checkpoint_adapter_sha256": adapter_sha256,
            "proof": [
                "passing pre-optimizer rollout signal gate",
                "successful Ray training process",
                "post-update iteration checkpoint with eight training states",
                "checkpoint adapter differs from SynthMem ep50",
            ],
        },
        "runtime_health": {"fatal_error_patterns": runtime_errors},
        "checkpoint": {
            "iteration": marker["iteration"],
            "file_count": marker["file_count"],
            "total_bytes": marker["total_bytes"],
            "manifest_sha256": marker["manifest_sha256"],
            "gcs_destination": marker["gcs_destination"],
            "roundtrip_verified": True,
        },
        "rollout": rollout,
        "images": images,
        "result_sync": {
            "consecutive_successes": sync["consecutive_successes"],
            "successful_sync_receipts": sync["successful_sync_receipts"],
            "periodic_failures": [],
        },
    }


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite smoke receipt: {path}")
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--recovered-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-profile-id", default=DEFAULT_PROFILE_ID)
    parser.add_argument("--run-id-prefix", default=DEFAULT_RUN_ID_PREFIX)
    parser.add_argument("--permit-field", default=DEFAULT_PERMIT_FIELD)
    parser.add_argument("--expected-group-count", type=int, default=29)
    parser.add_argument(
        "--expected-reward-mode",
        choices=("production_ast17", "hybrid_bipolar45"),
        default="production_ast17",
    )
    args = parser.parse_args()
    receipt = certify(
        args.run_id,
        args.run_root.resolve(),
        args.recovered_root.resolve(),
        expected_profile_id=args.expected_profile_id,
        run_id_prefix=args.run_id_prefix,
        permit_field=args.permit_field,
        expected_group_count=args.expected_group_count,
        expected_reward_mode=args.expected_reward_mode,
    )
    atomic_json(args.output, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
