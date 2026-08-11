from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from glm47_posttraining.public_pr_eval.validator import (
    canonical_json,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
V5_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v5.jsonl"
)
V5_SHA256 = "db8de1a51420ba5424f1799ea15e81adeaadaeb3dcd6331ce94412d98c223202"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v5_contract_is_deterministic_and_thinking_on() -> None:
    builder = _load(
        REPO_ROOT / "scripts/build_public_pr_eval_v2.py",
        "build_public_pr_eval_v2_v5",
    )
    rows = builder.demo_fmtlib_compact_bestof4_thinking_tasks()
    generated = b"".join(canonical_json(row) for row in rows)
    assert generated == V5_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == V5_SHA256
    assert validate_contract_file(V5_JSONL, REPO_ROOT)["decision"] == "PASS"

    row = rows[0]
    assert row["run_policy"]["thinking_mode"] == "enabled"
    assert row["harness_instructions"]["thinking_mode"] == "enabled"
    assert row["harness_instructions"]["thinking_request"] == {
        "transport": "openai_chat_completions_extra_body",
        "field": "chat_template_kwargs.enable_thinking",
        "value": True,
    }


def test_v1_epoch50_profile_and_thinking_request_are_exact(tmp_path: Path) -> None:
    runtime = _load(
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py",
        "gcp_public_pr_synthmem_v1_ep50",
    )
    profile = runtime.CHECKPOINT_PROFILES["synthmem-v1-ep50"]
    assert runtime.DEFAULT_CHECKPOINT_PROFILE == "synthmem-v1-ep50"
    assert profile["training_run_id"] == (
        "glm47-synth-memorization-v1-100ep-20260731T071000Z"
    )
    assert profile["checkpoint_path"] == "checkpoints/sft_lora_r16/iter_0000649"
    assert profile["epoch"] == 50
    assert profile["optimizer_iteration"] == 649
    assert profile["source_adapter_sha256"] == (
        "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a"
    )
    assert profile["serving_adapter_sha256"] == (
        "6de1aeba533a5bfef26a73286fc32b47f403c022bd7467e2b3dc32cf18a35f48"
    )

    settings = tmp_path / "model-settings.yml"
    runtime.write_model_settings(
        settings,
        str(profile["model_name"]),
        True,
        "diff",
        temperature=0.2,
        seed=1704,
    )
    text = settings.read_text(encoding="utf-8")
    assert "extra_body:" in text
    assert "chat_template_kwargs:" in text
    assert "enable_thinking: true" in text
    assert "temperature: 0.2" in text
    assert "seed: 1704" in text


def test_v1_epoch50_image_is_v8_single_suite_and_launcher_defaults_match() -> None:
    dockerfile = (
        REPO_ROOT / "docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile"
    ).read_text(encoding="utf-8")
    launcher = (REPO_ROOT / "scripts/gcp_public_pr_eval_run.sh").read_text(
        encoding="utf-8"
    )
    assert "38f567a074a5a61e53ee1dad478833f10d9f7a40738d8d6c0baedfe1fe5294b6" in dockerfile
    assert dockerfile.count("verify-oracles") == 1
    assert "public-pr-repo-eval-demo-fmtlib-v8.jsonl" in dockerfile
    assert "public-pr-repo-eval-v2-r5.jsonl" not in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v4.jsonl" not in dockerfile
    assert 'CHECKPOINT_PROFILE="${CHECKPOINT_PROFILE:-synthmem-v1-ep50}"' in launcher
    assert (
        'SUITE="${SUITE:-fmtlib-final-cleanup-verified-mechanisms-thinking}"' in launcher
    )
    assert "docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile" in launcher
