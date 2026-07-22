"""Fail-closed preservation gate for a completed canonical Aider GRPO run.

The training gate proves that Miles produced usable checkpoints.  This gate is
deliberately broader: it proves that every expected train/eval rollout dump,
every expected checkpoint slot, and the operational evidence needed to audit
the run are present before a pod is torn down.  It then emits a deterministic
manifest and ``SHA256SUMS`` for every regular file retained beneath the run
root.

The output directory must be outside the run root so the manifest never needs
to describe or hash itself.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_ROLLOUTS = 11
DEFAULT_TRAIN_SAMPLES_PER_DUMP = 256
DEFAULT_EVAL_SAMPLES_PER_DUMP = 22
DEFAULT_TRAIN_SAMPLES = 2_816
DEFAULT_EVAL_SAMPLES = 242
DEFAULT_NATIVE_SHARDS = 4
DEFAULT_TRAINING_STATES = 8


def expected_native_shard_names(
    expected_count: int,
    *,
    tensor_parallel_size: int | None = None,
    expert_parallel_size: int = 1,
    world_size: int | None = None,
) -> set[str]:
    if expected_count <= 0:
        raise ValueError("expected native shard count must be positive")
    tp_size = expected_count if tensor_parallel_size is None else tensor_parallel_size
    if tp_size <= 0 or expert_parallel_size <= 0 or (world_size is not None and world_size <= 0):
        raise ValueError("TP, EP, and world sizes must be positive")
    if expert_parallel_size == 1:
        if expected_count != tp_size:
            raise ValueError("legacy TP-only native shard count must equal TP size")
        return {f"adapter_megatron_tp{tp}_pp0.pt" for tp in range(tp_size)}
    owner_world_size = expected_count if world_size is None else world_size
    names = {
        f"adapter_megatron_tp{rank % tp_size}_pp0_ep{rank % expert_parallel_size}.pt"
        for rank in range(owner_world_size)
    }
    if len(names) != expected_count:
        raise ValueError(
            "EP-aware native shard count does not match the TP/EP owners implied by world size"
        )
    return names


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    if "\n" in value or "\r" in value:
        raise ValueError(f"retained path contains a newline: {value!r}")
    return value


def _require_regular(path: Path, *, label: str, nonempty: bool = True) -> None:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"missing regular {label}: {path}")
    if nonempty and path.stat().st_size == 0:
        raise ValueError(f"empty {label}: {path}")


class _FileInventory:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._records: dict[Path, dict[str, Any]] = {}
        self._signatures: dict[Path, tuple[int, int, int]] = {}

    def record(self, path: Path) -> dict[str, Any]:
        _require_regular(path, label="retained file", nonempty=False)
        stat = path.stat()
        signature = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
        if path in self._records:
            if signature != self._signatures[path]:
                raise RuntimeError(f"retained file changed during verification: {path}")
        else:
            digest = sha256_path(path)
            final_stat = path.stat()
            final_signature = (
                final_stat.st_ino,
                final_stat.st_size,
                final_stat.st_mtime_ns,
            )
            if signature != final_signature:
                raise RuntimeError(f"retained file changed while being hashed: {path}")
            self._records[path] = {
                "path": _relative(path, self.root),
                "size_bytes": final_stat.st_size,
                "sha256": digest,
            }
            self._signatures[path] = final_signature
        return dict(self._records[path])


def _load_rollout_samples(path: Path) -> list[Mapping[str, Any]]:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - the training runtime includes torch
        raise RuntimeError("torch is required to verify Miles rollout dumps") from exc

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:  # Older supported torch releases lack weights_only.
        payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, Mapping):
        raise TypeError(f"rollout dump is not a mapping: {path}")
    samples = payload.get("samples")
    if not isinstance(samples, list):
        raise TypeError(f"rollout dump has no sample list: {path}")
    if not all(isinstance(sample, Mapping) for sample in samples):
        raise TypeError(f"rollout dump contains a non-mapping sample: {path}")
    return samples


def _audit_reward_records(samples: list[Mapping[str, Any]], *, path: Path) -> dict[str, Any]:
    forbidden_reasons = {"reward_exception", "infrastructure_error", "missing_task_path"}
    rewards: list[float] = []
    reasons: Counter[str] = Counter()
    task_ids: Counter[str] = Counter()
    sample_evidence: list[dict[str, Any]] = []
    for index, sample in enumerate(samples):
        record = sample.get("reward")
        if not isinstance(record, Mapping):
            raise RuntimeError(f"non-mapping reward in {path.name} sample {index}")
        score = record.get("score")
        reward = record.get("reward")
        reason = record.get("reason")
        task_id = record.get("task_id")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
            or isinstance(reward, bool)
            or not isinstance(reward, (int, float))
            or not math.isfinite(float(reward))
            or float(score) != float(reward)
        ):
            raise RuntimeError(f"invalid numeric reward in {path.name} sample {index}")
        if record.get("infrastructure_error") is not False:
            raise RuntimeError(f"infrastructure reward record in {path.name} sample {index}")
        if not isinstance(reason, str) or reason in forbidden_reasons:
            raise RuntimeError(f"forbidden reward reason in {path.name} sample {index}: {reason!r}")
        if not isinstance(task_id, str) or not task_id:
            raise RuntimeError(f"missing reward task ID in {path.name} sample {index}")
        rewards.append(float(score))
        reasons[reason] += 1
        task_ids[task_id] += 1
        sample_evidence.append(
            {
                "group_index": sample.get("group_index"),
                "sample_index": sample.get("index"),
                "task_id": task_id,
                "response": str(sample.get("response") or ""),
                "reward": dict(record),
            }
        )
    evidence_text = json.dumps(
        sample_evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return {
        "valid_reward_records": len(rewards),
        "infrastructure_error_records": 0,
        "reward_min": min(rewards),
        "reward_max": max(rewards),
        "reward_mean": sum(rewards) / len(rewards),
        "reasons": dict(sorted(reasons.items())),
        "task_sample_counts": dict(sorted(task_ids.items())),
        "sample_evidence_sha256": hashlib.sha256(evidence_text.encode()).hexdigest(),
    }


def _slot_difference(actual: set[str], expected: set[str]) -> str:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return f"missing={missing}, extra={extra}"


def _verify_rollouts(
    run_root: Path,
    inventory: _FileInventory,
    *,
    expected_rollouts: int,
    expected_train_samples_per_dump: int,
    expected_eval_samples_per_dump: int,
    expected_train_samples: int,
    expected_eval_samples: int,
) -> dict[str, Any]:
    dump_root = run_root / "rollout_dumps"
    if not dump_root.is_dir():
        raise FileNotFoundError(f"missing rollout dump directory: {dump_root}")

    train_names = {f"grpo_{index}.pt" for index in range(expected_rollouts)}
    eval_names = {f"grpo_eval_{index}.pt" for index in range(expected_rollouts)}
    expected_names = train_names | eval_names
    actual_paths = sorted(path for path in dump_root.rglob("*") if path.name.startswith("grpo_"))
    actual_names = {_relative(path, dump_root) for path in actual_paths}
    if actual_names != expected_names:
        raise RuntimeError(
            "rollout dump slots do not match the preservation contract: "
            + _slot_difference(actual_names, expected_names)
        )

    result: dict[str, Any] = {"train": [], "eval": []}
    for stage, names, expected_per_dump in (
        ("train", train_names, expected_train_samples_per_dump),
        ("eval", eval_names, expected_eval_samples_per_dump),
    ):
        for name in sorted(names, key=lambda value: int(value.rsplit("_", 1)[-1][:-3])):
            path = dump_root / name
            _require_regular(path, label=f"{stage} rollout dump")
            samples = _load_rollout_samples(path)
            sample_count = len(samples)
            if sample_count != expected_per_dump:
                raise RuntimeError(
                    f"{name} sample count mismatch: {sample_count} != {expected_per_dump}"
                )
            result[stage].append(
                {
                    **inventory.record(path),
                    "sample_count": sample_count,
                    "reward_audit": _audit_reward_records(samples, path=path),
                }
            )

    train_total = sum(row["sample_count"] for row in result["train"])
    eval_total = sum(row["sample_count"] for row in result["eval"])
    if train_total != expected_train_samples:
        raise RuntimeError(
            f"training sample total mismatch: {train_total} != {expected_train_samples}"
        )
    if eval_total != expected_eval_samples:
        raise RuntimeError(f"eval sample total mismatch: {eval_total} != {expected_eval_samples}")
    result["train_sample_total"] = train_total
    result["eval_sample_total"] = eval_total
    return result


def _verify_validity_inputs_and_signal_gates(
    run_root: Path,
    inventory: _FileInventory,
    rollouts: dict[str, Any],
    *,
    expected_rollouts: int,
) -> dict[str, Any]:
    input_receipt_path = run_root / "input_receipt.json"
    task_split_path = run_root / "task_split.json"
    data_manifest_path = run_root / "data" / "manifest.json"
    train_path = run_root / "data" / "grpo" / "train.jsonl"
    monitor_path = run_root / "data" / "eval" / "train_monitor.jsonl"
    runtime_receipt_path = run_root / "runtime_receipt.json"
    for path, label in (
        (input_receipt_path, "validity input receipt"),
        (task_split_path, "validity task split"),
        (data_manifest_path, "validity data manifest"),
        (train_path, "validity train JSONL"),
        (monitor_path, "validity monitor JSONL"),
        (runtime_receipt_path, "validity runtime receipt"),
    ):
        _require_regular(path, label=label)

    input_receipt = json.loads(input_receipt_path.read_text(encoding="utf-8"))
    task_split = json.loads(task_split_path.read_text(encoding="utf-8"))
    data_manifest = json.loads(data_manifest_path.read_text(encoding="utf-8"))
    runtime_receipt = json.loads(runtime_receipt_path.read_text(encoding="utf-8"))
    train_ids = task_split.get("train_task_ids")
    monitor_ids = task_split.get("monitor_task_ids")
    if (
        input_receipt.get("kind") != "glm47-aider-rl8-input-receipt"
        or input_receipt.get("status") != "passed"
        or not isinstance(train_ids, list)
        or not isinstance(monitor_ids, list)
        or len(train_ids) != len(set(train_ids))
        or len(monitor_ids) != len(set(monitor_ids))
        or set(train_ids) & set(monitor_ids)
        or data_manifest.get("selection", {}).get("train_task_ids") != train_ids
        or data_manifest.get("selection", {}).get("monitor_task_ids") != monitor_ids
        or input_receipt.get("selection") != data_manifest.get("selection")
        or input_receipt.get("task_split_sha256") != sha256_path(task_split_path)
        or input_receipt.get("data_manifest_sha256") != sha256_path(data_manifest_path)
        or input_receipt.get("train_jsonl_sha256") != sha256_path(train_path)
        or input_receipt.get("monitor_jsonl_sha256") != sha256_path(monitor_path)
    ):
        raise RuntimeError("validity input receipt, task split, and data manifest are not bound")
    if (
        runtime_receipt.get("kind") != "glm47-aider-rl8-runtime-receipt"
        or runtime_receipt.get("status") != "passed"
        or runtime_receipt.get("run_id") != run_root.name
        or runtime_receipt.get("gpu_count") != 8
        or not str(runtime_receipt.get("runtime_image_id", "")).startswith("sha256:")
    ):
        raise RuntimeError("validity runtime receipt is incomplete")

    signal_root = run_root / "signal_gates"
    failed = sorted(signal_root.glob("signal_gate_failed_*.json"))
    passed = sorted(signal_root.glob("signal_gate_passed_*.json"))
    if failed or len(passed) != expected_rollouts:
        raise RuntimeError(
            f"signal gate receipt inventory mismatch: passed={len(passed)} failed={len(failed)}"
        )
    by_sequence: dict[int, tuple[Path, dict[str, Any]]] = {}
    for path in passed:
        payload = json.loads(path.read_text(encoding="utf-8"))
        sequence = payload.get("sequence")
        if (
            payload.get("kind") != "glm47-aider-pre-optimizer-signal-gate"
            or payload.get("status") != "passed"
            or not isinstance(sequence, int)
            or sequence in by_sequence
        ):
            raise RuntimeError(f"invalid signal gate receipt: {path}")
        by_sequence[sequence] = (path, payload)
    if set(by_sequence) != set(range(expected_rollouts)):
        raise RuntimeError("signal gate receipt sequences are incomplete")

    gate_records = []
    for sequence in range(expected_rollouts):
        path, payload = by_sequence[sequence]
        rollout_audit = rollouts["train"][sequence]["reward_audit"]
        task_counts = rollout_audit["task_sample_counts"]
        groups = payload.get("groups")
        group_counts = (
            {group.get("task_id"): group.get("sample_count") for group in groups}
            if isinstance(groups, list) and all(isinstance(group, Mapping) for group in groups)
            else {}
        )
        if (
            payload.get("sample_evidence_sha256") != rollout_audit.get("sample_evidence_sha256")
            or set(task_counts) != set(train_ids)
            or group_counts != task_counts
            or payload.get("group_count") != len(train_ids)
            or payload.get("signal_requirements_applied") is not (sequence == 0)
        ):
            raise RuntimeError(f"signal gate receipt does not bind train rollout {sequence}")
        gate_records.append(inventory.record(path))

    for record in rollouts["eval"]:
        counts = record["reward_audit"]["task_sample_counts"]
        if set(counts) != set(monitor_ids) or len(set(counts.values())) != 1:
            raise RuntimeError("eval rollout does not bind the gradient-held-out monitor split")

    return {
        "input_receipt": inventory.record(input_receipt_path),
        "task_split": inventory.record(task_split_path),
        "data_manifest": inventory.record(data_manifest_path),
        "train_jsonl": inventory.record(train_path),
        "monitor_jsonl": inventory.record(monitor_path),
        "runtime_receipt": inventory.record(runtime_receipt_path),
        "signal_gates": gate_records,
        "train_task_ids": train_ids,
        "monitor_task_ids": monitor_ids,
        "runtime": runtime_receipt,
    }


def _verify_checkpoints(
    run_root: Path,
    inventory: _FileInventory,
    *,
    expected_rollouts: int,
    expected_native_shards: int,
    expected_training_states: int,
    tensor_parallel_size: int | None,
    expert_parallel_size: int,
) -> list[dict[str, Any]]:
    checkpoint_root = run_root / "checkpoints" / "grpo_lora_r16"
    if not checkpoint_root.is_dir():
        raise FileNotFoundError(f"missing checkpoint directory: {checkpoint_root}")

    expected_slots = {f"iter_{index:07d}" for index in range(expected_rollouts)}
    slot_entries = {
        path.name for path in checkpoint_root.iterdir() if path.name.startswith("iter_")
    }
    if slot_entries != expected_slots:
        raise RuntimeError(
            "checkpoint slots do not match the preservation contract: "
            + _slot_difference(slot_entries, expected_slots)
        )

    expected_native = expected_native_shard_names(
        expected_native_shards,
        tensor_parallel_size=tensor_parallel_size,
        expert_parallel_size=expert_parallel_size,
        world_size=expected_training_states,
    )
    expected_training = {
        f"training_state_rank{index}.pt" for index in range(expected_training_states)
    }
    checkpoints: list[dict[str, Any]] = []
    for iteration in range(expected_rollouts):
        slot = f"iter_{iteration:07d}"
        iteration_dir = checkpoint_root / slot
        if not iteration_dir.is_dir() or iteration_dir.is_symlink():
            raise FileNotFoundError(f"checkpoint slot is not a regular directory: {iteration_dir}")
        adapter = iteration_dir / "adapter"
        if not adapter.is_dir() or adapter.is_symlink():
            raise FileNotFoundError(f"missing checkpoint adapter directory: {adapter}")

        model = adapter / "adapter_model.bin"
        config = adapter / "adapter_config.json"
        _require_regular(model, label="consolidated adapter")
        _require_regular(config, label="adapter config")
        config_payload = json.loads(config.read_text(encoding="utf-8"))
        if not isinstance(config_payload, dict):
            raise TypeError(f"adapter config is not a JSON object: {config}")

        native_candidates = {
            path.name for path in adapter.iterdir() if path.name.startswith("adapter_megatron_")
        }
        if native_candidates != expected_native:
            raise RuntimeError(
                f"{slot} native shard slots do not match the preservation contract: "
                + _slot_difference(native_candidates, expected_native)
            )
        training_candidates = {
            path.name for path in adapter.iterdir() if path.name.startswith("training_state_rank")
        }
        if training_candidates != expected_training:
            raise RuntimeError(
                f"{slot} training-state slots do not match the preservation contract: "
                + _slot_difference(training_candidates, expected_training)
            )

        native_paths = [adapter / name for name in sorted(expected_native)]
        training_paths = [adapter / name for name in sorted(expected_training)]
        for path in native_paths:
            _require_regular(path, label="Megatron-native adapter shard")
        for path in training_paths:
            _require_regular(path, label="per-rank training state")
        checkpoints.append(
            {
                "iteration": iteration,
                "slot": slot,
                "adapter_model": inventory.record(model),
                "adapter_config": inventory.record(config),
                "native_shards": [inventory.record(path) for path in native_paths],
                "training_states": [inventory.record(path) for path in training_paths],
            }
        )
    return checkpoints


def _regular_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and not path.is_symlink()),
        key=lambda path: _relative(path, root),
    )


def _verify_evidence(
    run_root: Path,
    inventory: _FileInventory,
    *,
    checkpoints: list[dict[str, Any]],
    expected_rollouts: int,
    expected_native_shards: int,
    expected_training_states: int,
    tensor_parallel_size: int,
    expert_parallel_size: int,
    validity_inputs: Mapping[str, Any] | None = None,
    require_gpu_activity: bool = False,
) -> dict[str, Any]:
    stage_root = run_root / "grpo_lora_r16"
    run_log = stage_root / "run.log"
    gate_path = stage_root / "grpo_training_gate.json"
    receipt_path = stage_root / "run_receipt.txt"
    for path, label in (
        (run_log, "training log"),
        (gate_path, "training gate"),
        (receipt_path, "run receipt"),
    ):
        _require_regular(path, label=label)

    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if (
        not isinstance(gate, dict)
        or gate.get("schema_version") != 1
        or gate.get("kind") != "glm47-aider-grpo-training-gate"
        or gate.get("status") != "passed"
    ):
        raise RuntimeError("training gate is missing a passed status")
    expected_gate_fields = {
        "run_id": run_root.name,
        "gpus_per_node": expected_training_states,
        "tensor_parallel_size": tensor_parallel_size,
        "expert_parallel_size": expert_parallel_size,
        "num_rollout": expected_rollouts,
    }
    gate_mismatches = {
        key: {"actual": gate.get(key), "expected": expected}
        for key, expected in expected_gate_fields.items()
        if gate.get(key) != expected
    }
    try:
        gate_run_root_matches = Path(str(gate.get("run_root"))).resolve() == run_root
    except (OSError, RuntimeError, TypeError, ValueError):
        gate_run_root_matches = False
    if gate_mismatches or not gate_run_root_matches:
        raise RuntimeError(
            "training gate is not bound to this preservation contract: "
            f"field_mismatches={gate_mismatches}, run_root_matches={gate_run_root_matches}"
        )
    if validity_inputs is not None:
        runtime = validity_inputs.get("runtime")
        if not isinstance(runtime, Mapping) or runtime.get("source_commit") != gate.get(
            "source_commit"
        ):
            raise RuntimeError("runtime receipt and training gate source commits disagree")

    gate_checkpoints = gate.get("checkpoints")
    if not isinstance(gate_checkpoints, list) or len(gate_checkpoints) != expected_rollouts:
        raise RuntimeError("training gate checkpoint inventory is incomplete")
    for actual, recorded in zip(checkpoints, gate_checkpoints):
        if not isinstance(recorded, Mapping):
            raise RuntimeError("training gate checkpoint record is invalid")
        actual_native = {
            Path(item["path"]).name: item["sha256"] for item in actual["native_shards"]
        }
        actual_training = sorted(Path(item["path"]).name for item in actual["training_states"])
        if (
            recorded.get("iteration") != actual["iteration"]
            or recorded.get("adapter_model_sha256") != actual["adapter_model"]["sha256"]
            or recorded.get("adapter_config_sha256") != actual["adapter_config"]["sha256"]
            or recorded.get("native_shards") != actual_native
            or recorded.get("training_state_files") != actual_training
        ):
            raise RuntimeError(
                f"training gate checkpoint record does not match retained {actual['slot']}"
            )
    latest = gate.get("latest_checkpoint")
    if latest != gate_checkpoints[-1]:
        raise RuntimeError("training gate latest-checkpoint record is inconsistent")
    if any(
        len(checkpoint["native_shards"]) != expected_native_shards for checkpoint in checkpoints
    ):
        raise RuntimeError("retained checkpoint native-shard counts are inconsistent")

    receipt: dict[str, str] = {}
    for line in receipt_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            receipt[key.strip()] = value.strip()
    if receipt.get("status") != "success" or receipt.get("training_gate_status") != "passed":
        raise RuntimeError("run receipt does not record successful training and a passed gate")
    expected_receipt_fields = {
        "run_id": run_root.name,
        "run_root": str(run_root),
        "num_rollout": str(expected_rollouts),
        "gpus_per_node": str(expected_training_states),
        "tensor_model_parallel_size": str(tensor_parallel_size),
        "expert_model_parallel_size": str(expert_parallel_size),
        "training_gate": str(gate_path),
    }
    receipt_mismatches = {
        key: {"actual": receipt.get(key), "expected": expected}
        for key, expected in expected_receipt_fields.items()
        if receipt.get(key) != expected
    }
    if receipt_mismatches:
        raise RuntimeError(
            "run receipt is not bound to this preservation contract: "
            f"field_mismatches={receipt_mismatches}"
        )
    continuation_mode = receipt.get("grpo_continuation_mode", "none")
    reconstruction_sha256 = receipt.get("expected_native_reconstruction_manifest_sha256", "none")
    gate_reconstruction = gate.get("native_reconstruction_manifest")
    requires_reconstruction = expert_parallel_size > 1 or continuation_mode != "none"
    if requires_reconstruction and (
        continuation_mode not in {"none", "weights_only_fresh_optimizer"}
        or not re.fullmatch(r"[0-9a-f]{64}", reconstruction_sha256)
        or not isinstance(gate_reconstruction, Mapping)
        or gate_reconstruction.get("sha256") != reconstruction_sha256
        or gate_reconstruction.get("status") != "passed"
        or gate_reconstruction.get("source_hf_roundtrip_status") != "passed"
        or gate_reconstruction.get("native_shard_count") != expected_native_shards
    ):
        raise RuntimeError("receipt and gate do not bind a passed native reconstruction proof")

    wandb_root = run_root / "wandb"
    sync_root = run_root / "sync_metrics"
    if not wandb_root.is_dir():
        raise FileNotFoundError(f"missing W&B evidence directory: {wandb_root}")
    if not sync_root.is_dir():
        raise FileNotFoundError(f"missing synchronization evidence directory: {sync_root}")
    wandb_files = _regular_files(wandb_root)
    sync_files = _regular_files(sync_root)
    if not wandb_files or not any(path.stat().st_size for path in wandb_files):
        raise RuntimeError("W&B evidence directory contains no nonempty regular file")
    if not sync_files or not any(path.stat().st_size for path in sync_files):
        raise RuntimeError("synchronization evidence directory contains no nonempty regular file")

    logs = sorted(
        (path for path in _regular_files(run_root) if path.suffix.lower() == ".log"),
        key=lambda path: _relative(path, run_root),
    )
    if run_log not in logs:
        raise RuntimeError("canonical training log is absent from the log inventory")
    gpu_activity = None
    if require_gpu_activity:
        vram_path = stage_root / "vram_usage.csv"
        _require_regular(vram_path, label="GPU activity log")
        maxima: dict[int, dict[str, float]] = {}
        with vram_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    index = int(str(row["index"]).strip())
                    memory = float(str(row["memory.used"]).strip())
                    utilization = float(str(row["utilization.gpu"]).strip())
                except (KeyError, TypeError, ValueError) as exc:
                    raise RuntimeError("GPU activity log contains an invalid row") from exc
                record = maxima.setdefault(index, {"memory_used_mib": 0.0, "utilization_gpu": 0.0})
                record["memory_used_mib"] = max(record["memory_used_mib"], memory)
                record["utilization_gpu"] = max(record["utilization_gpu"], utilization)
        expected_indices = set(range(expected_training_states))
        if set(maxima) != expected_indices or any(
            record["memory_used_mib"] < 10_000 for record in maxima.values()
        ):
            raise RuntimeError(f"all-GPU activity contract failed: {maxima}")
        gpu_activity = {
            "vram_log": inventory.record(vram_path),
            "per_gpu_maxima": {str(key): value for key, value in sorted(maxima.items())},
        }
    return {
        "logs": [inventory.record(path) for path in logs],
        "wandb": {
            "root": _relative(wandb_root, run_root),
            "files": [inventory.record(path) for path in wandb_files],
        },
        "sync": {
            "root": _relative(sync_root, run_root),
            "files": [inventory.record(path) for path in sync_files],
        },
        "training_gate": inventory.record(gate_path),
        "run_receipt": inventory.record(receipt_path),
        "gpu_activity": gpu_activity,
    }


def _inventory_all(
    run_root: Path, inventory: _FileInventory
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    retained: list[dict[str, Any]] = []
    symlinks: list[dict[str, str]] = []
    resolved_root = run_root.resolve()
    for path in sorted(run_root.rglob("*"), key=lambda item: _relative(item, run_root)):
        if path.is_symlink():
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(resolved_root)
            except (FileNotFoundError, ValueError) as exc:
                raise RuntimeError(
                    f"retained symlink is broken or escapes the run root: {path}"
                ) from exc
            symlinks.append({"path": _relative(path, run_root), "target": os.readlink(path)})
        elif path.is_file():
            retained.append(inventory.record(path))
        elif path.is_dir():
            continue
        else:
            raise RuntimeError(f"unsupported retained filesystem entry: {path}")
    return retained, symlinks


def verify_preservation(
    run_root: Path,
    output_dir: Path,
    *,
    expected_rollouts: int = DEFAULT_ROLLOUTS,
    expected_train_samples_per_dump: int = DEFAULT_TRAIN_SAMPLES_PER_DUMP,
    expected_eval_samples_per_dump: int = DEFAULT_EVAL_SAMPLES_PER_DUMP,
    expected_train_samples: int = DEFAULT_TRAIN_SAMPLES,
    expected_eval_samples: int = DEFAULT_EVAL_SAMPLES,
    expected_native_shards: int = DEFAULT_NATIVE_SHARDS,
    expected_training_states: int = DEFAULT_TRAINING_STATES,
    tensor_parallel_size: int | None = None,
    expert_parallel_size: int = 1,
    require_signal_gates: bool = False,
    require_gpu_activity: bool = False,
) -> dict[str, Any]:
    run_root = run_root.resolve()
    output_dir = output_dir.resolve()
    if not run_root.is_dir():
        raise FileNotFoundError(f"missing run root: {run_root}")
    try:
        output_dir.relative_to(run_root)
    except ValueError:
        pass
    else:
        raise ValueError("preservation output directory must be outside the retained run root")
    if output_dir.exists():
        raise FileExistsError(f"refusing to replace preservation output: {output_dir}")
    positive_contract_values = {
        "expected_rollouts": expected_rollouts,
        "expected_train_samples_per_dump": expected_train_samples_per_dump,
        "expected_eval_samples_per_dump": expected_eval_samples_per_dump,
        "expected_train_samples": expected_train_samples,
        "expected_eval_samples": expected_eval_samples,
        "expected_native_shards": expected_native_shards,
        "expected_training_states": expected_training_states,
        "tensor_parallel_size": (
            expected_native_shards if tensor_parallel_size is None else tensor_parallel_size
        ),
        "expert_parallel_size": expert_parallel_size,
    }
    invalid = {key: value for key, value in positive_contract_values.items() if value <= 0}
    if invalid:
        raise ValueError(f"preservation contract values must be positive: {invalid}")
    if expected_rollouts * expected_train_samples_per_dump != expected_train_samples:
        raise ValueError("training per-dump and total sample contracts disagree")
    if expected_rollouts * expected_eval_samples_per_dump != expected_eval_samples:
        raise ValueError("eval per-dump and total sample contracts disagree")

    inventory = _FileInventory(run_root)
    rollouts = _verify_rollouts(
        run_root,
        inventory,
        expected_rollouts=expected_rollouts,
        expected_train_samples_per_dump=expected_train_samples_per_dump,
        expected_eval_samples_per_dump=expected_eval_samples_per_dump,
        expected_train_samples=expected_train_samples,
        expected_eval_samples=expected_eval_samples,
    )
    validity_inputs = (
        _verify_validity_inputs_and_signal_gates(
            run_root,
            inventory,
            rollouts,
            expected_rollouts=expected_rollouts,
        )
        if require_signal_gates
        else None
    )
    checkpoints = _verify_checkpoints(
        run_root,
        inventory,
        expected_rollouts=expected_rollouts,
        expected_native_shards=expected_native_shards,
        expected_training_states=expected_training_states,
        tensor_parallel_size=tensor_parallel_size,
        expert_parallel_size=expert_parallel_size,
    )
    effective_tensor_parallel_size = (
        expected_native_shards if tensor_parallel_size is None else tensor_parallel_size
    )
    evidence = _verify_evidence(
        run_root,
        inventory,
        checkpoints=checkpoints,
        expected_rollouts=expected_rollouts,
        expected_native_shards=expected_native_shards,
        expected_training_states=expected_training_states,
        tensor_parallel_size=effective_tensor_parallel_size,
        expert_parallel_size=expert_parallel_size,
        validity_inputs=validity_inputs,
        require_gpu_activity=require_gpu_activity,
    )
    retained_files, symlinks = _inventory_all(run_root, inventory)
    confirmed_files, confirmed_symlinks = _inventory_all(run_root, inventory)
    if confirmed_files != retained_files or confirmed_symlinks != symlinks:
        raise RuntimeError("retained run contents changed during verification")

    sha256sums = "".join(f"{record['sha256']}  {record['path']}\n" for record in retained_files)
    manifest = {
        "schema_version": 1,
        "kind": "glm47-grpo-preservation-manifest",
        "status": "passed",
        "run_id": run_root.name,
        "contract": {
            "rollouts": expected_rollouts,
            "train_samples_per_dump": expected_train_samples_per_dump,
            "eval_samples_per_dump": expected_eval_samples_per_dump,
            "train_samples": expected_train_samples,
            "eval_samples": expected_eval_samples,
            "native_shards_per_checkpoint": expected_native_shards,
            "training_states_per_checkpoint": expected_training_states,
            "tensor_parallel_size": (
                expected_native_shards if tensor_parallel_size is None else tensor_parallel_size
            ),
            "expert_parallel_size": expert_parallel_size,
            "signal_gates_required": require_signal_gates,
            "gpu_activity_required": require_gpu_activity,
        },
        "rollout_evidence": rollouts,
        "validity_evidence": validity_inputs,
        "checkpoints": checkpoints,
        "operational_evidence": evidence,
        "retained_file_count": len(retained_files),
        "retained_files": retained_files,
        "symlinks": symlinks,
        "sha256sums_sha256": hashlib.sha256(sha256sums.encode("utf-8")).hexdigest(),
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        (staging / "preservation_manifest.json").write_text(manifest_text, encoding="utf-8")
        (staging / "SHA256SUMS").write_text(sha256sums, encoding="utf-8")
        os.replace(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--expected-rollouts", type=int, default=DEFAULT_ROLLOUTS)
    parser.add_argument(
        "--expected-train-samples-per-dump",
        type=int,
        default=DEFAULT_TRAIN_SAMPLES_PER_DUMP,
    )
    parser.add_argument(
        "--expected-eval-samples-per-dump",
        type=int,
        default=DEFAULT_EVAL_SAMPLES_PER_DUMP,
    )
    parser.add_argument("--expected-train-samples", type=int, default=DEFAULT_TRAIN_SAMPLES)
    parser.add_argument("--expected-eval-samples", type=int, default=DEFAULT_EVAL_SAMPLES)
    parser.add_argument("--expected-native-shards", type=int, default=DEFAULT_NATIVE_SHARDS)
    parser.add_argument("--expected-training-states", type=int, default=DEFAULT_TRAINING_STATES)
    parser.add_argument("--tensor-parallel-size", type=int)
    parser.add_argument("--expert-parallel-size", type=int, default=1)
    parser.add_argument("--require-signal-gates", action="store_true")
    parser.add_argument("--require-gpu-activity", action="store_true")
    args = parser.parse_args()
    manifest = verify_preservation(
        args.run_root,
        args.output_dir,
        expected_rollouts=args.expected_rollouts,
        expected_train_samples_per_dump=args.expected_train_samples_per_dump,
        expected_eval_samples_per_dump=args.expected_eval_samples_per_dump,
        expected_train_samples=args.expected_train_samples,
        expected_eval_samples=args.expected_eval_samples,
        expected_native_shards=args.expected_native_shards,
        expected_training_states=args.expected_training_states,
        tensor_parallel_size=args.tensor_parallel_size,
        expert_parallel_size=args.expert_parallel_size,
        require_signal_gates=args.require_signal_gates,
        require_gpu_activity=args.require_gpu_activity,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "run_id": manifest["run_id"],
                "retained_file_count": manifest["retained_file_count"],
                "manifest": str(args.output_dir / "preservation_manifest.json"),
                "sha256sums": str(args.output_dir / "SHA256SUMS"),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
