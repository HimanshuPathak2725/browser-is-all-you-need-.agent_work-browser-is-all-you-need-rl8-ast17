from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from glm47_posttraining.cpp_perf.sandbox import SandboxInfrastructureError

from glm47_posttraining.aider_polyglot.schema import (
    AiderPolyglotTask,
    AiderTestResult,
    WEIGHTED45_HARNESS_CHECK_IDS,
)
from glm47_posttraining.aider_polyglot.validator.oracle import (
    OracleCertificationError,
    OracleCertificationReceipt,
    OracleReceiptCache,
    assert_receipt_integrity,
    certify_task_oracle,
    load_reference_solution,
    require_certified_oracle,
)


def _exercise(tmp_path: Path) -> tuple[Path, AiderPolyglotTask, str]:
    exercise = tmp_path / "example"
    reference = exercise / ".reference"
    reference.mkdir(parents=True)
    header = "example.h"
    source = "example.cpp"
    hidden_name = "example_test.cpp"
    (exercise / header).write_text("#pragma once\nint answer();\n", encoding="utf-8")
    (exercise / source).write_text(
        '#include "example.h"\nint answer() { return 0; }\n', encoding="utf-8"
    )
    (reference / header).write_text("#pragma once\nint answer();\n", encoding="utf-8")
    (reference / source).write_text(
        '#include "example.h"\nint answer() { return 42; }\n', encoding="utf-8"
    )
    hidden = (
        '#include "example.h"\nint main() {\n'
        " if (answer() != 42) return 1;\n"
        " if (answer() < 0) return 2;\n"
        " if (answer() > 100) return 3;\n"
        " if (answer() % 2 != 0) return 4;\n"
        " if (answer() != answer()) return 5;\n"
        " return 0;\n}\n"
    )
    (exercise / hidden_name).write_text(hidden, encoding="utf-8")
    hidden_hash = hashlib.sha256(hidden.encode()).hexdigest()
    task = AiderPolyglotTask(
        task_id="aider-shadow-cpp/example",
        exercise="example",
        split="train",
        harness_kind="shadow_cpp17",
        exercise_dir="shadow/example",
        editable_files=[header, source],
        prompt=[{"role": "user", "content": "implement answer"}],
        hidden_test_sha256=hidden_hash,
        source_prompt_sha256="a" * 64,
    )
    return exercise, task, hidden_name


def _passing_harness(
    workspace: Path,
    files: dict[str, str],
    standard: str,
    expected_hash: str,
) -> AiderTestResult:
    assert standard in {"c++17", "c++20"}
    assert not (workspace / ".reference").exists()
    assert hashlib.sha256((workspace / ".grader" / "test.cpp").read_bytes()).hexdigest() == (
        expected_hash
    )
    assert set(files) == {"example.h", "example.cpp"}
    checks = {check_id: True for check_id in WEIGHTED45_HARNESS_CHECK_IDS}
    return AiderTestResult(
        status="passed",
        tests_passed=5,
        tests_total=5,
        candidate_returncode=0,
        weighted45_checks=checks,
        weighted45_evidence={check_id: "unit pass" for check_id in checks},
    )


def test_oracle_certifies_three_perfect_runs_under_cpp17_and_cpp20(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)
    calls: list[str] = []

    def runner(*args):
        calls.append(args[2])
        return _passing_harness(*args)

    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=runner
    )

    assert receipt.status == "certified"
    assert calls == ["c++17"] * 3 + ["c++20"] * 3
    assert len(receipt.runs) == 6
    assert all(run.reward == 1.0 for run in receipt.runs)
    assert all(rule.passed for rule in receipt.rules)
    assert_receipt_integrity(receipt)
    require_certified_oracle(receipt)


