from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from glm47_posttraining.public_pr_eval.validator import (
    FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256,
    FINAL_CLEANUP_REPAIR_PROMPT_PROFILE,
    FINAL_CLEANUP_REPAIR_SUFFIX,
    canonical_json,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
V7_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v7.jsonl"
)
V8_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v8.jsonl"
)
V8_SHA256 = "38f567a074a5a61e53ee1dad478833f10d9f7a40738d8d6c0baedfe1fe5294b6"


def _load_builder():
    path = REPO_ROOT / "scripts/build_public_pr_eval_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_pr_eval_v2_v8", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v8_contract_is_deterministic_valid_and_thinking_on() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_final_cleanup_verified_mechanism_tasks()
    generated = b"".join(canonical_json(row) for row in rows)

    assert generated == V8_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == V8_SHA256
    assert (
        V8_JSONL.with_suffix(".jsonl.sha256").read_text(encoding="utf-8")
        == f"{V8_SHA256}  {V8_JSONL.name}\n"
    )
    assert validate_contract_file(V8_JSONL, REPO_ROOT)["decision"] == "PASS"

    row = rows[0]
    assert row["run_policy"]["thinking_mode"] == "enabled"
    assert row["harness_instructions"]["thinking_mode"] == "enabled"
    assert row["hidden_validation"]["mechanism_verification"]["required_for_pass"]


def test_v8_prompt_adds_only_the_terminal_cleanup_gate_to_v7() -> None:
    builder = _load_builder()
    v7_prompt = builder.demo_fmtlib_failure_prioritized_prompt()
    v8_prompt = builder.demo_fmtlib_final_cleanup_prompt()

    assert hashlib.sha256(v7_prompt.encode("utf-8")).hexdigest() == (
        FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256
    )
    assert v8_prompt == v7_prompt.rstrip() + "\n\n" + FINAL_CLEANUP_REPAIR_SUFFIX
    assert v8_prompt.endswith(FINAL_CLEANUP_REPAIR_SUFFIX)
    assert v8_prompt.count("# Final mandatory cleanup") == 1
    assert len(v8_prompt) < 18_000

    v7_row = json.loads(V7_JSONL.read_text(encoding="utf-8"))
    v8_row = json.loads(V8_JSONL.read_text(encoding="utf-8"))
    assert v7_row["model_input"]["messages"][0]["content"] == v7_prompt
    assert v8_row["model_input"]["messages"][0]["content"] == v8_prompt


def test_v8_contract_binds_the_mandatory_cleanup() -> None:
    row = _load_builder().demo_fmtlib_final_cleanup_verified_mechanism_tasks()[0]
    contract = row["prompt_contract"]

    assert contract["profile"] == FINAL_CLEANUP_REPAIR_PROMPT_PROFILE
    assert (
        contract["parent_prompt_sha256"]
        == FINAL_CLEANUP_REPAIR_PARENT_PROMPT_SHA256
    )
    assert "final_mandatory_legacy_helper_cleanup" in contract["added_sections"]
    assert contract["mandatory_cleanup"] == {
        "identifier_must_be_absent": "fmt_safe_duration_cast",
        "replacement_helper": "fmt_duration_cast",
        "required_after_consumer_migration": True,
        "preserve_adjacent_structure": True,
    }


def test_v8_is_the_current_gcp_and_docker_default() -> None:
    runtime = (
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py"
    ).read_text(encoding="utf-8")
    launcher = (REPO_ROOT / "scripts/gcp_public_pr_eval_run.sh").read_text(
        encoding="utf-8"
    )
    dockerfile = (
        REPO_ROOT / "docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile"
    ).read_text(encoding="utf-8")

    assert V8_SHA256 in runtime and V8_SHA256 in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v8.jsonl" in runtime
    assert "public-pr-repo-eval-demo-fmtlib-v8.jsonl" in dockerfile
    assert 'default="fmtlib-final-cleanup-verified-mechanisms-thinking"' in runtime
    assert (
        'SUITE="${SUITE:-fmtlib-final-cleanup-verified-mechanisms-thinking}"'
        in launcher
    )
    assert "synthmem-v1-ep50-thinking-v8" in launcher
