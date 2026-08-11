"""Reconstruct GLM-4.7 TP-native LoRA shards from a complete HF adapter.

The GLM/Miles checkpoint contains two views of the same LoRA state:

* ``adapter_model.bin`` uses Hugging Face/PEFT names and global tensors.
* ``adapter_megatron_tp*_pp0.pt`` uses fused Megatron names and TP-local
  tensors.

This utility learns the fixed layout from a *complete* rank-preserving
template adapter.  Before writing any output, it reconstructs every template
native tensor from the template HF state and requires exact dtype, shape,
value, and tensor-byte equality.  Only after that proof passes does it apply
the same mapping to the source adapter.

The current template is the exact rank-32 merge of two rank-16 adapters.  Its
HF LoRA A rank axis has two global rank-16 blocks, while its native shards
preserve four local rows from each block.  A later Miles HF export gathers
those local rows in TP-major order.  The utility therefore classifies the
source's rank-row layout against both template-derived references and refuses
an ambiguous source rather than silently applying the template's ordering.

Legacy four-file output remains fail-closed when independently trained expert
state cannot be represented.  ``--expert-parallel-size 8`` emits the verified
TP4/EP8 rank topology instead and inverts the resulting eight native shards,
requiring exact recovery of every source HF tensor before publishing output.

``--source-native-template`` handles a complete, unmerged Miles checkpoint
whose HF adapter and four legacy TP shards belong to the same training state.
It treats the single LoRA-rank block as TP-major, first requires byte-exact
reconstruction of all four legacy shards, and then applies the same EP-aware
round-trip gate.  This mode is explicit so an arbitrary directory without a
merge manifest can never be accepted by accident.

``--unmerged-native-template`` uses a separately supplied, complete rank-16
HF plus native checkpoint only as a byte-exact architecture/layout witness.
The source must have the identical adapter configuration and tensor schema,
and the emitted TP4/EP8 shards must invert to every source HF tensor byte. The
template's weights are never copied into the source output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


ADAPTER_MODEL = "adapter_model.bin"
ADAPTER_CONFIG = "adapter_config.json"
MERGE_MANIFEST = "merge_manifest.json"
OUTPUT_MANIFEST = "native_reconstruction_manifest.json"
NATIVE_RE = re.compile(r"^adapter_megatron_tp(\d+)_pp0\.pt$")
EP_NATIVE_RE = re.compile(r"^adapter_megatron_tp(\d+)_pp0_ep(\d+)\.pt$")
DECODER_LAYER_RE = re.compile(r"^module\.module\.decoder\.layers\.(\d+)\.")
MTP_PREFIX = "module.module.mtp.layers.0.transformer_layer."
EXPERT_HF_RE = re.compile(
    r"^(?P<prefix>model\.layers\.(?P<layer>\d+)\.mlp\.experts\.)"
    r"(?P<expert>\d+)\."
    r"(?P<factor>gate_proj\.lora_B|up_proj\.lora_B|down_proj\.lora_A)\.weight$"
)
RANK_LAYOUT_MERGE_BLOCKED = "merge-blocked"
RANK_LAYOUT_TP_MAJOR = "tp-major"
MINIMUM_LAYOUT_RMSE_RATIO = 100.0

ATTENTION_PROJECTIONS = {
    "linear_q_down_proj": "q_a_proj",
    "linear_kv_down_proj": "kv_a_proj_with_mqa",
    "linear_proj": "o_proj",
}


class ReconstructionBlockedError(ValueError):
    """Raised when a complete source cannot be represented by the template."""

    def __init__(self, message: str, audit: dict[str, Any]):
        super().__init__(message)
        self.audit = audit


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_torch_state(path: Path) -> Mapping[str, Any]:
    import torch

    state = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
    if not isinstance(state, Mapping):
        raise TypeError(f"{path}: expected a mapping state dictionary")
    if not all(isinstance(key, str) and torch.is_tensor(value) for key, value in state.items()):
        raise TypeError(f"{path}: expected string keys and tensor values")
    return state


def _tensor_bytes(tensor: Any) -> memoryview:
    return memoryview(tensor.detach().contiguous().view(dtype=__import__("torch").uint8).numpy())


def _tensors_byte_exact(lhs: Any, rhs: Any) -> bool:
    import torch

    lhs = lhs.detach().contiguous()
    rhs = rhs.detach().contiguous()
    return (
        lhs.shape == rhs.shape
        and lhs.dtype == rhs.dtype
        and torch.equal(lhs.view(torch.uint8), rhs.view(torch.uint8))
    )


def tensor_content_sha256(state: Mapping[str, Any]) -> str:
    """Hash tensor names, metadata, and raw bytes independently of torch.save."""
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().contiguous()
        metadata = json.dumps(
            {"name": name, "dtype": str(tensor.dtype), "shape": list(tensor.shape)},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(metadata).to_bytes(8, "big"))
        digest.update(metadata)
        digest.update(_tensor_bytes(tensor))
    return digest.hexdigest()


def _native_paths(template_dir: Path) -> list[Path]:
    indexed: dict[int, Path] = {}
    for path in template_dir.glob("adapter_megatron_tp*_pp0.pt"):
        match = NATIVE_RE.fullmatch(path.name)
        if match is None:
            continue
        indexed[int(match.group(1))] = path
    if not indexed:
        raise FileNotFoundError(f"no TP-native shards beneath {template_dir}")
    expected = set(range(len(indexed)))
    if set(indexed) != expected:
        raise ValueError(f"non-contiguous TP shard indices: {sorted(indexed)}")
    return [indexed[index] for index in sorted(indexed)]


def _ep_native_paths(
    template_dir: Path,
    *,
    expert_parallel_size: int,
) -> dict[int, Path]:
    """Return an exact TP4/EP topology keyed by EP rank."""
    indexed: dict[int, Path] = {}
    tp_by_ep: dict[int, int] = {}
    for path in template_dir.glob("adapter_megatron_tp*_pp0_ep*.pt"):
        match = EP_NATIVE_RE.fullmatch(path.name)
        if match is None:
            continue
        tp_rank, ep_rank = (int(value) for value in match.groups())
        if ep_rank in indexed:
            raise ValueError(f"duplicate EP-native shard rank: {ep_rank}")
        indexed[ep_rank] = path
        tp_by_ep[ep_rank] = tp_rank
    expected = set(range(expert_parallel_size))
    if set(indexed) != expected:
        raise FileNotFoundError(
            "source-native EP shards are incomplete: "
            f"expected={sorted(expected)}, actual={sorted(indexed)}"
        )
    expected_topology = {ep_rank: ep_rank % 4 for ep_rank in expected}
    if tp_by_ep != expected_topology:
        raise ValueError(
            "source-native EP shard topology differs: "
            f"expected={expected_topology}, actual={tp_by_ep}"
        )
    return indexed


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: expected a JSON object")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{path.name}-writing-", dir=path.parent) as tmp:
        temporary = Path(tmp) / path.name
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)


def _validate_template_bundle(template_dir: Path, native_paths: list[Path]) -> dict[str, Any]:
    manifest_path = template_dir / MERGE_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"template requires {manifest_path}")
    manifest = _load_json(manifest_path)
    if manifest.get("kind") != "exact-weighted-lora-delta-merge":
        raise ValueError("template merge manifest has the wrong kind")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("template merge manifest has no file receipts")
    required = [template_dir / ADAPTER_MODEL, template_dir / ADAPTER_CONFIG, *native_paths]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"incomplete template adapter: {path}")
    expected_model = files.get(ADAPTER_MODEL, {}).get("output_sha256")
    if not isinstance(expected_model, str):
        raise ValueError("template merge manifest does not bind the HF adapter hash")
    if sha256_path(template_dir / ADAPTER_MODEL) != expected_model:
        raise ValueError("template HF adapter hash does not match merge manifest")
    for path in native_paths:
        expected = files.get(path.name, {}).get("output_sha256")
        if not isinstance(expected, str):
            raise ValueError(f"template merge manifest does not bind {path.name}")
        if sha256_path(path) != expected:
            raise ValueError(f"template native shard hash mismatch: {path.name}")
    expected_config = manifest.get("adapter_config_sha256")
    if not isinstance(expected_config, str):
        raise ValueError("template merge manifest does not bind the adapter config hash")
    if sha256_path(template_dir / ADAPTER_CONFIG) != expected_config:
        raise ValueError("template adapter config hash does not match merge manifest")
    return manifest


def _validate_source_native_template_bundle(
    template_dir: Path,
    native_paths: list[Path],
    *,
    complete_native_paths: list[Path] | None = None,
) -> dict[str, Any]:
    """Bind a complete unmerged HF + TP-native checkpoint without a fake merge."""
    required = [
        template_dir / ADAPTER_MODEL,
        template_dir / ADAPTER_CONFIG,
        *(complete_native_paths or native_paths),
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"incomplete source-native template adapter: {path}")
    if (template_dir / MERGE_MANIFEST).exists():
        raise ValueError(
            f"source-native template mode requires an unmerged checkpoint without {MERGE_MANIFEST}"
        )
    config = _load_json(template_dir / ADAPTER_CONFIG)
    rank = config.get("r")
    if isinstance(rank, bool) or not isinstance(rank, int) or rank <= 0:
        raise ValueError("source-native template adapter has an invalid LoRA rank")
    tp_size = len(native_paths)
    if rank % tp_size:
        raise ValueError(f"source-native LoRA rank {rank} is not divisible by TP={tp_size}")
    return {
        "kind": "complete-source-native-checkpoint",
        "rank": rank,
        "rank_block_size": rank,
        "files": {
            path.name: {
                "sha256": sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for path in required
        },
    }


def _tp_chunk(tensor: Any, *, tp_rank: int, tp_size: int, dim: int) -> Any:
    if tensor.shape[dim] % tp_size:
        raise ValueError(f"cannot divide {tuple(tensor.shape)} axis {dim} over TP={tp_size}")
    return tensor.chunk(tp_size, dim=dim)[tp_rank].contiguous()


def _rank_block_chunk(
    tensor: Any,
    *,
    tp_rank: int,
    tp_size: int,
    rank_block_size: int,
) -> Any:
    """Partition each preserved LoRA-rank block and concatenate local pieces."""
    import torch

    if tensor.ndim < 2 or tensor.shape[0] % rank_block_size:
        raise ValueError(
            f"invalid blocked rank axis {tuple(tensor.shape)} for block size {rank_block_size}"
        )
    if rank_block_size % tp_size:
        raise ValueError(f"rank block {rank_block_size} is not divisible by TP={tp_size}")
    blocks = tensor.split(rank_block_size, dim=0)
    pieces = [_tp_chunk(block, tp_rank=tp_rank, tp_size=tp_size, dim=0) for block in blocks]
    return torch.cat(pieces, dim=0).contiguous()


def _rank_shard(
    tensor: Any,
    *,
    tp_rank: int,
    tp_size: int,
    rank_block_size: int,
    rank_layout: str,
) -> Any:
    if rank_layout == RANK_LAYOUT_MERGE_BLOCKED:
        return _rank_block_chunk(
            tensor,
            tp_rank=tp_rank,
            tp_size=tp_size,
            rank_block_size=rank_block_size,
        )
    if rank_layout == RANK_LAYOUT_TP_MAJOR:
        return _tp_chunk(tensor, tp_rank=tp_rank, tp_size=tp_size, dim=0)
    raise ValueError(f"unsupported source rank layout: {rank_layout}")


def _hf_layer(native_key: str) -> int:
    match = DECODER_LAYER_RE.match(native_key)
    if match is not None:
        return int(match.group(1))
    if native_key.startswith(MTP_PREFIX):
        return 47
    raise KeyError(f"unrecognized native layer key: {native_key}")


def _hf_tensor(hf_state: Mapping[str, Any], name: str) -> Any:
    try:
        return hf_state[name]
    except KeyError as error:
        raise KeyError(f"HF adapter is missing {name}") from error


def rank_sharded_hf_names(native_key: str) -> tuple[str, ...]:
    """Return HF A-factor aliases whose rank rows are sharded by TP."""
    layer = _hf_layer(native_key)
    attention = re.search(
        r"\.self_attention\.(linear_q_down_proj|linear_kv_down_proj)"
        r"\.adapter\.linear_in\.weight$",
        native_key,
    )
    if attention is not None:
        hf_projection = ATTENTION_PROJECTIONS[attention.group(1)]
        return (f"model.layers.{layer}.self_attn.{hf_projection}.lora_A.weight",)
    mlp = re.search(
        r"\.mlp\.(shared_experts\.)?linear_fc1\.adapter\.linear_in\.weight$",
        native_key,
    )
    if mlp is not None:
        shared_prefix = "shared_experts." if mlp.group(1) else ""
        prefix = f"model.layers.{layer}.mlp.{shared_prefix}"
        return (
            f"{prefix}gate_proj.lora_A.weight",
            f"{prefix}up_proj.lora_A.weight",
        )
    return ()


def classify_source_rank_layout(
    source_hf: Mapping[str, Any],
    blocked_reference: Mapping[str, Any],
    tp_major_reference: Mapping[str, Any],
    *,
    minimum_rmse_ratio: float = MINIMUM_LAYOUT_RMSE_RATIO,
) -> tuple[str, dict[str, Any]]:
    """Choose the source rank-row ordering only with a decisive template match."""
    import math

    if set(blocked_reference) != set(tp_major_reference):
        raise ValueError("rank-layout reference key sets differ")
    squared = {RANK_LAYOUT_MERGE_BLOCKED: 0.0, RANK_LAYOUT_TP_MAJOR: 0.0}
    maximum = {RANK_LAYOUT_MERGE_BLOCKED: 0.0, RANK_LAYOUT_TP_MAJOR: 0.0}
    elements = 0
    for name in sorted(blocked_reference):
        source = _hf_tensor(source_hf, name).detach().float()
        blocked = blocked_reference[name].detach().float()
        tp_major = tp_major_reference[name].detach().float()
        if source.shape != blocked.shape or source.shape != tp_major.shape:
            raise ValueError(f"rank-layout reference shape mismatch: {name}")
        for layout, reference in (
            (RANK_LAYOUT_MERGE_BLOCKED, blocked),
            (RANK_LAYOUT_TP_MAJOR, tp_major),
        ):
            difference = (source - reference).double()
            squared[layout] += difference.square().sum().item()
            maximum[layout] = max(maximum[layout], difference.abs().max().item())
        elements += source.numel()
    if not elements:
        raise ValueError("no rank-sharded A tensors were available for layout classification")
    rmse = {layout: math.sqrt(value / elements) for layout, value in squared.items()}
    winner = min(rmse, key=rmse.get)
    loser = (
        RANK_LAYOUT_TP_MAJOR if winner == RANK_LAYOUT_MERGE_BLOCKED else RANK_LAYOUT_MERGE_BLOCKED
    )
    ratio = math.inf if rmse[winner] == 0.0 else rmse[loser] / rmse[winner]
    if ratio < minimum_rmse_ratio:
        raise ValueError(
            "source rank-row layout is ambiguous: "
            f"blocked_rmse={rmse[RANK_LAYOUT_MERGE_BLOCKED]:.9g}, "
            f"tp_major_rmse={rmse[RANK_LAYOUT_TP_MAJOR]:.9g}, ratio={ratio:.3g}"
        )
    evidence = {
        "status": "passed",
        "selected": winner,
        "minimum_required_rmse_ratio": minimum_rmse_ratio,
        "observed_rmse_ratio": ratio,
        "tensor_count": len(blocked_reference),
        "element_count": elements,
        "rmse": rmse,
        "max_abs_difference": maximum,
    }
    return winner, evidence


def audit_expert_coverage(
    hf_state: Mapping[str, Any],
    *,
    represented_expert_count: int,
) -> dict[str, Any]:
    """Prove whether one TP-only shard set can stand in for every EP rank.

    The Miles loader selects a native file by TP rank only.  With EP=2, the
    same four files are therefore reused for the second half of routed
    experts.  That is lossless only when every uncovered upper-half factor is
    exactly equal to its represented lower-half counterpart.
    """
    import math
    import torch

    if represented_expert_count <= 0:
        raise ValueError("represented expert count must be positive")

    parsed: list[tuple[str, re.Match[str]]] = []
    all_expert_indices: set[int] = set()
    for name in hf_state:
        match = EXPERT_HF_RE.fullmatch(name)
        if match is None:
            continue
        parsed.append((name, match))
        all_expert_indices.add(int(match.group("expert")))
    if not parsed:
        raise ValueError("HF adapter has no routed-expert LoRA factors")

    uncovered = [
        (name, match)
        for name, match in parsed
        if int(match.group("expert")) >= represented_expert_count
    ]
    aggregate = {
        "squared_difference": 0.0,
        "squared_source": 0.0,
        "maximum_absolute_difference": 0.0,
        "element_count": 0,
        "tensor_count": 0,
        "exact_duplicate_tensor_count": 0,
        "mismatched_tensor_count": 0,
    }
    per_factor: dict[str, dict[str, Any]] = {}
    uncovered_expert_indices: set[int] = set()
    layers: set[int] = set()

    for name, match in sorted(uncovered, key=lambda item: item[0]):
        expert = int(match.group("expert"))
        counterpart = expert % represented_expert_count
        counterpart_name = f"{match.group('prefix')}{counterpart}.{match.group('factor')}.weight"
        if counterpart_name not in hf_state:
            raise ValueError(f"missing represented expert counterpart: {counterpart_name}")
        upper = hf_state[name].detach()
        lower = hf_state[counterpart_name].detach()
        if upper.shape != lower.shape or upper.dtype != lower.dtype:
            raise ValueError(f"expert counterpart schema mismatch: {name}")

        factor = match.group("factor").replace("_proj.lora_", "_")
        stats = per_factor.setdefault(
            factor,
            {
                "squared_difference": 0.0,
                "squared_source": 0.0,
                "maximum_absolute_difference": 0.0,
                "element_count": 0,
                "tensor_count": 0,
                "exact_duplicate_tensor_count": 0,
                "mismatched_tensor_count": 0,
            },
        )
        is_equal = torch.equal(upper, lower)
        upper_float = upper.float()
        difference = (upper_float - lower.float()).double()
        squared_difference = difference.square().sum().item()
        squared_source = upper_float.double().square().sum().item()
        maximum = difference.abs().max().item() if difference.numel() else 0.0
        for target in (aggregate, stats):
            target["squared_difference"] += squared_difference
            target["squared_source"] += squared_source
            target["maximum_absolute_difference"] = max(
                target["maximum_absolute_difference"], maximum
            )
            target["element_count"] += upper.numel()
            target["tensor_count"] += 1
            count_key = "exact_duplicate_tensor_count" if is_equal else "mismatched_tensor_count"
            target[count_key] += 1
        uncovered_expert_indices.add(expert)
        layers.add(int(match.group("layer")))

    def finalize(stats: dict[str, Any]) -> dict[str, Any]:
        element_count = stats.pop("element_count")
        squared_difference = stats.pop("squared_difference")
        squared_source = stats.pop("squared_source")
        stats["element_count"] = element_count
        stats["difference_rmse"] = (
            math.sqrt(squared_difference / element_count) if element_count else 0.0
        )
        stats["source_rms"] = math.sqrt(squared_source / element_count) if element_count else 0.0
        stats["relative_l2"] = (
            math.sqrt(squared_difference / squared_source) if squared_source else 0.0
        )
        return stats

    # Finalize factor metrics explicitly; the tensors are BF16 in the real
    # adapter, but compute bytes from each tensor so synthetic tests remain
    # truthful for other dtypes.
    for factor_name, stats in per_factor.items():
        stats = finalize(stats)
        stats["tensor_bytes"] = sum(
            hf_state[name].numel() * hf_state[name].element_size()
            for name, match in uncovered
            if match.group("factor").replace("_proj.lora_", "_") == factor_name
        )
        per_factor[factor_name] = stats
    aggregate = finalize(aggregate)
    aggregate["tensor_bytes"] = sum(
        hf_state[name].numel() * hf_state[name].element_size() for name, _ in uncovered
    )

    total_elements = sum(tensor.numel() for tensor in hf_state.values())
    total_bytes = sum(tensor.numel() * tensor.element_size() for tensor in hf_state.values())
    total_tensor_count = len(hf_state)
    source_expert_count = max(all_expert_indices) + 1
    representable = aggregate["mismatched_tensor_count"] == 0
    return {
        "status": "passed" if representable else "blocked",
        "representable_by_tp_only_native_shards": representable,
        "source_expert_count": source_expert_count,
        "represented_expert_count": represented_expert_count,
        "represented_expert_index_start": 0,
        "represented_expert_index_stop": represented_expert_count,
        "uncovered_expert_indices": sorted(uncovered_expert_indices),
        "uncovered_layer_indices": sorted(layers),
        "counterpart_rule": f"expert_index % {represented_expert_count}",
        "uncovered": aggregate,
        "per_factor": dict(sorted(per_factor.items())),
        "structural_fraction": {
            "hf_tensor_count": total_tensor_count,
            "hf_element_count": total_elements,
            "hf_tensor_bytes": total_bytes,
            "uncovered_tensor_count_fraction": (
                aggregate["tensor_count"] / total_tensor_count if total_tensor_count else 0.0
            ),
            "uncovered_element_fraction": (
                aggregate["element_count"] / total_elements if total_elements else 0.0
            ),
            "uncovered_tensor_byte_fraction": (
                aggregate["tensor_bytes"] / total_bytes if total_bytes else 0.0
            ),
        },
    }


def native_tensor_from_hf(
    native_key: str,
    hf_state: Mapping[str, Any],
    *,
    tp_rank: int,
    tp_size: int,
    rank_block_size: int,
    experts_per_shard: int,
    rank_layout: str = RANK_LAYOUT_MERGE_BLOCKED,
    expert_index_start: int | None = None,
) -> Any:
    """Return one Megatron-native tensor using the template-proven GLM layout."""
    import torch

    layer = _hf_layer(native_key)

    attention = re.search(
        r"\.self_attention\.(linear_q_down_proj|linear_kv_down_proj|linear_proj)"
        r"\.adapter\.(linear_in|linear_out)\.weight$",
        native_key,
    )
    if attention is not None:
        native_projection, factor = attention.groups()
        hf_projection = ATTENTION_PROJECTIONS[native_projection]
        hf_factor = "A" if factor == "linear_in" else "B"
        tensor = _hf_tensor(
            hf_state,
            f"model.layers.{layer}.self_attn.{hf_projection}.lora_{hf_factor}.weight",
        )
        if factor == "linear_in" and native_projection != "linear_proj":
            return _rank_shard(
                tensor,
                tp_rank=tp_rank,
                tp_size=tp_size,
                rank_block_size=rank_block_size,
                rank_layout=rank_layout,
            )
        dim = 1 if factor == "linear_in" else 0
        return _tp_chunk(tensor, tp_rank=tp_rank, tp_size=tp_size, dim=dim)

    expert = re.search(
        r"\.mlp\.experts\.(linear_fc1|linear_fc2)"
        r"\.adapter\.(linear_in|linear_out)\.weight$",
        native_key,
    )
    if expert is not None and ".shared_experts." not in native_key:
        projection, factor = expert.groups()
        prefix = f"model.layers.{layer}.mlp.experts"
        if projection == "linear_fc1" and factor == "linear_in":
            gate = _hf_tensor(hf_state, f"{prefix}.gate_proj.lora_A.weight").squeeze(0)
            up = _hf_tensor(hf_state, f"{prefix}.up_proj.lora_A.weight").squeeze(0)
            if not torch.equal(gate, up):
                raise ValueError(f"layer {layer}: expert gate/up shared A factors differ")
            return gate.contiguous()
        if projection == "linear_fc2" and factor == "linear_out":
            return _hf_tensor(hf_state, f"{prefix}.down_proj.lora_B.weight").squeeze(0).contiguous()
        expert_start = (
            tp_rank * experts_per_shard if expert_index_start is None else expert_index_start
        )
        expert_indices = range(expert_start, expert_start + experts_per_shard)
        if projection == "linear_fc1":
            return torch.stack(
                [
                    torch.cat(
                        (
                            _hf_tensor(
                                hf_state,
                                f"{prefix}.{index}.gate_proj.lora_B.weight",
                            ),
                            _hf_tensor(
                                hf_state,
                                f"{prefix}.{index}.up_proj.lora_B.weight",
                            ),
                        ),
                        dim=0,
                    )
                    for index in expert_indices
                ]
            ).contiguous()
        return torch.stack(
            [
                _hf_tensor(
                    hf_state,
                    f"{prefix}.{index}.down_proj.lora_A.weight",
                )
                for index in expert_indices
            ]
        ).contiguous()

    mlp = re.search(
        r"\.mlp\.(shared_experts\.)?(linear_fc1|linear_fc2)"
        r"\.adapter\.(linear_in|linear_out)\.weight$",
        native_key,
    )
    if mlp is not None:
        shared_marker, projection, factor = mlp.groups()
        shared_prefix = "shared_experts." if shared_marker else ""
        prefix = f"model.layers.{layer}.mlp.{shared_prefix}"
        if projection == "linear_fc1" and factor == "linear_in":
            gate = _hf_tensor(hf_state, f"{prefix}gate_proj.lora_A.weight")
            up = _hf_tensor(hf_state, f"{prefix}up_proj.lora_A.weight")
            if not torch.equal(gate, up):
                raise ValueError(f"layer {layer}: fused gate/up A factors differ")
            return _rank_shard(
                gate,
                tp_rank=tp_rank,
                tp_size=tp_size,
                rank_block_size=rank_block_size,
                rank_layout=rank_layout,
            )
        if projection == "linear_fc1":
            gate = _tp_chunk(
                _hf_tensor(hf_state, f"{prefix}gate_proj.lora_B.weight"),
                tp_rank=tp_rank,
                tp_size=tp_size,
                dim=0,
            )
            up = _tp_chunk(
                _hf_tensor(hf_state, f"{prefix}up_proj.lora_B.weight"),
                tp_rank=tp_rank,
                tp_size=tp_size,
                dim=0,
            )
            return torch.cat((gate, up), dim=0).contiguous()
        if factor == "linear_in":
            return _tp_chunk(
                _hf_tensor(hf_state, f"{prefix}down_proj.lora_A.weight"),
                tp_rank=tp_rank,
                tp_size=tp_size,
                dim=1,
            )
        return _tp_chunk(
            _hf_tensor(hf_state, f"{prefix}down_proj.lora_B.weight"),
            tp_rank=tp_rank,
            tp_size=tp_size,
            dim=0,
        )

    raise KeyError(f"unrecognized Megatron adapter tensor: {native_key}")


def reconstruct_native_state(
    hf_state: Mapping[str, Any],
    template_native_state: Mapping[str, Any],
    *,
    tp_rank: int,
    tp_size: int,
    rank_block_size: int,
    experts_per_shard: int,
    rank_layout: str = RANK_LAYOUT_MERGE_BLOCKED,
    expert_index_start: int | None = None,
) -> dict[str, Any]:
    reconstructed: dict[str, Any] = {}
    for name, template_tensor in template_native_state.items():
        tensor = native_tensor_from_hf(
            name,
            hf_state,
            tp_rank=tp_rank,
            tp_size=tp_size,
            rank_block_size=rank_block_size,
            experts_per_shard=experts_per_shard,
            rank_layout=rank_layout,
            expert_index_start=expert_index_start,
        )
        if tensor.shape != template_tensor.shape or tensor.dtype != template_tensor.dtype:
            raise ValueError(
                f"{name}: reconstructed {tuple(tensor.shape)}/{tensor.dtype}, "
                f"template has {tuple(template_tensor.shape)}/{template_tensor.dtype}"
            )
        # Slices can be contiguous while still retaining a much larger backing
        # storage.  Clone every output so torch.save serializes only the native
        # tensor payload, matching the compact Miles checkpoint layout.
        reconstructed[name] = tensor.detach().clone().contiguous()
    return reconstructed


def _state_signature(state: Mapping[str, Any]) -> dict[str, tuple[tuple[int, ...], str]]:
    return {name: (tuple(tensor.shape), str(tensor.dtype)) for name, tensor in state.items()}


def _states_exact(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> tuple[int, int]:
    import torch

    if list(expected) != list(actual):
        raise ValueError("reconstructed native tensor key order differs from template")
    tensor_bytes = 0
    for name in expected:
        lhs = expected[name].detach().contiguous()
        rhs = actual[name].detach().contiguous()
        if lhs.shape != rhs.shape or lhs.dtype != rhs.dtype or not torch.equal(lhs, rhs):
            raise ValueError(f"template reconstruction mismatch: {name}")
        lhs_bytes = lhs.view(torch.uint8)
        rhs_bytes = rhs.view(torch.uint8)
        if not torch.equal(lhs_bytes, rhs_bytes):
            raise ValueError(f"template tensor-byte mismatch: {name}")
        tensor_bytes += lhs.numel() * lhs.element_size()
    return len(expected), tensor_bytes


def _infer_experts_per_shard(native_state: Mapping[str, Any]) -> int:
    for name, tensor in native_state.items():
        if ".mlp.experts.linear_fc1.adapter.linear_out.weight" in name:
            return int(tensor.shape[0])
    raise ValueError("template native state has no packed expert tensor")


def _join_rank_shards(
    pieces: list[Any],
    *,
    tp_size: int,
    rank_block_size: int,
    rank_layout: str,
) -> Any:
    """Invert ``_rank_shard`` without changing dtype or element values."""
    import torch

    if len(pieces) != tp_size:
        raise ValueError(f"expected {tp_size} rank pieces, found {len(pieces)}")
    if rank_layout == RANK_LAYOUT_TP_MAJOR:
        return torch.cat(pieces, dim=0).contiguous()
    if rank_layout != RANK_LAYOUT_MERGE_BLOCKED:
        raise ValueError(f"unsupported source rank layout: {rank_layout}")
    if rank_block_size % tp_size:
        raise ValueError(f"rank block {rank_block_size} is not divisible by TP={tp_size}")
    local_block_size = rank_block_size // tp_size
    if any(piece.shape[0] % local_block_size for piece in pieces):
        raise ValueError("native rank piece does not contain complete merge blocks")
    block_count = pieces[0].shape[0] // local_block_size
    if any(piece.shape[0] // local_block_size != block_count for piece in pieces):
        raise ValueError("native rank pieces disagree on merge-block count")
    return torch.cat(
        [
            torch.cat(
                [piece.narrow(0, block * local_block_size, local_block_size) for piece in pieces],
                dim=0,
            )
            for block in range(block_count)
        ],
        dim=0,
    ).contiguous()


def _is_ep_variable_native_tensor(name: str) -> bool:
    return (
        ".mlp.experts.linear_fc1.adapter.linear_out.weight" in name
        or ".mlp.experts.linear_fc2.adapter.linear_in.weight" in name
    )


def prove_ep_hf_roundtrip(
    hf_state: Mapping[str, Any],
    native_states_by_ep: Mapping[int, Mapping[str, Any]],
    *,
    tp_size: int,
    expert_parallel_size: int,
    experts_per_shard: int,
    rank_block_size: int,
    rank_layout: str,
    native_filenames_by_ep: Mapping[int, str] | None = None,
) -> dict[str, Any]:
    """Invert all EP-aware shards and require exact recovery of every HF tensor."""
    import torch

    expected_ep_ranks = set(range(expert_parallel_size))
    if set(native_states_by_ep) != expected_ep_ranks:
        raise ValueError(
            "EP-native state ranks differ: "
            f"expected={sorted(expected_ep_ranks)}, actual={sorted(native_states_by_ep)}"
        )
    if expert_parallel_size < tp_size or expert_parallel_size % tp_size:
        raise ValueError("expert-parallel rank count must be a multiple of TP size")
    expected_topology = {ep_rank: ep_rank % tp_size for ep_rank in expected_ep_ranks}
    if native_filenames_by_ep is not None:
        if set(native_filenames_by_ep) != expected_ep_ranks:
            raise ValueError("EP-native filenames do not cover every EP rank")
        observed_topology: dict[int, int] = {}
        for ep_rank, filename in native_filenames_by_ep.items():
            match = EP_NATIVE_RE.fullmatch(filename)
            if match is None or int(match.group(2)) != ep_rank:
                raise ValueError(f"invalid EP-native filename for ep={ep_rank}: {filename}")
            observed_topology[ep_rank] = int(match.group(1))
        if observed_topology != expected_topology:
            raise ValueError(
                "EP-native filename topology differs: "
                f"expected={expected_topology}, actual={observed_topology}"
            )

    first_state = native_states_by_ep[0]
    native_names = list(first_state)
    native_signature = _state_signature(first_state)
    for ep_rank, state in native_states_by_ep.items():
        if list(state) != native_names or _state_signature(state) != native_signature:
            raise ValueError(f"EP-native shard schema differs at ep={ep_rank}")

    # Dense, attention, shared-expert, and replicated routed-expert factors
    # depend on TP only.  Prove that EP aliases with the same TP rank agree.
    replicated_comparisons = 0
    for ep_rank, state in native_states_by_ep.items():
        tp_rank = ep_rank % tp_size
        reference = native_states_by_ep[tp_rank]
        if ep_rank == tp_rank:
            continue
        for name in native_names:
            if _is_ep_variable_native_tensor(name):
                continue
            if not torch.equal(state[name], reference[name]) or not _tensors_byte_exact(
                state[name], reference[name]
            ):
                raise ValueError(f"EP alias changed a TP/shared tensor at ep={ep_rank}: {name}")
            replicated_comparisons += 1

    by_tp = [native_states_by_ep[tp_rank] for tp_rank in range(tp_size)]
    covered: set[str] = set()
    recovered_bytes = 0
    recovered_elements = 0

    def verify(name: str, recovered: Any) -> None:
        nonlocal recovered_bytes, recovered_elements
        if name in covered:
            raise ValueError(f"HF tensor reconstructed more than once: {name}")
        expected = _hf_tensor(hf_state, name).detach().contiguous()
        actual = recovered.detach().contiguous()
        if expected.shape != actual.shape or expected.dtype != actual.dtype:
            raise ValueError(f"HF round-trip schema mismatch: {name}")
        if not torch.equal(expected, actual):
            raise ValueError(f"HF round-trip value mismatch: {name}")
        if not torch.equal(expected.view(torch.uint8), actual.view(torch.uint8)):
            raise ValueError(f"HF round-trip tensor-byte mismatch: {name}")
        covered.add(name)
        recovered_elements += expected.numel()
        recovered_bytes += expected.numel() * expected.element_size()

    for native_name in native_names:
        layer = _hf_layer(native_name)
        attention = re.search(
            r"\.self_attention\.(linear_q_down_proj|linear_kv_down_proj|linear_proj)"
            r"\.adapter\.(linear_in|linear_out)\.weight$",
            native_name,
        )
        if attention is not None:
            native_projection, factor = attention.groups()
            hf_projection = ATTENTION_PROJECTIONS[native_projection]
            hf_factor = "A" if factor == "linear_in" else "B"
            pieces = [state[native_name] for state in by_tp]
            if factor == "linear_in" and native_projection != "linear_proj":
                recovered = _join_rank_shards(
                    pieces,
                    tp_size=tp_size,
                    rank_block_size=rank_block_size,
                    rank_layout=rank_layout,
                )
            else:
                dim = 1 if factor == "linear_in" else 0
                recovered = torch.cat(pieces, dim=dim).contiguous()
            verify(
                f"model.layers.{layer}.self_attn.{hf_projection}.lora_{hf_factor}.weight",
                recovered,
            )
            continue

        expert = re.search(
            r"\.mlp\.experts\.(linear_fc1|linear_fc2)"
            r"\.adapter\.(linear_in|linear_out)\.weight$",
            native_name,
        )
        if expert is not None and ".shared_experts." not in native_name:
            projection, factor = expert.groups()
            prefix = f"model.layers.{layer}.mlp.experts"
            if projection == "linear_fc1" and factor == "linear_in":
                for ep_rank, state in native_states_by_ep.items():
                    if not torch.equal(
                        state[native_name], first_state[native_name]
                    ) or not _tensors_byte_exact(state[native_name], first_state[native_name]):
                        raise ValueError(
                            f"replicated expert A factor differs at ep={ep_rank}: {native_name}"
                        )
                recovered = first_state[native_name].unsqueeze(0).contiguous()
                verify(f"{prefix}.gate_proj.lora_A.weight", recovered)
                verify(f"{prefix}.up_proj.lora_A.weight", recovered)
                continue
            if projection == "linear_fc2" and factor == "linear_out":
                for ep_rank, state in native_states_by_ep.items():
                    if not torch.equal(
                        state[native_name], first_state[native_name]
                    ) or not _tensors_byte_exact(state[native_name], first_state[native_name]):
                        raise ValueError(
                            f"replicated expert B factor differs at ep={ep_rank}: {native_name}"
                        )
                verify(
                    f"{prefix}.down_proj.lora_B.weight",
                    first_state[native_name].unsqueeze(0).contiguous(),
                )
                continue
            for ep_rank in range(expert_parallel_size):
                packed = native_states_by_ep[ep_rank][native_name]
                if packed.shape[0] != experts_per_shard:
                    raise ValueError(f"EP shard ep={ep_rank} has wrong expert count: {native_name}")
                for local_expert in range(experts_per_shard):
                    global_expert = ep_rank * experts_per_shard + local_expert
                    tensor = packed[local_expert]
                    if projection == "linear_fc1":
                        if tensor.shape[0] % 2:
                            raise ValueError(f"fused expert fc1 rows are odd: {native_name}")
                        gate, up = tensor.chunk(2, dim=0)
                        verify(f"{prefix}.{global_expert}.gate_proj.lora_B.weight", gate)
                        verify(f"{prefix}.{global_expert}.up_proj.lora_B.weight", up)
                    else:
                        verify(f"{prefix}.{global_expert}.down_proj.lora_A.weight", tensor)
            continue

        mlp = re.search(
            r"\.mlp\.(shared_experts\.)?(linear_fc1|linear_fc2)"
            r"\.adapter\.(linear_in|linear_out)\.weight$",
            native_name,
        )
        if mlp is not None:
            shared_marker, projection, factor = mlp.groups()
            shared_prefix = "shared_experts." if shared_marker else ""
            prefix = f"model.layers.{layer}.mlp.{shared_prefix}"
            pieces = [state[native_name] for state in by_tp]
            if projection == "linear_fc1" and factor == "linear_in":
                recovered = _join_rank_shards(
                    pieces,
                    tp_size=tp_size,
                    rank_block_size=rank_block_size,
                    rank_layout=rank_layout,
                )
                verify(f"{prefix}gate_proj.lora_A.weight", recovered)
                verify(f"{prefix}up_proj.lora_A.weight", recovered)
            elif projection == "linear_fc1":
                gate_pieces: list[Any] = []
                up_pieces: list[Any] = []
                for piece in pieces:
                    if piece.shape[0] % 2:
                        raise ValueError(f"fused fc1 rows are odd: {native_name}")
                    gate, up = piece.chunk(2, dim=0)
                    gate_pieces.append(gate)
                    up_pieces.append(up)
                verify(
                    f"{prefix}gate_proj.lora_B.weight",
                    torch.cat(gate_pieces, dim=0).contiguous(),
                )
                verify(
                    f"{prefix}up_proj.lora_B.weight",
                    torch.cat(up_pieces, dim=0).contiguous(),
                )
            elif factor == "linear_in":
                verify(
                    f"{prefix}down_proj.lora_A.weight",
                    torch.cat(pieces, dim=1).contiguous(),
                )
            else:
                verify(
                    f"{prefix}down_proj.lora_B.weight",
                    torch.cat(pieces, dim=0).contiguous(),
                )
            continue

        raise KeyError(f"unrecognized Megatron adapter tensor during round-trip: {native_name}")

    missing = sorted(set(hf_state) - covered)
    unexpected = sorted(covered - set(hf_state))
    if missing or unexpected:
        raise ValueError(
            "EP-native round-trip did not cover the complete HF state: "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}, "
            f"covered={len(covered)}/{len(hf_state)}"
        )
    return {
        "status": "passed",
        "source_hf_tensor_count": len(hf_state),
        "recovered_hf_tensor_count": len(covered),
        "source_hf_element_count": sum(tensor.numel() for tensor in hf_state.values()),
        "recovered_hf_element_count": recovered_elements,
        "source_hf_tensor_bytes": sum(
            tensor.numel() * tensor.element_size() for tensor in hf_state.values()
        ),
        "recovered_hf_tensor_bytes": recovered_bytes,
        "coverage_fraction": len(covered) / len(hf_state),
        "all_source_hf_tensors_value_exact": True,
        "all_source_hf_tensor_bytes_exact": True,
        "native_shard_count": expert_parallel_size,
        "native_tensor_instances": expert_parallel_size * len(native_names),
        "tp_shared_alias_comparisons": replicated_comparisons,
        "native_filename_topology_exact": native_filenames_by_ep is not None,
    }


def reconstruct_adapter(
    source_dir: Path,
    template_dir: Path,
    output_dir: Path,
    *,
    expected_source_sha256: str | None = None,
    audit_report_path: Path | None = None,
    expert_parallel_size: int | None = None,
    source_native_template: bool = False,
    unmerged_native_template: bool = False,
) -> dict[str, Any]:
    """Prove the template mapping, then atomically emit a complete adapter."""
    import torch

    source_dir = source_dir.resolve()
    template_dir = template_dir.resolve()
    output_dir = output_dir.resolve()
    if audit_report_path is not None:
        audit_report_path = audit_report_path.resolve()
    if output_dir in {source_dir, template_dir}:
        raise ValueError("output adapter directory must differ from all input directories")
    if source_native_template and unmerged_native_template:
        raise ValueError(
            "source-native and unmerged-native template modes are mutually exclusive"
        )
    if source_native_template:
        if source_dir != template_dir:
            raise ValueError(
                "source-native template mode requires source and template to be the same directory"
            )
    elif source_dir == template_dir:
        raise ValueError("source and template adapter directories must differ")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to replace nonempty destination: {output_dir}")
    for name in (ADAPTER_MODEL, ADAPTER_CONFIG):
        if not (source_dir / name).is_file():
            raise FileNotFoundError(f"incomplete source adapter: {source_dir / name}")

    source_sha256 = sha256_path(source_dir / ADAPTER_MODEL)
    if expected_source_sha256 and source_sha256 != expected_source_sha256.lower():
        raise ValueError(
            f"source adapter SHA-256 mismatch: {source_sha256} != {expected_source_sha256.lower()}"
        )

    source_ep_native_paths: dict[int, Path] = {}
    try:
        native_paths = _native_paths(template_dir)
    except FileNotFoundError:
        if (
            not (source_native_template or unmerged_native_template)
            or expert_parallel_size is None
        ):
            raise
        source_ep_native_paths = _ep_native_paths(
            template_dir,
            expert_parallel_size=expert_parallel_size,
        )
        native_paths = [source_ep_native_paths[tp_rank] for tp_rank in range(4)]
    tp_size = len(native_paths)
    template_config = _load_json(template_dir / ADAPTER_CONFIG)
    source_native_bundle: dict[str, Any] | None = None
    merge_manifest: dict[str, Any] | None = None
    if source_native_template or unmerged_native_template:
        source_native_bundle = _validate_source_native_template_bundle(
            template_dir,
            native_paths,
            complete_native_paths=(
                [source_ep_native_paths[index] for index in sorted(source_ep_native_paths)]
                if source_ep_native_paths
                else None
            ),
        )
        output_rank = int(source_native_bundle["rank"])
        rank_block_size = int(source_native_bundle["rank_block_size"])
    else:
        merge_manifest = _validate_template_bundle(template_dir, native_paths)
        output_rank = int(merge_manifest["output_rank"])
        rank_block_size = int(merge_manifest["input_rank"])
    if output_rank % rank_block_size:
        raise ValueError("template output rank is not composed of complete input-rank blocks")
    source_config = _load_json(source_dir / ADAPTER_CONFIG)
    if source_config != template_config:
        differing = sorted(
            key
            for key in set(source_config) | set(template_config)
            if source_config.get(key) != template_config.get(key)
        )
        raise ValueError(f"source/template adapter configs differ: {differing}")
    if int(source_config.get("r", -1)) != output_rank:
        raise ValueError("source rank does not match template merge output rank")

    # Mandatory gate: reconstruct every known native tensor from the template
    # HF state before inspecting or writing any source-derived output.
    template_hf = _load_torch_state(template_dir / ADAPTER_MODEL)
    template_signature = _state_signature(template_hf)
    proof_shards: dict[str, Any] = {}
    rank_layout_pieces: dict[str, list[Any | None]] = {}
    experts_per_shard: int | None = None
    for tp_rank, native_path in enumerate(native_paths):
        template_native = _load_torch_state(native_path)
        inferred = _infer_experts_per_shard(template_native)
        if experts_per_shard is None:
            experts_per_shard = inferred
        elif experts_per_shard != inferred:
            raise ValueError("template native shards disagree on experts per shard")
        reconstructed = reconstruct_native_state(
            template_hf,
            template_native,
            tp_rank=tp_rank,
            tp_size=tp_size,
            rank_block_size=rank_block_size,
            experts_per_shard=experts_per_shard,
            rank_layout=(
                RANK_LAYOUT_TP_MAJOR
                if source_native_template or unmerged_native_template
                else RANK_LAYOUT_MERGE_BLOCKED
            ),
        )
        tensor_count, tensor_bytes = _states_exact(template_native, reconstructed)
        expected_digest = tensor_content_sha256(template_native)
        actual_digest = tensor_content_sha256(reconstructed)
        if expected_digest != actual_digest:
            raise ValueError(f"template canonical digest mismatch: {native_path.name}")
        for native_name, native_tensor in template_native.items():
            aliases = rank_sharded_hf_names(native_name)
            if not aliases:
                continue
            piece = native_tensor.detach().clone().contiguous()
            for hf_name in aliases:
                pieces = rank_layout_pieces.setdefault(hf_name, [None] * tp_size)
                if pieces[tp_rank] is not None:
                    if not torch.equal(pieces[tp_rank], piece):
                        raise ValueError(f"conflicting native rank-layout piece: {hf_name}")
                    continue
                pieces[tp_rank] = piece
        proof_shards[native_path.name] = {
            "template_file_sha256": sha256_path(native_path),
            "tensor_content_sha256": expected_digest,
            "tensor_count": tensor_count,
            "tensor_bytes": tensor_bytes,
            "value_exact": True,
            "tensor_bytes_exact": True,
        }
    assert experts_per_shard is not None
    source_ep_template_proof: dict[str, Any] | None = None
    if source_ep_native_paths:
        source_ep_states: dict[int, Mapping[str, Any]] = {}
        source_ep_shards: dict[str, Any] = {}
        for ep_rank, native_path in sorted(source_ep_native_paths.items()):
            template_native = _load_torch_state(native_path)
            inferred = _infer_experts_per_shard(template_native)
            if inferred != experts_per_shard:
                raise ValueError(
                    f"source-native EP shard expert count differs at ep={ep_rank}"
                )
            reconstructed = reconstruct_native_state(
                template_hf,
                template_native,
                tp_rank=ep_rank % tp_size,
                tp_size=tp_size,
                rank_block_size=rank_block_size,
                experts_per_shard=experts_per_shard,
                rank_layout=RANK_LAYOUT_TP_MAJOR,
                expert_index_start=ep_rank * experts_per_shard,
            )
            tensor_count, tensor_bytes = _states_exact(template_native, reconstructed)
            expected_digest = tensor_content_sha256(template_native)
            actual_digest = tensor_content_sha256(reconstructed)
            if expected_digest != actual_digest:
                raise ValueError(
                    f"source-native EP canonical digest mismatch: {native_path.name}"
                )
            source_ep_states[ep_rank] = template_native
            source_ep_shards[native_path.name] = {
                "template_file_sha256": sha256_path(native_path),
                "tensor_content_sha256": expected_digest,
                "tensor_count": tensor_count,
                "tensor_bytes": tensor_bytes,
                "value_exact": True,
                "tensor_bytes_exact": True,
            }
        source_ep_template_proof = {
            "status": "passed",
            "all_source_ep_native_tensors_value_exact": True,
            "all_source_ep_native_tensor_bytes_exact": True,
            "shards": source_ep_shards,
            "source_hf_roundtrip": prove_ep_hf_roundtrip(
                template_hf,
                source_ep_states,
                tp_size=tp_size,
                expert_parallel_size=expert_parallel_size,
                experts_per_shard=experts_per_shard,
                rank_block_size=rank_block_size,
                rank_layout=RANK_LAYOUT_TP_MAJOR,
                native_filenames_by_ep={
                    ep_rank: path.name
                    for ep_rank, path in sorted(source_ep_native_paths.items())
                },
            ),
        }
    represented_expert_count = tp_size * experts_per_shard
    template_expert_coverage = audit_expert_coverage(
        template_hf,
        represented_expert_count=represented_expert_count,
    )

    blocked_reference: dict[str, Any] = {}
    tp_major_reference: dict[str, Any] = {}
    for name, pieces in sorted(rank_layout_pieces.items()):
        if any(piece is None for piece in pieces):
            raise ValueError(f"incomplete native rank-layout reference: {name}")
        blocked = _hf_tensor(template_hf, name)
        tp_major = torch.cat([piece for piece in pieces if piece is not None], dim=0)
        if blocked.shape != tp_major.shape or blocked.dtype != tp_major.dtype:
            raise ValueError(f"native rank-layout reference schema mismatch: {name}")
        blocked_reference[name] = blocked
        tp_major_reference[name] = tp_major

    source_hf = (
        template_hf if source_native_template else _load_torch_state(source_dir / ADAPTER_MODEL)
    )
    if _state_signature(source_hf) != template_signature:
        missing = sorted(set(template_signature) - set(source_hf))[:5]
        unexpected = sorted(set(source_hf) - set(template_signature))[:5]
        changed = sorted(
            name
            for name in set(source_hf) & set(template_signature)
            if _state_signature({name: source_hf[name]})[name] != template_signature[name]
        )[:5]
        raise ValueError(
            "source HF tensor schema differs from template: "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )

    if source_native_template:
        if output_rank != rank_block_size:
            raise ValueError("source-native template must contain exactly one LoRA-rank block")
        element_count = 0
        for name in sorted(blocked_reference):
            blocked = blocked_reference[name]
            tp_major = tp_major_reference[name]
            source = _hf_tensor(source_hf, name)
            if not _tensors_byte_exact(blocked, tp_major) or not _tensors_byte_exact(
                source, tp_major
            ):
                raise ValueError(f"source-native single-block rank layout mismatch: {name}")
            element_count += source.numel()
        source_rank_layout = RANK_LAYOUT_TP_MAJOR
        rank_layout_evidence = {
            "status": "passed",
            "selected": source_rank_layout,
            "selection_basis": "single-rank-block-byte-exact-native-proof",
            "rank_layouts_equivalent": True,
            "tensor_count": len(blocked_reference),
            "element_count": element_count,
            "all_reference_tensor_bytes_exact": True,
        }
    elif unmerged_native_template:
        source_rank_layout = RANK_LAYOUT_TP_MAJOR
        rank_layout_evidence = {
            "status": "passed",
            "selected": source_rank_layout,
            "selection_basis": (
                "separate-unmerged-template-byte-exact-proof-plus-source-hf-roundtrip"
            ),
            "rank_layouts_equivalent": True,
            "tensor_count": len(tp_major_reference),
            "element_count": sum(
                _hf_tensor(source_hf, name).numel() for name in tp_major_reference
            ),
            "all_reference_tensor_bytes_exact": True,
        }
    else:
        source_rank_layout, rank_layout_evidence = classify_source_rank_layout(
            source_hf,
            blocked_reference,
            tp_major_reference,
        )
    source_expert_coverage = audit_expert_coverage(
        source_hf,
        represented_expert_count=represented_expert_count,
    )
    if expert_parallel_size is not None:
        if (tp_size, expert_parallel_size) != (4, 8):
            raise ValueError(
                "EP-aware reconstruction is pinned to the verified TP=4, EP=8 topology"
            )
        expected_expert_count = expert_parallel_size * experts_per_shard
        if source_expert_coverage["source_expert_count"] != expected_expert_count:
            raise ValueError(
                "source expert count does not match EP-aware topology: "
                f"{source_expert_coverage['source_expert_count']} != "
                f"{expert_parallel_size} * {experts_per_shard}"
            )
    topology = (
        [
            {
                "global_rank": ep_rank,
                "tp_rank": ep_rank % tp_size,
                "ep_rank": ep_rank,
                "expert_index_start": ep_rank * experts_per_shard,
                "expert_index_stop": (ep_rank + 1) * experts_per_shard,
                "filename": (f"adapter_megatron_tp{ep_rank % tp_size}_pp0_ep{ep_rank}.pt"),
            }
            for ep_rank in range(expert_parallel_size)
        ]
        if expert_parallel_size is not None
        else [
            {
                "tp_rank": tp_rank,
                "expert_index_start": tp_rank * experts_per_shard,
                "expert_index_stop": (tp_rank + 1) * experts_per_shard,
                "filename": native_path.name,
            }
            for tp_rank, native_path in enumerate(native_paths)
        ]
    )
    template_receipt = {
        "path": str(template_dir),
        "adapter_model_sha256": sha256_path(template_dir / ADAPTER_MODEL),
        "adapter_config_sha256": sha256_path(template_dir / ADAPTER_CONFIG),
        "bundle_kind": (
            source_native_bundle["kind"]
            if source_native_bundle is not None
            else "exact-weighted-lora-delta-merge"
        ),
        "expert_coverage": template_expert_coverage,
        "proof": {
            "status": "passed",
            "all_template_native_tensors_value_exact": True,
            "all_template_native_tensor_bytes_exact": True,
            "shards": proof_shards,
        },
    }
    if source_native_bundle is not None:
        template_receipt["source_native_bundle"] = source_native_bundle
        if source_ep_template_proof is not None:
            template_receipt["source_ep_native_proof"] = source_ep_template_proof
    else:
        assert merge_manifest is not None
        template_receipt["merge_manifest_sha256"] = sha256_path(template_dir / MERGE_MANIFEST)
    source_receipt = {
        "path": str(source_dir),
        "adapter_model_sha256": source_sha256,
        "adapter_config_sha256": sha256_path(source_dir / ADAPTER_CONFIG),
        "tensor_content_sha256": tensor_content_sha256(source_hf),
        "tensor_count": len(source_hf),
    }
    mapping_receipt = {
        "mode": ("expert-parallel-aware" if expert_parallel_size is not None else "legacy-tp-only"),
        "tp_size": tp_size,
        "expert_parallel_size": expert_parallel_size,
        "rank": output_rank,
        "template_rank_block_size": rank_block_size,
        "template_rank_block_count": output_rank // rank_block_size,
        "source_rank_layout": rank_layout_evidence,
        "experts_per_shard": experts_per_shard,
        "represented_expert_index_start": 0,
        "represented_expert_index_stop": (
            expert_parallel_size * experts_per_shard
            if expert_parallel_size is not None
            else represented_expert_count
        ),
        "legacy_tp_only_expert_coverage": source_expert_coverage,
        "rank_topology": topology,
        "decoder_hf_layers": [0, 46],
        "mtp_hf_layer": 47,
    }
    if (
        expert_parallel_size is None
        and not source_expert_coverage["representable_by_tp_only_native_shards"]
    ):
        uncovered = source_expert_coverage["uncovered"]
        blocked_manifest = {
            "schema_version": 1,
            "kind": "glm47-hf-to-megatron-tp-native-reconstruction-audit",
            "status": "blocked",
            "reason": {
                "code": "unrepresented-expert-state",
                "message": (
                    "the TP-only native template is reused across expert-parallel ranks, "
                    "but uncovered source expert factors differ from their represented aliases"
                ),
            },
            "source": source_receipt,
            "template": template_receipt,
            "mapping": mapping_receipt,
            "outputs": {
                "native_shards_generated": False,
                "output_path": str(output_dir),
            },
        }
        if audit_report_path is not None:
            _write_json_atomic(audit_report_path, blocked_manifest)
        raise ReconstructionBlockedError(
            "source cannot be represented by TP-only native template: "
            f"{uncovered['mismatched_tensor_count']} of "
            f"{uncovered['tensor_count']} uncovered expert tensors differ",
            blocked_manifest,
        )

    del template_hf, blocked_reference, tp_major_reference, rank_layout_pieces
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=f".{output_dir.name}-reconstructing-", dir=output_dir.parent
    ) as tmp:
        staging = Path(tmp)
        shutil.copy2(source_dir / ADAPTER_MODEL, staging / ADAPTER_MODEL)
        shutil.copy2(source_dir / ADAPTER_CONFIG, staging / ADAPTER_CONFIG)
        output_shards: dict[str, Any] = {}
        output_state_paths_by_ep: dict[int, Path] = {}
        output_specs = (
            [
                (
                    ep_rank % tp_size,
                    ep_rank,
                    native_paths[ep_rank % tp_size],
                    f"adapter_megatron_tp{ep_rank % tp_size}_pp0_ep{ep_rank}.pt",
                )
                for ep_rank in range(expert_parallel_size)
            ]
            if expert_parallel_size is not None
            else [
                (tp_rank, None, native_path, native_path.name)
                for tp_rank, native_path in enumerate(native_paths)
            ]
        )
        for tp_rank, ep_rank, native_path, destination_name in output_specs:
            template_native = _load_torch_state(native_path)
            reconstructed = reconstruct_native_state(
                source_hf,
                template_native,
                tp_rank=tp_rank,
                tp_size=tp_size,
                rank_block_size=rank_block_size,
                experts_per_shard=experts_per_shard,
                rank_layout=source_rank_layout,
                expert_index_start=(ep_rank * experts_per_shard if ep_rank is not None else None),
            )
            destination = staging / destination_name
            torch.save(reconstructed, destination)
            output_shards[destination_name] = {
                "sha256": sha256_path(destination),
                "size_bytes": destination.stat().st_size,
                "tensor_content_sha256": tensor_content_sha256(reconstructed),
                "tensor_count": len(reconstructed),
                "tp_rank": tp_rank,
                "ep_rank": ep_rank,
                "expert_index_start": (
                    ep_rank * experts_per_shard if ep_rank is not None else None
                ),
                "expert_index_stop": (
                    (ep_rank + 1) * experts_per_shard if ep_rank is not None else None
                ),
            }
            if ep_rank is not None:
                output_state_paths_by_ep[ep_rank] = destination
            del reconstructed

        if expert_parallel_size is not None:
            output_states_by_ep = {
                ep_rank: _load_torch_state(path)
                for ep_rank, path in output_state_paths_by_ep.items()
            }
            roundtrip = prove_ep_hf_roundtrip(
                source_hf,
                output_states_by_ep,
                tp_size=tp_size,
                expert_parallel_size=expert_parallel_size,
                experts_per_shard=experts_per_shard,
                rank_block_size=rank_block_size,
                rank_layout=source_rank_layout,
                native_filenames_by_ep={
                    ep_rank: path.name for ep_rank, path in output_state_paths_by_ep.items()
                },
            )
            roundtrip["source_tensor_content_sha256"] = source_receipt["tensor_content_sha256"]
            mapping_receipt["source_hf_roundtrip"] = roundtrip
            del output_states_by_ep

        manifest = {
            "schema_version": 1,
            "kind": "glm47-hf-to-megatron-tp-native-reconstruction",
            "status": "passed",
            "source": source_receipt,
            "template": template_receipt,
            "mapping": mapping_receipt,
            "outputs": {
                ADAPTER_MODEL: {
                    "sha256": source_sha256,
                    "size_bytes": (staging / ADAPTER_MODEL).stat().st_size,
                },
                ADAPTER_CONFIG: {
                    "sha256": sha256_path(staging / ADAPTER_CONFIG),
                    "size_bytes": (staging / ADAPTER_CONFIG).stat().st_size,
                },
                "native_shards": output_shards,
            },
        }
        (staging / OUTPUT_MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if output_dir.exists():
            output_dir.rmdir()
        os.replace(staging, output_dir)
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="HF adapter to reconstruct")
    parser.add_argument("template", help="complete HF + TP-native template adapter")
    parser.add_argument("output", help="new complete adapter directory")
    parser.add_argument("--expected-source-sha256")
    parser.add_argument(
        "--source-native-template",
        action="store_true",
        help=(
            "use the source checkpoint's own complete legacy TP shards as the "
            "byte-exact mapping template (source and template paths must match)"
        ),
    )
    parser.add_argument(
        "--unmerged-native-template",
        action="store_true",
        help=(
            "use a distinct complete rank-16 HF plus native checkpoint as a "
            "byte-exact layout witness; source HF round-trip remains mandatory"
        ),
    )
    parser.add_argument(
        "--expert-parallel-size",
        type=int,
        help=("emit lossless TP4/EP8 shards named adapter_megatron_tp{tp}_pp0_ep{ep}.pt"),
    )
    parser.add_argument(
        "--audit-report",
        type=Path,
        help="atomically write a JSON audit even when reconstruction is blocked",
    )
    args = parser.parse_args(argv)
    output = Path(args.output).resolve()
    try:
        manifest = reconstruct_adapter(
            Path(args.source),
            Path(args.template),
            output,
            expected_source_sha256=args.expected_source_sha256,
            audit_report_path=args.audit_report,
            expert_parallel_size=args.expert_parallel_size,
            source_native_template=args.source_native_template,
            unmerged_native_template=args.unmerged_native_template,
        )
    except ReconstructionBlockedError as error:
        print(json.dumps(error.audit, indent=2, sort_keys=True))
        parser.exit(2, f"MEGATRON_NATIVE_ADAPTER_BLOCKED: {error}\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    print("MEGATRON_NATIVE_ADAPTER_READY", output)


if __name__ == "__main__":
    main()
