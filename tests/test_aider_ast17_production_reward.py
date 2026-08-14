from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from glm47_posttraining.aider_polyglot.ast_evaluator import (
    AST17_CHECK_WEIGHTS,
    AST17Evaluation,
    _libclang_resource_args,
    compute_ast17_score,
)
from glm47_posttraining.aider_polyglot.reward import (
    CLARIFICATION_OR_NO_FILE_REASON,
    COMPILATION_FAILURE_REASON,
    COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REASON,
    COMPILATION_FAILURE_SYNTAX_REASON,
    COMPILATION_FAILURE_WARNING_REASON,
    DUPLICATE_FILE_REASON,
    FATAL_PARSE_REASON,
    FORBIDDEN_VIOLATION_REASON,
    PARTIAL_TEST_PASS_REASON,
    RUNTIME_ZERO_PASS_REASON,
    SANITIZER_ERROR_REASON,
    WRONG_FILE_LABEL_REASON,
    compute_production_aider_reward,
)
from glm47_posttraining.aider_polyglot.parser import segment_glm47_response
from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask, AiderTestResult


def test_libclang_resource_directory_is_explicit_and_validated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resource_dir = tmp_path / "clang" / "18"
    include_dir = resource_dir / "include"
    include_dir.mkdir(parents=True)
    (include_dir / "stddef.h").write_text("/* built-in */\n", encoding="utf-8")
    monkeypatch.setenv("GLM47_LIBCLANG_RESOURCE_DIR", str(resource_dir))

    assert _libclang_resource_args() == [f"-resource-dir={resource_dir}"]


def test_libclang_resource_directory_rejects_missing_builtin_headers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resource_dir = tmp_path / "clang" / "18"
    resource_dir.mkdir(parents=True)
    monkeypatch.setenv("GLM47_LIBCLANG_RESOURCE_DIR", str(resource_dir))

    with pytest.raises(RuntimeError, match="include/stddef.h"):
        _libclang_resource_args()


def _task() -> AiderPolyglotTask:
    return AiderPolyglotTask(
        task_id="aider-shadow-cpp/example",
        exercise="example",
        split="train",
        harness_kind="shadow_cpp17",
        exercise_dir="shadow/example",
        editable_files=["example.cpp"],
        prompt=[{"role": "user", "content": "solve"}],
    )


def _response(code: str, label: str = "example.cpp") -> str:
    return f"{label}\n```cpp\n{code.rstrip()}\n```\n"


def test_ast17_weights_are_the_declared_five_check_policy() -> None:
    assert AST17_CHECK_WEIGHTS == {
        "raii": 0.30,
        "encapsulation": 0.25,
        "const_correctness": 0.20,
        "density": 0.15,
        "sanitizer": 0.10,
    }
    assert sum(AST17_CHECK_WEIGHTS.values()) == pytest.approx(1.0)


def test_ast17_rewards_raii_and_const_correctness() -> None:
    result = compute_ast17_score(
        """
        #include <memory>
        #include <string>
        class Holder {
        public:
            explicit Holder(std::string_view name) : name_(name) {}
            int value() const { return 1; }
        private:
            std::string_view name_;
            std::unique_ptr<int> owned_;
        };
        """
    )
    assert isinstance(result, AST17Evaluation)
    assert result.checks["raii"] == 1.0
    assert result.checks["const_correctness"] == 1.0
    assert -1.0 <= result.score <= 1.0


def test_ast17_penalizes_raw_allocation_and_sanitizer_reports() -> None:
    result = compute_ast17_score(
        "int *bad(){ return new int(1); }\n",
        sanitizer_report="ERROR: AddressSanitizer: heap-buffer-overflow",
    )
    assert isinstance(result, AST17Evaluation)
    assert result.checks["raii"] == -1.0
    assert result.checks["sanitizer"] == -1.0
    assert result.score < 0.5


def test_production_reward_rejects_forbidden_file_without_runner(tmp_path: Path) -> None:
    called = False

    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        nonlocal called
        called = True
        return AiderTestResult(status="passed", tests_passed=1, tests_total=1)

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}", "example_test.cpp"), runner=runner
    )
    assert (result.reward, result.reason, called) == (-1.0, FORBIDDEN_VIOLATION_REASON, False)


def test_production_reward_applies_only_segmented_final_files(tmp_path: Path) -> None:
    observed: list[dict[str, str]] = []

    def runner(_path: Path, files: dict[str, str]) -> AiderTestResult:
        observed.append(files)
        return AiderTestResult(status="passed", tests_passed=1, tests_total=1)

    raw = (
        _response("int answer(){return 0;}")
        + _response("project(unsafe)", "CMakeLists.txt")
        + "</think>\n"
        + _response("int answer(){return 42;}")
    )
    segments = segment_glm47_response(raw)
    result = compute_production_aider_reward(
        _task(), tmp_path, segments.final_answer, runner=runner
    )

    assert segments.thinking_boundary_applied is True
    assert observed == [{"example.cpp": "int answer(){return 42;}\n"}]
    assert result.parsed is not None
    assert result.parsed.format_valid is True


def test_production_reward_parse_failure_is_negative(tmp_path: Path) -> None:
    result = compute_production_aider_reward(_task(), tmp_path, "no file block", runner=None)
    assert (result.reward, result.reason) == (-0.92, CLARIFICATION_OR_NO_FILE_REASON)


