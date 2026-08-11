from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest


torch = pytest.importorskip("torch")
module = runpy.run_path("scripts/reconstruct_megatron_lora.py")
native_tensor_from_hf = module["native_tensor_from_hf"]
reconstruct_adapter = module["reconstruct_adapter"]
reconstruct_native_state = module["reconstruct_native_state"]
sha256_path = module["sha256_path"]
ReconstructionBlockedError = module["ReconstructionBlockedError"]
RANK_LAYOUT_TP_MAJOR = module["RANK_LAYOUT_TP_MAJOR"]


def _values(shape: tuple[int, ...], offset: int = 0):
    count = 1
    for size in shape:
        count *= size
    return torch.arange(offset, offset + count, dtype=torch.float32).reshape(shape)


def test_rank_block_and_fused_dense_mapping() -> None:
    rank_a = _values((8, 3))
    gate_b = _values((4, 8), 100)
    up_b = _values((4, 8), 200)
    hf = {
        "model.layers.0.mlp.gate_proj.lora_A.weight": rank_a,
        "model.layers.0.mlp.up_proj.lora_A.weight": rank_a.clone(),
        "model.layers.0.mlp.gate_proj.lora_B.weight": gate_b,
        "model.layers.0.mlp.up_proj.lora_B.weight": up_b,
    }

    native_a = native_tensor_from_hf(
        "module.module.decoder.layers.0.mlp.linear_fc1.adapter.linear_in.weight",
        hf,
        tp_rank=1,
        tp_size=2,
        rank_block_size=4,
        experts_per_shard=1,
    )
    native_b = native_tensor_from_hf(
        "module.module.decoder.layers.0.mlp.linear_fc1.adapter.linear_out.weight",
        hf,
        tp_rank=1,
        tp_size=2,
        rank_block_size=4,
        experts_per_shard=1,
    )

    assert torch.equal(native_a, torch.cat((rank_a[2:4], rank_a[6:8]), dim=0))
    assert torch.equal(native_b, torch.cat((gate_b[2:4], up_b[2:4]), dim=0))

    tp_major_a = native_tensor_from_hf(
        "module.module.decoder.layers.0.mlp.linear_fc1.adapter.linear_in.weight",
        hf,
        tp_rank=1,
        tp_size=2,
        rank_block_size=4,
        experts_per_shard=1,
        rank_layout=RANK_LAYOUT_TP_MAJOR,
    )
    assert torch.equal(tp_major_a, rank_a[4:8])


def test_mtp_and_packed_expert_mapping() -> None:
    shared_a = _values((1, 8, 3))
    shared_down_b = _values((1, 4, 8), 50)
    hf = {
        "model.layers.47.mlp.experts.gate_proj.lora_A.weight": shared_a,
        "model.layers.47.mlp.experts.up_proj.lora_A.weight": shared_a.clone(),
        "model.layers.47.mlp.experts.down_proj.lora_B.weight": shared_down_b,
    }
    for expert in range(4):
        hf[f"model.layers.47.mlp.experts.{expert}.gate_proj.lora_B.weight"] = _values(
            (2, 8), 100 * expert
        )
        hf[f"model.layers.47.mlp.experts.{expert}.up_proj.lora_B.weight"] = _values(
            (2, 8), 100 * expert + 20
        )
        hf[f"model.layers.47.mlp.experts.{expert}.down_proj.lora_A.weight"] = _values(
            (8, 2), 100 * expert + 40
        )

    prefix = "module.module.mtp.layers.0.transformer_layer.mlp.experts"
    native_fc1 = native_tensor_from_hf(
        f"{prefix}.linear_fc1.adapter.linear_out.weight",
        hf,
        tp_rank=1,
        tp_size=2,
        rank_block_size=4,
        experts_per_shard=2,
    )
    native_fc2 = native_tensor_from_hf(
        f"{prefix}.linear_fc2.adapter.linear_in.weight",
        hf,
        tp_rank=1,
        tp_size=2,
        rank_block_size=4,
        experts_per_shard=2,
    )

    assert torch.equal(
        native_fc1[0],
        torch.cat(
            (
                hf["model.layers.47.mlp.experts.2.gate_proj.lora_B.weight"],
                hf["model.layers.47.mlp.experts.2.up_proj.lora_B.weight"],
            ),
            dim=0,
        ),
    )
    assert torch.equal(native_fc2[1], hf["model.layers.47.mlp.experts.3.down_proj.lora_A.weight"])


