from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import glm47_posttraining.public_pr_eval.runner as runner
from glm47_posttraining.public_pr_eval.validator import (
    COMPACT_REPAIR_INSTRUCTION_IDS,
    COMPACT_REPAIR_PROMPT_PROFILE,
    REQUIRED_PROMPT_SECTIONS,
    canonical_json,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
V4_JSONL = (
    REPO_ROOT
    / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl"
)
V4_SHA256 = "03ed4454a8953b80b09325392c0045e9ea0ba64b6c483ea886c3850ffbd7c7a3"
HANDOFF_PROMPT_SHA256 = (
    "b3997db3f5148890b879db2807c9a3c8de6f5be0552954cef529d8110c86ed25"
)


def _load_builder():
    path = REPO_ROOT / "scripts/build_public_pr_eval_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_pr_eval_v2_v4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v4_contract_is_deterministic_compact_and_valid() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_compact_bestof4_tasks()
    generated = b"".join(canonical_json(row) for row in rows)
    assert generated == V4_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == V4_SHA256
    report = validate_contract_file(V4_JSONL, REPO_ROOT)
    assert report["decision"] == "PASS"

    row = rows[0]
    prompt = row["model_input"]["messages"][0]["content"]
    assert row["prompt_contract"]["profile"] == COMPACT_REPAIR_PROMPT_PROFILE
    assert row["prompt_contract"]["handoff_prompt_sha256"] == HANDOFF_PROMPT_SHA256
    assert 7_063 < len(prompt.encode("utf-8")) < 13_717
    assert all(section in prompt for section in REQUIRED_PROMPT_SECTIONS)
    assert "# Mandatory repository-edit workflow" not in prompt
    assert "# Task-specific implementation self-audit" not in prompt
    for instruction_id in COMPACT_REPAIR_INSTRUCTION_IDS:
        assert prompt.count(f"[{instruction_id}]") == 1

    policy = row["run_policy"]
    assert policy["candidate_count"] == 4
    assert policy["seeds"] == [1701, 1702, 1703, 1704]
    assert policy["attempts"] == 2
    assert row["harness_instructions"]["aider_auto_lint"] is False
    assert row["harness_instructions"]["aider_auto_test"] is False


def test_aider_command_disables_opaque_internal_lint_only_when_requested(
    tmp_path: Path,
) -> None:
    common = {
        "aider_python": "python",
        "model": "model",
        "settings": tmp_path / "settings.yml",
        "message": tmp_path / "message.txt",
        "history": tmp_path / "history.md",
        "editable_files": ["include/fmt/chrono.h"],
        "restore": False,
        "edit_format": "diff",
    }
    controlled = runner._aider_command(
        **common,
        auto_lint=False,
        auto_test=False,
    )
    assert "--no-auto-lint" in controlled
    assert "--no-auto-test" in controlled

    historical = runner._aider_command(
        **common,
        auto_lint=True,
        auto_test=False,
    )
    assert "--no-auto-lint" not in historical
    assert "--no-auto-test" in historical


def test_aider_model_call_markers_are_recorded() -> None:
    output = (
        "Tokens: 81k sent, 6.5k received.\n"
        "Applied edit\n"
        "Tokens: 84k sent, 1.2k received.\n"
    )
    assert runner.observed_aider_model_calls(output) == 2
    assert runner.observed_aider_model_calls("no usage markers") is None


def test_best_of_n_uses_fresh_candidates_and_stops_on_first_pass(
    monkeypatch, tmp_path: Path
) -> None:
    calls: list[int] = []

    def fake_evaluate(candidate_row, *, output_dir, **_kwargs):
        seed = candidate_row["run_policy"]["seeds"][0]
        calls.append(seed)
        output_dir.mkdir(parents=True)
        passed = seed == 1702
        score = {
            "passed": passed,
            "scope_passed": True,
            "build_passed": passed,
            "probe_passed": passed,
            "build_commands": [],
            "probe_commands": [],
        }
        return {
            "task_id": candidate_row["task_id"],
            "pass_at_1": passed,
            "pass_at_2": passed,
            "attempts": [{"score": score, "diagnostics": {"failure_class": "none"}}],
            "final_changed_paths": ["include/fmt/chrono.h"],
        }

    monkeypatch.setattr(runner, "evaluate_task_with_aider", fake_evaluate)
    settings = {}
    repairs = {}
    for seed in (1701, 1702, 1703, 1704):
        settings[seed] = tmp_path / f"settings-{seed}.yml"
        repairs[seed] = tmp_path / f"repair-{seed}.yml"

    row = {
        "task_id": "fmtlib-unit-best-of-n",
        "run_policy": {
            "candidate_count": 4,
            "candidate_isolation": "fresh_prepared_repository_copy",
            "candidate_selection": "first_executable_pass_else_furthest_executable_stage",
            "stop_on_first_executable_pass": True,
            "seeds": [1701, 1702, 1703, 1704],
        },
    }
    receipt = runner.evaluate_task_best_of_n(
        row,
        prepared_repo=tmp_path / "prepared",
        output_dir=tmp_path / "output",
        aider_python="python",
        model="unit",
        model_settings_by_seed=settings,
        api_base="http://127.0.0.1:1/v1",
        api_key="unit",
        repair_model_settings_by_seed=repairs,
    )
    assert calls == [1701, 1702]
    assert receipt["candidate_count_requested"] == 4
    assert receipt["candidate_count_executed"] == 2
    assert receipt["selected_candidate_seed"] == 1702
    assert receipt["selection_basis"] == "first_executable_pass"
    assert receipt["pass_at_2"] is True


def test_candidate_ranking_ignores_reference_similarity_and_checklist() -> None:
    scope_only = {
        "attempts": [
            {
                "score": {
                    "passed": False,
                    "scope_passed": True,
                    "build_passed": False,
                    "probe_passed": False,
                    "build_commands": [],
                    "probe_commands": [],
                },
                "diagnostics": {
                    "exact_upstream_production_match": True,
                    "demo_baseline": {"present_checklist_items": 12},
                },
            }
        ]
    }
    executable_progress = {
        "attempts": [
            {
                "score": {
                    "passed": False,
                    "scope_passed": True,
                    "build_passed": True,
                    "probe_passed": False,
                    "build_commands": [{"returncode": 0}],
                    "probe_commands": [{"returncode": 1}],
                },
                "diagnostics": {
                    "exact_upstream_production_match": False,
                    "demo_baseline": {"present_checklist_items": 0},
                },
            }
        ]
    }
    assert runner._candidate_rank(executable_progress) > runner._candidate_rank(
        scope_only
    )


def test_gcp_v4_bindings_are_present() -> None:
    runtime = (
        REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py"
    ).read_text(encoding="utf-8")
    dockerfile = (
        REPO_ROOT / "docker/public-pr-synthmem-gcp/Dockerfile"
    ).read_text(encoding="utf-8")
    assert "fmtlib-compact-repair-bestof4" in runtime
    assert "public-pr-repo-eval-demo-fmtlib-v4.jsonl" in runtime
    assert "candidate_seeds" in runtime
    assert "model_settings_by_seed" in runtime
    assert V4_SHA256 in runtime
    assert V4_SHA256 in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v4.jsonl" in dockerfile