def test_production_reward_single_unlabelled_fence_is_recoverable(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(status="passed", tests_passed=1, tests_total=1)

    result = compute_production_aider_reward(
        _task(), tmp_path, "```cpp\nint answer(){return 42;}\n```", runner=runner
    )
    assert (result.reward, result.reason) == (1.0, "recoverable_format_correct")
    assert result.parsed is not None and result.parsed.format_valid is False


def test_production_reward_wrong_file_label_is_recoverable_negative(tmp_path: Path) -> None:
    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}", "solution.cpp"), runner=None
    )
    assert (result.reward, result.reason) == (-0.75, WRONG_FILE_LABEL_REASON)


def test_production_reward_nested_wrong_file_label_is_not_security_floor(
    tmp_path: Path,
) -> None:
    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}", "src/solution.cpp"), runner=None
    )
    assert (result.reward, result.reason) == (-0.75, WRONG_FILE_LABEL_REASON)


def test_production_reward_duplicate_file_is_recoverable_negative(tmp_path: Path) -> None:
    result = compute_production_aider_reward(
        _task(),
        tmp_path,
        _response("int answer(){return 42;}") + "\n" + _response("int answer(){return 43;}"),
        runner=None,
    )
    assert (result.reward, result.reason) == (-0.70, DUPLICATE_FILE_REASON)


def test_production_reward_compile_failure_is_hard_negative(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(status="compile_failed")

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}"), runner=runner
    )
    assert (result.reward, result.reason) == (pytest.approx(-0.42), COMPILATION_FAILURE_REASON)


def test_production_reward_recoverable_format_prefixes_compile_bucket(
    tmp_path: Path,
) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(status="compile_failed")

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}", "src/example.cpp"), runner=runner
    )
    assert result.reward == pytest.approx(-0.50)
    assert result.reason == "recoverable_format_compilation_failure"
    assert result.parsed is not None
    assert result.parsed.format_valid is False


def test_production_reward_compile_failure_syntax_stays_low(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(
            status="compile_failed",
            logs={"compile": "example.cpp:1:12: error: expected ';' before '}' token"},
        )

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42}"), runner=runner
    )
    assert (result.reward, result.reason) == (-0.55, COMPILATION_FAILURE_SYNTAX_REASON)


def test_production_reward_compile_failure_missing_include_is_shaped(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(
            status="compile_failed",
            logs={"compile": "fatal error: missing.hpp: No such file or directory"},
        )

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}"), runner=runner
    )
    assert (result.reward, result.reason) == (
        pytest.approx(-0.37),
        COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REASON,
    )


def test_production_reward_compile_failure_warning_is_near_compile(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(
            status="compile_failed",
            logs={"compile": "error: unused variable 'x' [-Werror=unused-variable]"},
        )

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){int x=0; return 42;}"), runner=runner
    )
    assert (result.reward, result.reason) == (
        pytest.approx(-0.30),
        COMPILATION_FAILURE_WARNING_REASON,
    )


def test_production_reward_sanitizer_marker_is_hard_negative(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(
            status="passed",
            tests_passed=1,
            tests_total=1,
            logs={"run": "ERROR: AddressSanitizer: stack-buffer-overflow"},
        )

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}"), runner=runner
    )
    assert (result.reward, result.reason) == (-0.5, SANITIZER_ERROR_REASON)


@pytest.mark.parametrize(
    ("tests_passed", "status", "expected_reward", "expected_reason"),
    [
        (0, "tests_failed", -0.20, RUNTIME_ZERO_PASS_REASON),
        (1, "tests_failed", 0.04, PARTIAL_TEST_PASS_REASON),
        (2, "tests_failed", 0.28, PARTIAL_TEST_PASS_REASON),
        (3, "tests_failed", 0.52, PARTIAL_TEST_PASS_REASON),
        (4, "tests_failed", 0.76, PARTIAL_TEST_PASS_REASON),
        (5, "passed", 1.00, "correct"),
    ],
)
def test_production_reward_is_continuous_across_five_test_cases(
    tmp_path: Path,
    tests_passed: int,
    status: Literal["tests_failed", "passed"],
    expected_reward: float,
    expected_reason: str,
) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(
            status=status,
            tests_passed=tests_passed,
            tests_total=5,
        )

    result = compute_production_aider_reward(
        _task(), tmp_path, _response("int answer(){return 42;}"), runner=runner
    )
    assert result.reward == pytest.approx(expected_reward)
    assert result.reason == expected_reason
    assert result.s_aider == pytest.approx(tests_passed / 5)


def test_production_reward_full_pass_includes_ast17_style_and_bloat(tmp_path: Path) -> None:
    def runner(_path: Path, _files: dict[str, str]) -> AiderTestResult:
        return AiderTestResult(status="passed", tests_passed=5, tests_total=5)

    code = """
    #include <memory>
    int answer() {
        auto value = std::make_unique<int>(42);
        return *value;
    }
    """
    result = compute_production_aider_reward(_task(), tmp_path, _response(code), runner=runner)
    assert result.reason == "correct"
    assert result.s_aider == 1.0
    assert -1.0 <= result.s_ast17 <= 1.0
    assert result.reward == 1.0
    assert result.anti_bloat == 0.0