def _write_adapter(path: Path, state: dict[str, object], rank: int = 8) -> None:
    path.mkdir(parents=True)
    torch.save(state, path / "adapter_model.bin")
    config = {
        "bias": "none",
        "lora_alpha": rank,
        "lora_dropout": 0.0,
        "peft_type": "LORA",
        "r": rank,
        "target_modules": ["q_a_proj"],
        "task_type": "CAUSAL_LM",
    }
    (path / "adapter_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _synthetic_bundle(
    tmp_path: Path,
    *,
    mismatched_surplus_expert: bool = False,
    tp_size: int = 2,
    source_expert_parallel_size: int | None = None,
) -> tuple[Path, Path]:
    template = tmp_path / "template"
    source = tmp_path / "source"
    rank_a = _values((8, 3))
    shared_a = _values((1, 8, 3), 100)
    template_hf = {
        "model.layers.0.self_attn.q_a_proj.lora_A.weight": rank_a,
        "model.layers.1.mlp.experts.gate_proj.lora_A.weight": shared_a,
        "model.layers.1.mlp.experts.up_proj.lora_A.weight": shared_a.clone(),
    }
    source_hf = {name: tensor + 1000 for name, tensor in template_hf.items()}
    # A normal Miles save gathers TP-local rank rows in TP-major order.  The
    # template HF file instead preserves its two merged rank-4 blocks.
    local_block_size = 4 // tp_size
    source_hf["model.layers.0.self_attn.q_a_proj.lora_A.weight"] = (
        torch.cat(
            [
                torch.cat(
                    [
                        rank_a.narrow(0, block * 4 + tp_rank * local_block_size, local_block_size)
                        for block in range(2)
                    ],
                    dim=0,
                )
                for tp_rank in range(tp_size)
            ],
            dim=0,
        )
        + 0.01
    )
    source_hf["model.layers.1.mlp.experts.up_proj.lora_A.weight"] = source_hf[
        "model.layers.1.mlp.experts.gate_proj.lora_A.weight"
    ].clone()
    expert_count = (
        source_expert_parallel_size
        if source_expert_parallel_size is not None
        else tp_size * 2
        if mismatched_surplus_expert
        else tp_size
    )
    for expert in range(expert_count):
        counterpart = expert % tp_size
        template_hf[f"model.layers.1.mlp.experts.{expert}.gate_proj.lora_B.weight"] = _values(
            (2, 8), counterpart * 100
        )
        template_hf[f"model.layers.1.mlp.experts.{expert}.up_proj.lora_B.weight"] = _values(
            (2, 8), counterpart * 100 + 20
        )
        template_hf[f"model.layers.1.mlp.experts.{expert}.down_proj.lora_A.weight"] = _values(
            (8, 2), counterpart * 100 + 40
        )
        for factor in ("gate_proj.lora_B", "up_proj.lora_B", "down_proj.lora_A"):
            name = f"model.layers.1.mlp.experts.{expert}.{factor}.weight"
            lower_name = f"model.layers.1.mlp.experts.{counterpart}.{factor}.weight"
            if expert < tp_size:
                source_hf[name] = template_hf[name] + 1000
            else:
                source_hf[name] = source_hf[lower_name].clone()
    if mismatched_surplus_expert:
        source_hf[f"model.layers.1.mlp.experts.{tp_size}.gate_proj.lora_B.weight"] += 1
    if source_expert_parallel_size is not None:
        for expert in range(tp_size, expert_count):
            for factor_index, factor in enumerate(
                ("gate_proj.lora_B", "up_proj.lora_B", "down_proj.lora_A")
            ):
                name = f"model.layers.1.mlp.experts.{expert}.{factor}.weight"
                source_hf[name] += expert * 10 + factor_index + 1
    _write_adapter(template, template_hf)
    _write_adapter(source, source_hf)

    native_names = [
        "module.module.decoder.layers.0.self_attention.linear_q_down_proj.adapter.linear_in.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc1.adapter.linear_in.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc1.adapter.linear_out.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc2.adapter.linear_in.weight",
    ]
    receipts = {"adapter_model.bin": {"output_sha256": sha256_path(template / "adapter_model.bin")}}
    for tp_rank in range(tp_size):
        native = {
            name: native_tensor_from_hf(
                name,
                template_hf,
                tp_rank=tp_rank,
                tp_size=tp_size,
                rank_block_size=4,
                experts_per_shard=1,
            )
            for name in native_names
        }
        native_path = template / f"adapter_megatron_tp{tp_rank}_pp0.pt"
        torch.save(native, native_path)
        receipts[native_path.name] = {"output_sha256": sha256_path(native_path)}
    merge_manifest = {
        "kind": "exact-weighted-lora-delta-merge",
        "input_rank": 4,
        "output_rank": 8,
        "adapter_config_sha256": sha256_path(template / "adapter_config.json"),
        "files": receipts,
    }
    (template / "merge_manifest.json").write_text(
        json.dumps(merge_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return source, template


def _synthetic_rank16_source_native_bundle(tmp_path: Path) -> Path:
    source = tmp_path / "rank16-source-native"
    rank = 16
    tp_size = 4
    expert_parallel_size = 8
    experts_per_shard = 1
    rank_a = _values((rank, 3))
    shared_expert_a = _values((1, rank, 3), 100)
    hf = {
        "model.layers.0.self_attn.q_a_proj.lora_A.weight": rank_a,
        "model.layers.1.mlp.experts.gate_proj.lora_A.weight": shared_expert_a,
        "model.layers.1.mlp.experts.up_proj.lora_A.weight": shared_expert_a.clone(),
    }
    for expert in range(expert_parallel_size):
        hf[f"model.layers.1.mlp.experts.{expert}.gate_proj.lora_B.weight"] = _values(
            (2, rank), 1000 * expert
        )
        hf[f"model.layers.1.mlp.experts.{expert}.up_proj.lora_B.weight"] = _values(
            (2, rank), 1000 * expert + 100
        )
        hf[f"model.layers.1.mlp.experts.{expert}.down_proj.lora_A.weight"] = _values(
            (rank, 2), 1000 * expert + 200
        )
    _write_adapter(source, hf, rank=rank)

    native_names = [
        "module.module.decoder.layers.0.self_attention.linear_q_down_proj.adapter.linear_in.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc1.adapter.linear_in.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc1.adapter.linear_out.weight",
        "module.module.decoder.layers.1.mlp.experts.linear_fc2.adapter.linear_in.weight",
    ]
    for tp_rank in range(tp_size):
        native = {
            name: native_tensor_from_hf(
                name,
                hf,
                tp_rank=tp_rank,
                tp_size=tp_size,
                rank_block_size=rank,
                experts_per_shard=experts_per_shard,
                rank_layout=RANK_LAYOUT_TP_MAJOR,
            )
            for name in native_names
        }
        torch.save(native, source / f"adapter_megatron_tp{tp_rank}_pp0.pt")
    return source


def _replace_legacy_shards_with_ep8(source: Path) -> None:
    hf = torch.load(source / "adapter_model.bin", map_location="cpu", weights_only=True)
    legacy = {
        tp_rank: torch.load(
            source / f"adapter_megatron_tp{tp_rank}_pp0.pt",
            map_location="cpu",
            weights_only=True,
        )
        for tp_rank in range(4)
    }
    for ep_rank in range(8):
        tp_rank = ep_rank % 4
        native = reconstruct_native_state(
            hf,
            legacy[tp_rank],
            tp_rank=tp_rank,
            tp_size=4,
            rank_block_size=16,
            experts_per_shard=1,
            rank_layout=RANK_LAYOUT_TP_MAJOR,
            expert_index_start=ep_rank,
        )
        torch.save(
            native,
            source / f"adapter_megatron_tp{tp_rank}_pp0_ep{ep_rank}.pt",
        )
    for tp_rank in range(4):
        (source / f"adapter_megatron_tp{tp_rank}_pp0.pt").unlink()


def test_reconstruction_is_proof_gated_and_deterministic(tmp_path) -> None:
    source, template = _synthetic_bundle(tmp_path)
    output_a = tmp_path / "output-a"
    output_b = tmp_path / "output-b"

    manifest_a = reconstruct_adapter(source, template, output_a)
    reconstruct_adapter(source, template, output_b)

    assert manifest_a["template"]["proof"]["status"] == "passed"
    assert manifest_a["template"]["proof"]["all_template_native_tensor_bytes_exact"]
    assert manifest_a["mapping"]["source_rank_layout"]["selected"] == "tp-major"
    source_hf = torch.load(source / "adapter_model.bin", map_location="cpu", weights_only=True)
    for tp_rank in range(2):
        name = f"adapter_megatron_tp{tp_rank}_pp0.pt"
        assert sha256_path(output_a / name) == sha256_path(output_b / name)
        native = torch.load(output_a / name, map_location="cpu", weights_only=True)
        q_name = (
            "module.module.decoder.layers.0.self_attention.linear_q_down_proj."
            "adapter.linear_in.weight"
        )
        assert torch.equal(
            native[q_name],
            source_hf["model.layers.0.self_attn.q_a_proj.lora_A.weight"].chunk(2)[tp_rank],
        )

    broken = torch.load(
        template / "adapter_megatron_tp0_pp0.pt", map_location="cpu", weights_only=True
    )
    first = next(iter(broken))
    broken[first] = broken[first] + 1
    torch.save(broken, template / "adapter_megatron_tp0_pp0.pt")
    merge_manifest = json.loads((template / "merge_manifest.json").read_text())
    merge_manifest["files"]["adapter_megatron_tp0_pp0.pt"]["output_sha256"] = sha256_path(
        template / "adapter_megatron_tp0_pp0.pt"
    )
    (template / "merge_manifest.json").write_text(json.dumps(merge_manifest))

    rejected_output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="template reconstruction mismatch"):
        reconstruct_adapter(source, template, rejected_output)
    assert not rejected_output.exists()


def test_reconstruction_refuses_unrepresented_expert_state(tmp_path) -> None:
    source, template = _synthetic_bundle(tmp_path, mismatched_surplus_expert=True)
    output = tmp_path / "output"
    audit = tmp_path / "blocked-audit.json"

    with pytest.raises(
        ReconstructionBlockedError,
        match=r"1 of 6 uncovered expert tensors differ",
    ):
        reconstruct_adapter(
            source,
            template,
            output,
            audit_report_path=audit,
        )

    assert not output.exists()
    receipt = json.loads(audit.read_text())
    assert receipt["status"] == "blocked"
    assert receipt["outputs"]["native_shards_generated"] is False
    coverage = receipt["mapping"]["legacy_tp_only_expert_coverage"]
    assert coverage["uncovered"]["tensor_count"] == 6
    assert coverage["uncovered"]["mismatched_tensor_count"] == 1
    assert coverage["uncovered"]["exact_duplicate_tensor_count"] == 5


def test_ep8_reconstruction_roundtrips_every_hf_tensor(tmp_path) -> None:
    source, template = _synthetic_bundle(
        tmp_path,
        tp_size=4,
        source_expert_parallel_size=8,
    )
    legacy_output = tmp_path / "legacy-output"
    with pytest.raises(ReconstructionBlockedError):
        reconstruct_adapter(source, template, legacy_output)
    assert not legacy_output.exists()

    output = tmp_path / "ep8-output"
    manifest = reconstruct_adapter(
        source,
        template,
        output,
        expert_parallel_size=8,
    )
    output_b = tmp_path / "ep8-output-b"
    reconstruct_adapter(
        source,
        template,
        output_b,
        expert_parallel_size=8,
    )

    topology = [(item["tp_rank"], item["ep_rank"]) for item in manifest["mapping"]["rank_topology"]]
    assert topology == [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    roundtrip = manifest["mapping"]["source_hf_roundtrip"]
    assert roundtrip["status"] == "passed"
    assert roundtrip["coverage_fraction"] == 1.0
    assert roundtrip["source_hf_tensor_count"] == roundtrip["recovered_hf_tensor_count"]
    assert roundtrip["all_source_hf_tensor_bytes_exact"] is True

    source_hf = torch.load(source / "adapter_model.bin", map_location="cpu", weights_only=True)
    q_name = (
        "module.module.decoder.layers.0.self_attention.linear_q_down_proj.adapter.linear_in.weight"
    )
    fc1_name = "module.module.decoder.layers.1.mlp.experts.linear_fc1.adapter.linear_out.weight"
    for ep_rank in range(8):
        tp_rank = ep_rank % 4
        filename = f"adapter_megatron_tp{tp_rank}_pp0_ep{ep_rank}.pt"
        assert sha256_path(output / filename) == sha256_path(output_b / filename)
        native = torch.load(output / filename, map_location="cpu", weights_only=True)
        assert torch.equal(
            native[q_name],
            source_hf["model.layers.0.self_attn.q_a_proj.lora_A.weight"].chunk(4)[tp_rank],
        )
        gate, up = native[fc1_name][0].chunk(2, dim=0)
        assert torch.equal(
            gate,
            source_hf[f"model.layers.1.mlp.experts.{ep_rank}.gate_proj.lora_B.weight"],
        )
        assert torch.equal(
            up,
            source_hf[f"model.layers.1.mlp.experts.{ep_rank}.up_proj.lora_B.weight"],
        )


def test_rank16_source_native_template_roundtrips_every_hf_tensor(tmp_path) -> None:
    source = _synthetic_rank16_source_native_bundle(tmp_path)
    output = tmp_path / "rank16-ep8-output"
    output_b = tmp_path / "rank16-ep8-output-b"
    expected_source_sha256 = sha256_path(source / "adapter_model.bin")

    manifest = reconstruct_adapter(
        source,
        source,
        output,
        expected_source_sha256=expected_source_sha256,
        expert_parallel_size=8,
        source_native_template=True,
    )
    reconstruct_adapter(
        source,
        source,
        output_b,
        expected_source_sha256=expected_source_sha256,
        expert_parallel_size=8,
        source_native_template=True,
    )

    assert manifest["template"]["bundle_kind"] == "complete-source-native-checkpoint"
    assert "merge_manifest_sha256" not in manifest["template"]
    assert manifest["template"]["proof"]["status"] == "passed"
    assert manifest["template"]["proof"]["all_template_native_tensor_bytes_exact"]
    assert manifest["mapping"]["rank"] == 16
    assert manifest["mapping"]["template_rank_block_size"] == 16
    assert manifest["mapping"]["template_rank_block_count"] == 1
    rank_layout = manifest["mapping"]["source_rank_layout"]
    assert rank_layout["selected"] == "tp-major"
    assert rank_layout["rank_layouts_equivalent"] is True
    assert rank_layout["all_reference_tensor_bytes_exact"] is True
    roundtrip = manifest["mapping"]["source_hf_roundtrip"]
    assert roundtrip["status"] == "passed"
    assert roundtrip["coverage_fraction"] == 1.0
    assert roundtrip["source_hf_tensor_count"] == roundtrip["recovered_hf_tensor_count"]
    assert roundtrip["all_source_hf_tensor_bytes_exact"] is True

    output_names = set(manifest["outputs"]["native_shards"])
    assert output_names == {
        f"adapter_megatron_tp{ep_rank % 4}_pp0_ep{ep_rank}.pt" for ep_rank in range(8)
    }
    for name in output_names:
        assert sha256_path(output / name) == sha256_path(output_b / name)


def test_distinct_unmerged_rank16_template_roundtrips_selected_source(tmp_path) -> None:
    template = _synthetic_rank16_source_native_bundle(tmp_path)
    source = tmp_path / "selected-rank16-source"
    source_hf = torch.load(
        template / "adapter_model.bin", map_location="cpu", weights_only=True
    )
    source_hf = {name: tensor + 0.25 for name, tensor in source_hf.items()}
    _write_adapter(source, source_hf, rank=16)
    output = tmp_path / "selected-rank16-ep8-output"

    manifest = reconstruct_adapter(
        source,
        template,
        output,
        expected_source_sha256=sha256_path(source / "adapter_model.bin"),
        expert_parallel_size=8,
        unmerged_native_template=True,
    )

    assert manifest["source"]["adapter_model_sha256"] == sha256_path(
        source / "adapter_model.bin"
    )
    assert manifest["source"]["adapter_model_sha256"] != manifest["template"][
        "adapter_model_sha256"
    ]
    assert manifest["template"]["bundle_kind"] == "complete-source-native-checkpoint"
    layout = manifest["mapping"]["source_rank_layout"]
    assert layout["selected"] == "tp-major"
    assert (
        layout["selection_basis"]
        == "separate-unmerged-template-byte-exact-proof-plus-source-hf-roundtrip"
    )
    roundtrip = manifest["mapping"]["source_hf_roundtrip"]
    assert roundtrip["status"] == "passed"
    assert roundtrip["coverage_fraction"] == 1.0
    assert roundtrip["all_source_hf_tensor_bytes_exact"] is True
    assert sha256_path(output / "adapter_model.bin") == sha256_path(
        source / "adapter_model.bin"
    )
    assert set(manifest["outputs"]["native_shards"]) == {
        f"adapter_megatron_tp{ep_rank % 4}_pp0_ep{ep_rank}.pt"
        for ep_rank in range(8)
    }


def test_source_native_template_is_explicit_and_fails_closed(tmp_path) -> None:
    source = _synthetic_rank16_source_native_bundle(tmp_path)
    with pytest.raises(ValueError, match="source and template adapter directories must differ"):
        reconstruct_adapter(source, source, tmp_path / "implicit-output")

    corrupted = torch.load(
        source / "adapter_megatron_tp0_pp0.pt",
        map_location="cpu",
        weights_only=True,
    )
    first = next(iter(corrupted))
    corrupted[first] = corrupted[first] + 1
    torch.save(corrupted, source / "adapter_megatron_tp0_pp0.pt")

    rejected_output = tmp_path / "rejected-rank16-output"
    with pytest.raises(ValueError, match="template reconstruction mismatch"):
        reconstruct_adapter(
            source,
            source,
            rejected_output,
            expected_source_sha256=sha256_path(source / "adapter_model.bin"),
            expert_parallel_size=8,
            source_native_template=True,
        )
    assert not rejected_output.exists()


def test_ep8_only_source_native_template_is_proof_gated(tmp_path) -> None:
    source = _synthetic_rank16_source_native_bundle(tmp_path)
    _replace_legacy_shards_with_ep8(source)
    output = tmp_path / "ep8-source-native-output"

    manifest = reconstruct_adapter(
        source,
        source,
        output,
        expected_source_sha256=sha256_path(source / "adapter_model.bin"),
        expert_parallel_size=8,
        source_native_template=True,
    )

    proof = manifest["template"]["source_ep_native_proof"]
    assert proof["status"] == "passed"
    assert proof["all_source_ep_native_tensor_bytes_exact"] is True
    assert proof["source_hf_roundtrip"]["coverage_fraction"] == 1.0
    assert set(manifest["template"]["source_native_bundle"]["files"]) == {
        "adapter_model.bin",
        "adapter_config.json",
        *{
            f"adapter_megatron_tp{ep_rank % 4}_pp0_ep{ep_rank}.pt"
            for ep_rank in range(8)
        },
    }
    assert set(manifest["outputs"]["native_shards"]) == {
        f"adapter_megatron_tp{ep_rank % 4}_pp0_ep{ep_rank}.pt" for ep_rank in range(8)
    }