def test_oracle_rejects_any_nonperfect_weighted45_run(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)

    def imperfect(workspace, files, standard, expected_hash):
        result = _passing_harness(workspace, files, standard, expected_hash)
        checks = dict(result.weighted45_checks)
        checks["H5"] = False
        checks["A5"] = False
        return result.model_copy(
            update={
                "status": "tests_failed",
                "tests_passed": 4,
                "weighted45_checks": checks,
            }
        )

    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=imperfect
    )

    assert receipt.status == "rejected"
    assert {"ORC-012", "ORC-013", "ORC-016"} <= set(receipt.failed_rule_ids)
    with pytest.raises(OracleCertificationError, match="ORC-012"):
        require_certified_oracle(receipt)


def test_oracle_rejects_nondeterministic_repeated_outcomes(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)
    calls = 0

    def flaky(workspace, files, standard, expected_hash):
        nonlocal calls
        calls += 1
        result = _passing_harness(workspace, files, standard, expected_hash)
        if calls != 2:
            return result
        checks = dict(result.weighted45_checks)
        checks["H1"] = False
        checks["A5"] = False
        return result.model_copy(
            update={
                "status": "tests_failed",
                "tests_passed": 4,
                "weighted45_checks": checks,
            }
        )

    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=flaky
    )

    assert receipt.status == "rejected"
    assert "ORC-015" in receipt.failed_rule_ids


def test_oracle_rejects_missing_or_extra_reference_files(tmp_path: Path) -> None:
    exercise, task, _hidden_name = _exercise(tmp_path)
    (exercise / ".reference" / "extra.cpp").write_text("int extra;\n", encoding="utf-8")

    files, rules = load_reference_solution(exercise, task.editable_files)

    assert files == {}
    failed = {rule.rule_id for rule in rules if not rule.passed}
    assert "ORC-002" in failed


def test_oracle_cache_is_bound_to_inputs_and_avoids_reexecution(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)
    cache = OracleReceiptCache(tmp_path / "cache")
    calls = 0

    def runner(*args):
        nonlocal calls
        calls += 1
        return _passing_harness(*args)

    first = certify_task_oracle(
        task, exercise, hidden_name, cache=cache, harness_runner=runner
    )
    second = certify_task_oracle(
        task, exercise, hidden_name, cache=cache, harness_runner=runner
    )

    assert first.certification_sha256 == second.certification_sha256
    assert calls == 6

    (exercise / ".reference" / "example.cpp").write_text(
        '#include "example.h"\nint answer() { return 43; }\n', encoding="utf-8"
    )
    certify_task_oracle(task, exercise, hidden_name, cache=cache, harness_runner=runner)
    assert calls == 12


def test_oracle_certification_digest_detects_semantic_receipt_tampering(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)
    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=_passing_harness
    )
    mutated_run = receipt.runs[0].model_copy(update={"reason": "tampered"})
    mutated = receipt.model_copy(update={"runs": (mutated_run, *receipt.runs[1:])})

    with pytest.raises(ValueError, match="certification SHA-256 mismatch"):
        assert_receipt_integrity(mutated)


def test_oracle_run_receipt_rejects_a_forged_check_digest(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)
    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=_passing_harness
    )
    payload = receipt.model_dump(mode="json")
    payload["runs"][0]["checks_sha256"] = "f" * 64

    with pytest.raises(ValueError, match="oracle checks SHA-256 mismatch"):
        OracleCertificationReceipt.model_validate(payload)


def test_oracle_receipt_preserves_infrastructure_failure_evidence(tmp_path: Path) -> None:
    exercise, task, hidden_name = _exercise(tmp_path)

    def unavailable(*_args):
        raise SandboxInfrastructureError("bwrap namespace unavailable")

    receipt = certify_task_oracle(
        task, exercise, hidden_name, harness_runner=unavailable
    )

    assert receipt.status == "rejected"
    assert all(run.infrastructure_error for run in receipt.runs)
    assert {run.infrastructure_detail for run in receipt.runs} == {
        "bwrap namespace unavailable"
    }
    orc_010 = next(rule for rule in receipt.rules if rule.rule_id == "ORC-010")
    assert "bwrap namespace unavailable" in orc_010.evidence
