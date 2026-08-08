from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import glm47_posttraining.public_pr_eval.runner as runner_module
from glm47_posttraining.public_pr_eval.runner import (
    BASELINE_TAG,
    changed_paths,
    compiler_feedback_for_attempt,
    score_candidate,
    write_attempt_diagnostics,
)
from glm47_posttraining.public_pr_eval.validator import (
    BASELINE_REPAIR_INSTRUCTION_IDS,
    BASELINE_REPAIR_PROMPT_PROFILE,
    COMPILER_FEEDBACK_MODE,
    EXACT_FEEDBACK,
    REQUIRED_PROMPT_SECTIONS,
    REQUIRED_TASK_AUDIT_SECTION,
    REQUIRED_WORKFLOW_INSTRUCTION_IDS,
    REQUIRED_WORKFLOW_SECTION,
    canonical_json,
    finding_ids,
    load_jsonl,
    validate_contract_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_JSONL = REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl"
EXPECTED_SHA256 = "316e293ecf3a183b1f14612007e47edfbbea3e2b72ee5349b95b12d0a779ec82"
DEMO_EXPECTED_SHA256 = (
    "9db4bbc4df06aed1cb87dca1026456f2cafa3973f15024fba41b3c912d5b22a7"
)
COMPILER_REPAIR_EXPECTED_SHA256 = (
    "01d2015df04766726b778948997be9d34aa48cba1e78c002d92429b582e0765c"
)


def _load_builder():
    path = REPO_ROOT / "scripts/build_public_pr_eval_v2.py"
    spec = importlib.util.spec_from_file_location("build_public_pr_eval_v2", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def test_generated_contract_is_deterministic_and_static_validator_passes() -> None:
    builder = _load_builder()
    generated = b"".join(canonical_json(row) for row in builder.tasks())
    assert generated == TASK_JSONL.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == EXPECTED_SHA256
    report = validate_contract_file(TASK_JSONL, REPO_ROOT)
    assert report["decision"] == "PASS"
    assert report["row_count"] == report["passed_rows"] == 3
    assert report["scope"] == "format_prompt_content_code_quality_only"


def test_fmtlib_demo_contract_is_single_turn_and_checklisted() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_single_turn_tasks()
    assert len(rows) == 1
    row = rows[0]
    assert row["task_id"] == "fmtlib-fmt-large-time-point-overflow-v2"
    assert row["run_policy"]["attempts"] == 1
    assert "attempt_2_feedback" not in row["run_policy"]
    assert row["output_contract"]["edit_format"] == "diff"
    assert row["model_input"]["response_protocol"] == "aider_diff_workspace_edit"
    assert row["demo_evaluation_policy"]["minimum_present_checklist_items"] == 9
    assert row["demo_evaluation_policy"]["total_checklist_items"] == 12
    assert len(row["required_header_changes"]) == 12
    assert row["harness_instructions"]["edit_format"] == "diff"
    assert row["harness_instructions"]["hard_scope_gate"].startswith(
        "changed_paths must be"
    )
    assert row["hard_scope_gate"] == {
        "schema_version": "public-pr-hard-scope-gate-v1",
        "require_nonempty_change": True,
        "required_changed_paths": ["include/fmt/chrono.h"],
        "allowed_changed_paths": ["include/fmt/chrono.h"],
        "forbidden_changed_paths": ["test/chrono-test.cc", "include/fmt/format.h"],
        "failure_class_when_empty": "no_production_change",
        "failure_class_when_forbidden_path_changes": "scope_violation",
    }
    assert row["harness_instructions"]["demo_baseline_pass"].startswith(
        "demo_baseline.passed"
    )
    assert "Do not modify include/fmt/format.h." in row["wrong_solution_guards"]
    assert row["demo_evaluation_policy"]["minimum_line_similarity_ratio"] == 0.75
    checklist = row["diagnostic_checklist"]
    assert [item["id"] for item in checklist] == [
        "fmt-duration-cast-helper",
        "same-arithmetic-dispatch",
        "safe-cast-placement",
        "to-time-t-helper",
        "templated-gmtime",
        "localtime-to-time-t",
        "fractional-seconds-casts",
        "remove-old-safe-helper",
        "milliseconds-casts",
        "chrono-formatter-cast",
        "time-point-root-fix",
        "local-time-root-fix",
    ]
    demo_jsonl = (
        REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl"
    )
    generated = b"".join(canonical_json(item) for item in rows)
    assert generated == demo_jsonl.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == DEMO_EXPECTED_SHA256
    report = validate_contract_file(demo_jsonl, REPO_ROOT)
    assert report["decision"] == "PASS"
    assert report["row_count"] == report["passed_rows"] == 1


def test_fmtlib_compiler_repair_contract_preserves_first_prompt_strengths() -> None:
    builder = _load_builder()
    rows = builder.demo_fmtlib_compiler_repair_tasks()
    assert len(rows) == 1
    row = rows[0]
    contract = row["prompt_contract"]
    assert contract["profile"] == BASELINE_REPAIR_PROMPT_PROFILE
    assert contract["baseline_prompt_sha256"] == (
        "443e4fe72cc4960881d2718821e7f4cf3cb00100080f0b64677b1d02025fdf77"
    )
    assert contract["preserved_baseline_mechanisms"] == [
        "fmt-duration-cast-helper",
        "same-arithmetic-dispatch",
        "safe-cast-placement",
        "templated-gmtime",
        "localtime-to-time-t",
        "fractional-seconds-casts",
        "remove-old-safe-helper",
        "chrono-formatter-cast",
    ]
    prompt = row["model_input"]["messages"][0]["content"]
    final_prompt = REPO_ROOT / "reports/public-pr-prompt-ablation-r1/final-prompt.md"
    assert final_prompt.read_text(encoding="utf-8") == prompt
    assert "# Mandatory repository-edit workflow" not in prompt
    assert "# Task-specific implementation self-audit" not in prompt
    assert "Demo baseline scoring" not in prompt
    assert "template <typename Duration>\nstd::time_t to_time_t(" in prompt
    assert "safe_duration_cast::safe_duration_cast<To>(from, ec)" in prompt
    assert "do_format(gmtime(val), ctx, &subsecs)" in prompt
    for instruction_id in BASELINE_REPAIR_INSTRUCTION_IDS:
        assert prompt.count(f"[{instruction_id}]") == 1
    assert row["run_policy"]["attempts"] == 2
    assert row["run_policy"]["attempt_2_feedback_mode"] == COMPILER_FEEDBACK_MODE
    assert row["run_policy"]["repair_temperature"] == 0.2

    jsonl = REPO_ROOT / "configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl"
    generated = b"".join(canonical_json(item) for item in rows)
    assert generated == jsonl.read_bytes()
    assert hashlib.sha256(generated).hexdigest() == COMPILER_REPAIR_EXPECTED_SHA256
    report = validate_contract_file(jsonl, REPO_ROOT)
    assert report["decision"] == "PASS"


def test_compiler_feedback_exposes_only_first_editable_diagnostic(tmp_path: Path) -> None:
    log = tmp_path / "build.log"
    log.write_text(
        "/private/test/chrono-test.cc:91: error: secret evaluator assertion\n"
        "/work/include/fmt/chrono.h:527:18: error: 'to_time_t' is not a member of fmt::detail\n"
        "return gmtime(detail::to_time_t(time_point));\n"
        "                 ^~~~~~~~~\n"
        "/private/test/chrono-test.cc:92: note: expected secret output\n",
        encoding="utf-8",
    )
    score = {
        "build_commands": [
            {"name": "build-chrono", "returncode": 2, "log_path": str(log)}
        ]
    }
    feedback = compiler_feedback_for_attempt(score, ["include/fmt/chrono.h"])
    assert feedback != EXACT_FEEDBACK
    assert "include/fmt/chrono.h:527:18: error:" in feedback
    assert "/work" not in feedback
    assert "chrono-test.cc" not in feedback
    assert "secret" not in feedback
    assert "expected output" not in feedback


def test_compiler_feedback_falls_back_when_no_editable_diagnostic(tmp_path: Path) -> None:
    log = tmp_path / "build.log"
    log.write_text(
        "/private/test/chrono-test.cc:91: error: evaluator-only failure\n",
        encoding="utf-8",
    )
    score = {
        "build_commands": [
            {"name": "build-chrono", "returncode": 2, "log_path": str(log)}
        ]
    }
    assert (
        compiler_feedback_for_attempt(score, ["include/fmt/chrono.h"])
        == EXACT_FEEDBACK
    )


def test_evaluator_generates_compiler_feedback_before_repair_turn(
    monkeypatch, tmp_path: Path
) -> None:
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "include").mkdir()
    (prepared / "include/fmt").mkdir()
    (prepared / "include/fmt/chrono.h").write_text("broken\n", encoding="utf-8")
    initial_settings = tmp_path / "initial.yml"
    repair_settings = tmp_path / "repair.yml"
    initial_settings.write_text("temperature: 0.7\n", encoding="utf-8")
    repair_settings.write_text("temperature: 0.2\n", encoding="utf-8")
    messages: list[str] = []

    def fake_run(argv, **_kwargs):
        message_path = Path(argv[argv.index("--message-file") + 1])
        messages.append(message_path.read_text(encoding="utf-8"))
        return SimpleNamespace(returncode=0, stdout="aider output")

    score_index = 0

    def fake_score(_row, _repo, output_dir):
        nonlocal score_index
        output_dir.mkdir(parents=True)
        score_index += 1
        if score_index == 1:
            log = output_dir / "build.log"
            log.write_text(
                "/work/include/fmt/chrono.h:8: error: unterminated #ifndef\n",
                encoding="utf-8",
            )
            return {
                "passed": False,
                "build_commands": [
                    {"name": "build-chrono", "returncode": 2, "log_path": str(log)}
                ],
            }
        return {"passed": True, "build_commands": []}

    monkeypatch.setattr(runner_module, "_run", fake_run)
    monkeypatch.setattr(runner_module, "score_candidate", fake_score)
    monkeypatch.setattr(
        runner_module,
        "write_attempt_diagnostics",
        lambda *_args, **_kwargs: {"failure_class": "unit"},
    )
    monkeypatch.setattr(
        runner_module, "changed_paths", lambda _repo: ["include/fmt/chrono.h"]
    )
    row = {
        "task_id": "fmtlib-unit-repair",
        "model_input": {"messages": [{"content": "initial prompt"}]},
        "scope": {"editable_files": ["include/fmt/chrono.h"]},
        "output_contract": {"edit_format": "diff"},
        "run_policy": {
            "attempts": 2,
            "attempt_2_feedback_mode": COMPILER_FEEDBACK_MODE,
            "temperature": 0.7,
            "repair_temperature": 0.2,
            "top_p": 1.0,
            "seeds": [1701],
        },
    }
    receipt = runner_module.evaluate_task_with_aider(
        row,
        prepared_repo=prepared,
        output_dir=tmp_path / "output",
        aider_python="python",
        model="unit-model",
        model_settings=initial_settings,
        repair_model_settings=repair_settings,
        api_base="http://127.0.0.1:1/v1",
        api_key="unit",
    )
    assert len(messages) == 2
    assert messages[0] == "initial prompt"
    assert "include/fmt/chrono.h:8: error: unterminated #ifndef" in messages[1]
    assert receipt["pass_at_1"] is False
    assert receipt["pass_at_2"] is True
    assert receipt["attempts"][0]["model_settings_sha256"] != (
        receipt["attempts"][1]["model_settings_sha256"]
    )


def test_prompts_are_detailed_and_model_input_excludes_private_provenance() -> None:
    rows = load_jsonl(TASK_JSONL)
    assert len(REQUIRED_WORKFLOW_INSTRUCTION_IDS) == 38
    expected_task_audits = {
        "fmtlib-fmt-large-time-point-overflow-v2": tuple(
            f"F{index:02d}" for index in range(1, 13)
        ),
        "catch2-reset-assertion-disposition-v2": tuple(
            f"C{index:02d}" for index in range(1, 7)
        ),
        "simdjson-preserve-underflow-signed-zero-v2": tuple(
            f"S{index:02d}" for index in range(1, 7)
        ),
    }
    for row in rows:
        prompt = row["model_input"]["messages"][0]["content"]
        positions = [prompt.index(section) for section in REQUIRED_PROMPT_SECTIONS]
        assert positions == sorted(positions)
        assert len(prompt) >= 1_400
        assert row["repository"]["reference_commit"] not in prompt
        assert row["provenance"]["upstream_pr_url"] not in prompt
        assert "private_probes" not in prompt
        assert REQUIRED_WORKFLOW_SECTION in prompt
        assert REQUIRED_TASK_AUDIT_SECTION in prompt
        for instruction_id in REQUIRED_WORKFLOW_INSTRUCTION_IDS:
            assert prompt.count(f"[{instruction_id}]") == 1
        for instruction_id in expected_task_audits[row["task_id"]]:
            assert prompt.count(f"[{instruction_id}]") == 1
    assert len(rows[0]["diagnostic_checklist"]) == 12


def test_validator_rejects_incomplete_repository_edit_workflow(tmp_path: Path) -> None:
    rows = load_jsonl(TASK_JSONL)
    prompt = rows[2]["model_input"]["messages"][0]["content"].replace(
        "[W22]", "[REMOVED-W22]", 1
    )
    rows[2]["model_input"]["messages"][0]["content"] = prompt
    rows[2]["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt.encode()
    ).hexdigest()
    candidate = tmp_path / "missing-workflow-step.jsonl"
    candidate.write_bytes(b"".join(canonical_json(row) for row in rows))
    report = validate_contract_file(candidate, REPO_ROOT)
    finding_set = set(finding_ids(report))
    assert "PPR-PROMPT-008" in finding_set
    assert "PPR-PROMPT-009" in finding_set


def test_validator_rejects_non_exact_scope_without_task_specific_rules(
    tmp_path: Path,
) -> None:
    rows = load_jsonl(TASK_JSONL)
    rows[0]["scope"]["mode"] = "protected_paths_only"
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_bytes(b"".join(canonical_json(row) for row in rows))
    report = validate_contract_file(candidate, REPO_ROOT)
    assert report["decision"] == "FAIL"
    assert "PPR-SCOPE-001" in set(finding_ids(report))
    assert all("fmt" not in rule.lower() for rule in finding_ids(report))


def test_validator_rejects_prompt_provenance_leak(tmp_path: Path) -> None:
    rows = load_jsonl(TASK_JSONL)
    prompt = (
        rows[1]["model_input"]["messages"][0]["content"]
        + "\nhttps://github.com/example/pull/1\n"
    )
    rows[1]["model_input"]["messages"][0]["content"] = prompt
    rows[1]["integrity"]["model_prompt_sha256"] = hashlib.sha256(
        prompt.encode()
    ).hexdigest()
    candidate = tmp_path / "leaked.jsonl"
    candidate.write_bytes(b"".join(canonical_json(row) for row in rows))
    report = validate_contract_file(candidate, REPO_ROOT)
    assert "PPR-PROMPT-004" in set(finding_ids(report))


def test_changed_path_gate_covers_committed_working_staged_and_untracked(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@invalid")
    (repo / "allowed.cpp").write_text("int value = 1;\n", encoding="utf-8")
    _git(repo, "add", "allowed.cpp")
    _git(repo, "commit", "-qm", "baseline")
    _git(repo, "tag", BASELINE_TAG)

    (repo / "allowed.cpp").write_text("int value = 2;\n", encoding="utf-8")
    (repo / "extra.txt").write_text("unexpected\n", encoding="utf-8")
    assert changed_paths(repo) == ["allowed.cpp", "extra.txt"]

    _git(repo, "add", "allowed.cpp")
    _git(repo, "commit", "-qm", "model committed unexpectedly")
    assert changed_paths(repo) == ["allowed.cpp", "extra.txt"]


def test_score_candidate_requires_nonempty_target_header_change(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@invalid")
    header = repo / "include/fmt/chrono.h"
    header.parent.mkdir(parents=True)
    header.write_text("// baseline header\n", encoding="utf-8")
    _git(repo, "add", "include/fmt/chrono.h")
    _git(repo, "commit", "-qm", "baseline")
    _git(repo, "tag", BASELINE_TAG)

    row = {
        "task_id": "synthetic-hard-scope-test",
        "scope": {"editable_files": ["include/fmt/chrono.h"]},
        "hidden_validation": {"build_commands": [], "probe_commands": []},
    }
    score = score_candidate(row, repo, tmp_path / "score")
    assert score["scope_passed"] is False
    assert score["changed_paths"] == []
    assert score["build_commands"] == []
    assert score["probe_commands"] == []
    assert score["passed"] is False


def test_modal_lane_is_bound_to_final_jsonl_and_historical_synthmem_v1() -> None:
    source = (REPO_ROOT / "examples/modal/public_pr_synthmem_v1_eval_app.py").read_text(
        encoding="utf-8"
    )
    assert EXPECTED_SHA256 in source
    assert DEMO_EXPECTED_SHA256 in source
    assert "fmtlib-demo" in source
    assert "glm47-synth-memorization-v1-100ep-20260731T071000Z" in source
    assert "block_network=True" in source
    assert "expected_adapter_config_sha256" in source
    assert "sglang-kernel==0.4.4" in source
    assert "https://docs.sglang.ai/whl/cu129/" in source
    assert '"seed": 1701' in source


def test_failure_diagnostics_compare_candidate_to_reference(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@invalid")
    production = repo / "production.cpp"
    production.write_text("int value() { return 0; }\n", encoding="utf-8")
    _git(repo, "add", "production.cpp")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "tag", BASELINE_TAG)
    production.write_text("int value() { return 2; }\n", encoding="utf-8")
    _git(repo, "commit", "-am", "reference")
    reference = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", base)
    production.write_text("int value() { return 1; }\n", encoding="utf-8")
    failed_log = tmp_path / "failed.log"
    failed_log.write_text("test failed: wrong value\n", encoding="utf-8")
    row = {
        "task_id": "synthetic-diagnostic-test",
        "repository": {"base_commit": base, "reference_commit": reference},
        "scope": {"editable_files": ["production.cpp"]},
        "hidden_validation": {"required_behaviors": ["returns two"]},
        "diagnostic_checklist": [
            {
                "id": "return-two",
                "change": "return two",
                "purpose": "detect the expected reference mechanism",
                "path": "production.cpp",
                "required_substrings": ["return 2"],
                "forbidden_substrings": ["return 0"],
            }
        ],
    }
    score = {
        "passed": False,
        "scope_passed": True,
        "changed_paths": ["production.cpp"],
        "build_commands": [
            {"name": "test-all", "returncode": 8, "log_path": str(failed_log)}
        ],
        "probe_commands": [],
    }
    receipt = write_attempt_diagnostics(
        row, repo, score, tmp_path / "diagnostics", aider_returncode=0
    )
    assert receipt["failure_class"] == "regression_test_failure"
    assert receipt["exact_upstream_reference_match"] is False
    assert receipt["files"][0]["missing_or_changed_reference_lines"] == 1
    assert receipt["solution_checklist"][0]["status"] == "missing"
    assert receipt["solution_checklist"][0]["missing_required_substrings"] == [
        "return 2"
    ]
    assert (tmp_path / "diagnostics/diagnostics.md").is_file()
    assert (tmp_path / "diagnostics/candidate-production.patch").is_file()


def test_demo_baseline_rejects_checklist_without_executable_oracle(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@invalid")
    production = repo / "production.cpp"
    production.write_text("int value() { return 0; }\n", encoding="utf-8")
    _git(repo, "add", "production.cpp")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "tag", BASELINE_TAG)
    production.write_text("int value() { return 2; }\n", encoding="utf-8")
    _git(repo, "commit", "-am", "reference")
    reference = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", base)
    production.write_text("int value() { return 2; }\n", encoding="utf-8")
    failed_log = tmp_path / "failed.log"
    failed_log.write_text(
        "compile failed after near-reference implementation\n", encoding="utf-8"
    )
    row = {
        "task_id": "synthetic-diagnostic-test",
        "repository": {"base_commit": base, "reference_commit": reference},
        "scope": {"editable_files": ["production.cpp"]},
        "hidden_validation": {"required_behaviors": ["returns two"]},
        "demo_evaluation_policy": {
            "minimum_present_checklist_items": 9,
            "minimum_line_similarity_ratio": 0.75,
        },
        "diagnostic_checklist": [
            {
                "id": f"check-{index}",
                "change": "return two",
                "purpose": "demo baseline coverage",
                "path": "production.cpp",
                "required_substrings": ["return 2"] if index < 9 else ["missing_token"],
                "forbidden_substrings": [],
            }
            for index in range(11)
        ],
    }
    score = {
        "passed": False,
        "scope_passed": True,
        "changed_paths": ["production.cpp"],
        "build_commands": [
            {"name": "build-all", "returncode": 2, "log_path": str(failed_log)}
        ],
        "probe_commands": [],
    }
    receipt = write_attempt_diagnostics(
        row, repo, score, tmp_path / "baseline-diagnostics", aider_returncode=0
    )
    assert receipt["passed"] is False
    assert receipt["demo_baseline"]["passed"] is False
    assert receipt["demo_baseline"]["reason"] == "executable_oracle_failed"
    assert receipt["demo_baseline"]["textual_hints"]["present"] == 9
    assert receipt["demo_baseline"]["textual_hints"]["status"] == "diagnostic_only"


def test_gcp_lane_is_exactly_bound_and_offline() -> None:
    runtime = (REPO_ROOT / "scripts/gcp_public_pr_synthmem_50ep_eval.py").read_text(
        encoding="utf-8"
    )
    dockerfile = (REPO_ROOT / "docker/public-pr-synthmem-gcp/Dockerfile").read_text(
        encoding="utf-8"
    )
    launcher = (REPO_ROOT / "scripts/gcp_public_pr_eval_run.sh").read_text(
        encoding="utf-8"
    )
    assert "glm47-synth-mem-v3-v1std-50ep-20260803T023833Z" in runtime
    assert "5ca6a0cbede843e8c042ebb1004a80e85d85686974063cb9bd0540e236aab6ca" in runtime
    assert "exactly four GPUs are required" in runtime
    assert 'interfaces != {"lo"}' in runtime
    assert "verify-oracles" in dockerfile
    assert "public-pr-repo-eval-v2-r5.jsonl" in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v2.jsonl" in dockerfile
    assert "public-pr-repo-eval-demo-fmtlib-v3.jsonl" in dockerfile
    assert COMPILER_REPAIR_EXPECTED_SHA256 in dockerfile
    assert EXPECTED_SHA256 in dockerfile
    assert DEMO_EXPECTED_SHA256 in dockerfile
    assert "fmtlib-demo" in runtime
    assert "fmtlib-compiler-repair" in runtime
    assert '"repair_temperature": 0.2' in runtime
    assert "repair_model_settings=repair_settings" in runtime
    assert '"edit_format": "diff"' in runtime
    assert 'default="fmtlib-verified-mechanisms-thinking"' in runtime
    assert "write_model_settings(" in runtime
    assert 'temperature=float(suite_config.get("repair_temperature", 0.7))' in runtime
    assert 'SUITE="${SUITE:-fmtlib-verified-mechanisms-thinking}"' in launcher
    assert '--suite "${SUITE}"' in launcher
    assert "--network none" in launcher
    assert "--gpus all" in launcher
    assert "a2-ultragpu-4g" in launcher
