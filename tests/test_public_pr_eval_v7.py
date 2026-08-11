from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

from glm47_posttraining.public_pr_eval.validator import (
    PRIORITIZED_REPAIR_INSTRUCTION_IDS,
    PRIORITIZED_REPAIR_PARENT_PROMPT_SHA256,
    PRIORITIZED_REPAIR_PROMPT_PROFILE,
    canonical_json,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
V7_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v7.jsonl"
)
V7_SHA256 = "cec16a8abd6b1d66e40d6d8fc9cff872229173b2614ae4e0f7754e5b61969a89"


def _load_builder():
    path = REPO_ROOT / "scripts/build_public_pr_eval_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_pr_eval_v2_v7", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v7_contract_is_deterministic_valid_and_thinking_on() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_prioritized_verified_mechanism_tasks()
    generated = b"".join(canonical_json(row) for row in rows)

    assert generated == V7_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == V7_SHA256
    assert (
        V7_JSONL.with_suffix(".jsonl.sha256").read_text(encoding="utf-8")
        == f"{V7_SHA256}  {V7_JSONL.name}\n"
    )
    assert validate_contract_file(V7_JSONL, REPO_ROOT)["decision"] == "PASS"

    row = rows[0]
    assert row["run_policy"]["thinking_mode"] == "enabled"
    assert row["harness_instructions"]["thinking_mode"] == "enabled"
    assert row["hidden_validation"]["mechanism_verification"]["required_for_pass"]


def test_v7_prompt_is_failure_prioritized_without_generic_38_steps() -> None:
    builder = _load_builder()
    row = builder.demo_fmtlib_prioritized_verified_mechanism_tasks()[0]
    prompt = row["model_input"]["messages"][0]["content"]
    prompt_path = REPO_ROOT / "reports/public-pr-prompt-ablation-r3/final-prompt.md"

    assert prompt == prompt_path.read_text(encoding="utf-8")
    assert len(prompt) < 18_000
    assert not re.findall(r"\[W\d{2}\]|\[F\d{2}\]|\[C\d{2}\]", prompt)
    assert tuple(re.findall(r"\[(P\d{2})\]", prompt)) == (
        PRIORITIZED_REPAIR_INSTRUCTION_IDS
    )
    assert prompt.index("## Priority 0: add the helper block") < prompt.index(
        "## Priority 1: migrate every consumer"
    )
    assert prompt.index("## Priority 1: migrate every consumer") < prompt.index(
        "## Priority 2: preserve fragile structure"
    )

    contract = row["prompt_contract"]
    assert contract["profile"] == PRIORITIZED_REPAIR_PROMPT_PROFILE
    assert (
        contract["parent_prompt_sha256"]
        == PRIORITIZED_REPAIR_PARENT_PROMPT_SHA256
    )
    assert contract["priority_check_ids"] == list(
        PRIORITIZED_REPAIR_INSTRUCTION_IDS
    )
    assert "generic_w01_w38_repository_workflow" in contract["removed_sections"]
    assert "ten_flat_c01_c10_audit_locks" in contract["removed_sections"]


def test_v7_prompt_retains_exact_reference_aligned_compile_fixes() -> None:
    prompt = _load_builder().demo_fmtlib_failure_prioritized_prompt()

    required = (
        "template <typename Duration>\nstd::time_t to_time_t(",
        "template <typename Duration>\ninline std::tm gmtime(",
        "safe_duration_cast::safe_duration_cast<To>(from, ec)",
        "detail::to_time_t(time_point)",
        "d - fmt_duration_cast<std::chrono::seconds>(d)",
        "detail::fmt_duration_cast<Duration>(",
        "do_format(gmtime(val), ctx, &subsecs)",
        "format(localtime(val), ctx)",
        "`Duration` not declared",
        "`fmt_duration_cast` not declared",
        "`to_time_t` not a member of `detail`",
        "call `to_time_t` with a system-clock `time_point`, never",
    )
    for shape in required:
        assert shape in prompt


def test_v7_remains_available_but_is_not_the_current_docker_default() -> None:
    runtime = (
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py"
    ).read_text(encoding="utf-8")
    launcher = (REPO_ROOT / "scripts/gcp_public_pr_eval_run.sh").read_text(
        encoding="utf-8"
    )
    dockerfile = (
        REPO_ROOT / "docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile"
    ).read_text(encoding="utf-8")

    assert V7_SHA256 in runtime and V7_SHA256 not in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v7.jsonl" in runtime
    assert "public-pr-repo-eval-demo-fmtlib-v7.jsonl" not in dockerfile
    assert 'default="fmtlib-final-cleanup-verified-mechanisms-thinking"' in runtime
    assert (
        'SUITE="${SUITE:-fmtlib-final-cleanup-verified-mechanisms-thinking}"'
        in launcher
    )
    assert "synthmem-v1-ep50-thinking-v8" in launcher
