"""Pass@1-aligned reward for Aider-style shadow tasks and official evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path, PurePath
import re
from typing import Callable

from glm47_posttraining.cpp_perf.sandbox import SandboxInfrastructureError

from .ast_evaluator import AST17Evaluation, compute_ast17_score
from .harness import CandidatePolicyError, run_aider_tests
from .parser import AiderResponseError, ParsedAiderResponse, parse_whole_file_response
from .schema import AiderPolyglotTask, AiderTestResult


Runner = Callable[[Path, dict[str, str]], AiderTestResult]
FORBIDDEN_VIOLATION_REASON = "forbidden_file_or_primitive_violation"
CLARIFICATION_OR_NO_FILE_REASON = "clarification_or_no_file_output"
FATAL_PARSE_REASON = "fatal_parse_failure"
DUPLICATE_FILE_REASON = "duplicate_file"
WRONG_FILE_LABEL_REASON = "wrong_file_label"
COMPILATION_FAILURE_REASON = "compilation_failure"
COMPILATION_FAILURE_SYNTAX_REASON = "compilation_failure_syntax"
COMPILATION_FAILURE_MISSING_SYMBOL_REASON = "compilation_failure_missing_symbol"
COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REASON = "compilation_failure_missing_include_or_type"
COMPILATION_FAILURE_API_MISMATCH_REASON = "compilation_failure_api_mismatch"
COMPILATION_FAILURE_LINKER_REASON = "compilation_failure_linker"
COMPILATION_FAILURE_WARNING_REASON = "compilation_failure_warning"
SANITIZER_ERROR_REASON = "sanitizer_error"
CANDIDATE_TIMEOUT_REASON = "candidate_timeout"
INFRASTRUCTURE_FAULT_REASON = "infrastructure_fault"
PARTIAL_TEST_PASS_REASON = "partial_test_pass"
RUNTIME_ZERO_PASS_REASON = "runtime_zero_pass"
FORBIDDEN_REWARD = -1.0
CLARIFICATION_OR_NO_FILE_REWARD = -0.92
FATAL_PARSE_REWARD = -0.85
DUPLICATE_FILE_REWARD = -0.70
WRONG_FILE_LABEL_REWARD = -0.75
COMPILATION_FAILURE_REWARD = -0.5
COMPILATION_FAILURE_SYNTAX_REWARD = -0.55
COMPILATION_FAILURE_MISSING_SYMBOL_REWARD = -0.50
COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REWARD = -0.45
COMPILATION_FAILURE_API_MISMATCH_REWARD = -0.42
COMPILATION_FAILURE_LINKER_REWARD = -0.38
COMPILATION_FAILURE_WARNING_REWARD = -0.32
SANITIZER_ERROR_REWARD = -0.5
CANDIDATE_TIMEOUT_REWARD = -0.5
INFRASTRUCTURE_MASK_REWARD = 0.0
FULL_PASS_REWARD_FLOOR = 0.85
PARTIAL_TEST_BASE = 0.15
PARTIAL_TEST_SCALE = 0.6
EPS = 1e-9
PROTECTED_NAMES = {"CMakeLists.txt"}
PROTECTED_SUFFIXES = ("_test.cpp", "_test.cc", "_test.h", ".cmake")
SANITIZER_ERROR_MARKERS = (
    "addresssanitizer",
    "undefinedbehaviorsanitizer",
    "leaksanitizer",
    "runtime error:",
    "heap-buffer-overflow",
    "stack-buffer-overflow",
    "use-after-free",
)
COMPILE_WARNING_MARKERS = (
    "-werror",
    "warnings being treated as errors",
    "warning:",
    "unused variable",
    "unused parameter",
    "sign-compare",
    "reorder",
)
COMPILE_LINKER_MARKERS = (
    "undefined reference",
    "multiple definition",
    "ld returned",
    "collect2:",
    "duplicate symbol",
)
COMPILE_API_MISMATCH_MARKERS = (
    "no matching function",
    "candidate expects",
    "too few arguments",
    "too many arguments",
    "invalid conversion",
    "cannot convert",
    "ambiguous",
    "discard qualifiers",
    "passing",
)
COMPILE_MISSING_INCLUDE_OR_TYPE_MARKERS = (
    "no such file or directory",
    "has not been declared",
    "was not declared in this scope",
    "does not name a type",
    "unknown type name",
    "incomplete type",
)
COMPILE_MISSING_SYMBOL_MARKERS = (
    "not declared",
    "not a member",
    "no member named",
    "use of undeclared identifier",
)
COMPILE_SYNTAX_MARKERS = (
    "expected",
    "stray",
    "unterminated",
    "parse error",
    "invalid declarator",
    "expected initializer",
)
CPP_STRUCTURE_RE = re.compile(
    r"\b(?:class|struct|enum|template|std::|auto|constexpr|const|return|for|while|if)\b"
)
RAW_NEW_RE = re.compile(r"\bnew\s+(?!\()")
RAW_DELETE_RE = re.compile(r"\bdelete(?:\s*\[\s*\])?\s+")
MUTABLE_GLOBAL_RE = re.compile(
    r"(?m)^\s*(?:static\s+)?(?!const\b)(?:[A-Za-z_][\w:<>,\s*&]+\s+)"
    r"[A-Za-z_]\w*\s*(?:=|\{)"
)
CONST_REF_RE = re.compile(r"\b(?:const\s+[A-Za-z_:][\w:<>,\s]*\s*&|std::string_view)\b")


@dataclass(frozen=True)
class AiderRewardBreakdown:
    reward: float
    reason: str
    parsed: ParsedAiderResponse | None = None
    harness: AiderTestResult | None = None
    infrastructure_error: bool = False


@dataclass(frozen=True)
class ProductionAiderRewardBreakdown(AiderRewardBreakdown):
    """Production Aider reward with AST17/style/bloat telemetry."""

    s_aider: float = 0.0
    s_ast17: float = 0.0
    s_style: float = 0.0
    anti_bloat: float = 0.0
    line_count: int = 0
    ast17_checks: dict[str, float] | None = None


def compute_aider_reward(
    task: AiderPolyglotTask,
    exercise_dir: Path,
    model_output: str,
    *,
    runner: Runner | None = None,
) -> AiderRewardBreakdown:
    """Score correctness first and use formatting only as a small tie-breaker."""

    try:
        parsed = parse_whole_file_response(model_output, task.editable_files)
    except AiderResponseError as exc:
        reward = -1.0 if exc.reason == "forbidden_file" else -0.8
        return AiderRewardBreakdown(reward=reward, reason=exc.reason)

    try:
        harness = (runner or run_aider_tests)(exercise_dir, parsed.files)
    except CandidatePolicyError:
        return AiderRewardBreakdown(
            reward=-1.0,
            reason="forbidden_runtime_primitive",
            parsed=parsed,
        )

    if harness.status == "infrastructure_error":
        raise SandboxInfrastructureError(
            harness.logs.get("error", "Aider verifier reported an infrastructure error")
        )

    semantic = {
        "compile_failed": -0.5,
        "candidate_timeout": -0.5,
    }.get(harness.status)
    if semantic is None:
        semantic = 1.0 if harness.all_tests_pass else 0.6 * harness.fraction_tests_passed

    format_penalty = 0.0 if parsed.format_valid else 0.1
    reward = max(-1.0, min(1.0, semantic - format_penalty))
    reason = "passed" if harness.all_tests_pass else harness.status
    if not parsed.format_valid:
        reason = f"recoverable_format_{reason}"
    return AiderRewardBreakdown(reward=reward, reason=reason, parsed=parsed, harness=harness)


def compute_production_aider_reward(
    task: AiderPolyglotTask,
    exercise_dir: Path,
    model_output: str,
    *,
    runner: Runner | None = None,
) -> ProductionAiderRewardBreakdown:
    """Production reward behind the remote Aider parser/harness contract.

    Endpoint policy:
    - forbidden file/runtime primitive: -1.0
    - no-file/clarification output: -0.92
    - fatal parse failure: -0.85
    - duplicate/wrong file label: -0.70/-0.75
    - compile failure: diagnostic-shaped -0.55..-0.30
    - timeout/sanitizer failure: -0.5
    - infrastructure fault: 0.0 with ``infrastructure_error=True``
    - runtime zero-pass: 0.05..0.12
    - partial tests: shaped ``0.15 + 0.60*S_Aider + small bounded bonuses``
    - full pass: ``max(0.85, 0.90 + small AST/style/format bonuses - capped bloat)``
    """

    try:
        parsed = parse_whole_file_response(model_output, task.editable_files)
    except AiderResponseError as exc:
        reward, reason = _parse_failure_reward(exc, model_output)
        return ProductionAiderRewardBreakdown(
            reward=reward,
            reason=reason,
        )

    try:
        harness = (runner or run_aider_tests)(exercise_dir, parsed.files)
    except CandidatePolicyError:
        return ProductionAiderRewardBreakdown(
            reward=FORBIDDEN_REWARD,
            reason=FORBIDDEN_VIOLATION_REASON,
            parsed=parsed,
        )
    except SandboxInfrastructureError as exc:
        return ProductionAiderRewardBreakdown(
            reward=INFRASTRUCTURE_MASK_REWARD,
            reason=INFRASTRUCTURE_FAULT_REASON,
            parsed=parsed,
            infrastructure_error=True,
            ast17_checks={"error": 0.0},
        )

    if harness.status == "infrastructure_error":
        return ProductionAiderRewardBreakdown(
            reward=INFRASTRUCTURE_MASK_REWARD,
            reason=INFRASTRUCTURE_FAULT_REASON,
            parsed=parsed,
            harness=harness,
            infrastructure_error=True,
        )

    if harness.status == "compile_failed":
        reward, reason = _compile_failure_reward(harness, parsed, task)
        return ProductionAiderRewardBreakdown(
            reward=reward,
            reason=_format_sensitive_reason(parsed, reason),
            parsed=parsed,
            harness=harness,
            s_ast17=0.0,
            s_style=_cpp_quality_score(parsed.files),
        )
    if harness.status == "candidate_timeout":
        return ProductionAiderRewardBreakdown(
            reward=CANDIDATE_TIMEOUT_REWARD,
            reason=CANDIDATE_TIMEOUT_REASON,
            parsed=parsed,
            harness=harness,
        )
    if harness.status == "sanitizer_error" or _harness_has_sanitizer_error(harness):
        return ProductionAiderRewardBreakdown(
            reward=SANITIZER_ERROR_REWARD,
            reason=SANITIZER_ERROR_REASON,
            parsed=parsed,
            harness=harness,
        )

    s_aider = max(0.0, min(1.0, harness.fraction_tests_passed))
    format_score = _aider_format_score(parsed)
    mechanism_score = _mechanism_score(task, parsed)
    cpp_quality = _cpp_quality_score(parsed.files)
    if not harness.all_tests_pass:
        if harness.tests_passed <= 0:
            reward = 0.05 + 0.07 * format_score + 0.05 * mechanism_score
            return ProductionAiderRewardBreakdown(
                reward=round(min(0.12, reward), 4),
                reason=_format_sensitive_reason(parsed, RUNTIME_ZERO_PASS_REASON),
                parsed=parsed,
                harness=harness,
                s_aider=s_aider,
                s_style=cpp_quality,
            )
        reward = (
            PARTIAL_TEST_BASE
            + PARTIAL_TEST_SCALE * s_aider
            + 0.06 * format_score
            + 0.05 * mechanism_score
            + 0.03 * cpp_quality
        )
        return ProductionAiderRewardBreakdown(
            reward=round(min(0.80, reward), 4),
            reason=_format_sensitive_reason(parsed, PARTIAL_TEST_PASS_REASON),
            parsed=parsed,
            harness=harness,
            s_aider=s_aider,
            s_style=cpp_quality,
        )

    line_count = _candidate_line_count(parsed.files)
    ast_eval = compute_ast17_score(
        parsed.files,
        sanitizer_report=_combined_harness_logs(harness),
        return_details=True,
    )
    if isinstance(ast_eval, AST17Evaluation):
        s_ast17 = ast_eval.score
        ast_checks = ast_eval.checks
    else:
        s_ast17 = float(ast_eval)
        ast_checks = {}
    s_style = cpp_quality
    anti_bloat = min(0.08, 0.02 * math.sqrt(max(0, line_count - 50)))
    reward = 0.90 + 0.04 * s_ast17 + 0.03 * s_style + 0.02 * format_score - anti_bloat
    reward = max(FULL_PASS_REWARD_FLOOR, min(1.0, reward))
    return ProductionAiderRewardBreakdown(
        reward=round(reward, 4),
        reason=_format_sensitive_reason(parsed, "correct"),
        parsed=parsed,
        harness=harness,
        s_aider=s_aider,
        s_ast17=s_ast17,
        s_style=s_style,
        anti_bloat=anti_bloat,
        line_count=line_count,
        ast17_checks=ast_checks,
    )


def _parse_failure_reward(exc: AiderResponseError, response: str) -> tuple[float, str]:
    if exc.reason == "forbidden_file":
        target = _extract_target_from_error(exc)
        if _is_protected_or_escape_target(target):
            return FORBIDDEN_REWARD, FORBIDDEN_VIOLATION_REASON
        return WRONG_FILE_LABEL_REWARD, WRONG_FILE_LABEL_REASON
    if exc.reason == "duplicate_file":
        return DUPLICATE_FILE_REWARD, DUPLICATE_FILE_REASON
    if _has_no_usable_file_output(response):
        return CLARIFICATION_OR_NO_FILE_REWARD, CLARIFICATION_OR_NO_FILE_REASON
    return FATAL_PARSE_REWARD, FATAL_PARSE_REASON


def _extract_target_from_error(exc: AiderResponseError) -> str:
    marker = "response targets non-editable file:"
    message = str(exc)
    if marker not in message:
        return ""
    return message.split(marker, 1)[1].strip()


def _is_protected_or_escape_target(target: str) -> bool:
    if not target:
        return True
    path = PurePath(target)
    if path.is_absolute() or ".." in path.parts:
        return True
    return target in PROTECTED_NAMES or target.endswith(PROTECTED_SUFFIXES)


def _has_no_usable_file_output(response: str) -> bool:
    stripped = response.strip().lower()
    if "```" not in response:
        return True
    clarification_markers = (
        "clarify",
        "clarification",
        "could you provide",
        "please provide",
        "i need more",
        "need more information",
    )
    return bool(stripped) and any(marker in stripped for marker in clarification_markers)


def _compile_failure_reward(
    harness: AiderTestResult, parsed: ParsedAiderResponse, task: AiderPolyglotTask
) -> tuple[float, str]:
    base_reward, reason = _classify_compile_failure(harness)
    if reason == COMPILATION_FAILURE_SYNTAX_REASON:
        return base_reward, reason
    reward = base_reward + _compile_format_adjustment(parsed) + 0.05 * _mechanism_score(task, parsed)
    return round(max(-0.65, min(-0.30, reward)), 4), reason


def _classify_compile_failure(harness: AiderTestResult) -> tuple[float, str]:
    logs = _combined_harness_logs(harness).lower()
    if _contains_any(logs, COMPILE_LINKER_MARKERS):
        return COMPILATION_FAILURE_LINKER_REWARD, COMPILATION_FAILURE_LINKER_REASON
    if _contains_any(logs, COMPILE_API_MISMATCH_MARKERS):
        return COMPILATION_FAILURE_API_MISMATCH_REWARD, COMPILATION_FAILURE_API_MISMATCH_REASON
    if _contains_any(logs, COMPILE_MISSING_INCLUDE_OR_TYPE_MARKERS):
        return (
            COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REWARD,
            COMPILATION_FAILURE_MISSING_INCLUDE_OR_TYPE_REASON,
        )
    if _contains_any(logs, COMPILE_MISSING_SYMBOL_MARKERS):
        return COMPILATION_FAILURE_MISSING_SYMBOL_REWARD, COMPILATION_FAILURE_MISSING_SYMBOL_REASON
    if _contains_any(logs, COMPILE_SYNTAX_MARKERS):
        return COMPILATION_FAILURE_SYNTAX_REWARD, COMPILATION_FAILURE_SYNTAX_REASON
    if _contains_any(logs, COMPILE_WARNING_MARKERS):
        return COMPILATION_FAILURE_WARNING_REWARD, COMPILATION_FAILURE_WARNING_REASON
    return COMPILATION_FAILURE_REWARD, COMPILATION_FAILURE_REASON


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _compile_format_adjustment(parsed: ParsedAiderResponse) -> float:
    return 0.03 if parsed.format_valid else -0.05


def _aider_format_score(parsed: ParsedAiderResponse) -> float:
    return 1.0 if parsed.format_valid else 0.5


def _format_sensitive_reason(parsed: ParsedAiderResponse, reason: str) -> str:
    return reason if parsed.format_valid else f"recoverable_format_{reason}"


def _mechanism_score(task: AiderPolyglotTask, parsed: ParsedAiderResponse) -> float:
    combined = "\n".join(parsed.files.values())
    expected_files = set(task.editable_files)
    observed_files = set(parsed.files)
    checks = [
        bool(observed_files),
        expected_files.issubset(observed_files),
        bool(CPP_STRUCTURE_RE.search(combined)),
        _candidate_line_count(parsed.files) >= 1,
    ]
    return sum(checks) / len(checks)


def _cpp_quality_score(files: dict[str, str]) -> float:
    combined = "\n".join(files.values())
    line_count = _candidate_line_count(files)
    checks = [
        "using namespace std" not in combined,
        not RAW_NEW_RE.search(combined) and not RAW_DELETE_RE.search(combined),
        not MUTABLE_GLOBAL_RE.search(_remove_class_bodies(combined)),
        bool(CONST_REF_RE.search(combined)) or line_count <= 30,
    ]
    return sum(checks) / len(checks)


def _remove_class_bodies(source: str) -> str:
    return re.sub(r"\b(?:class|struct)\s+\w+[^{}]*\{.*?\};", "", source, flags=re.DOTALL)


def _candidate_line_count(files: dict[str, str]) -> int:
    return sum(1 for contents in files.values() for line in contents.splitlines() if line.strip())


def _combined_harness_logs(harness: AiderTestResult) -> str:
    return "\n".join(str(value) for value in harness.logs.values())


def _harness_has_sanitizer_error(harness: AiderTestResult) -> bool:
    logs = _combined_harness_logs(harness).lower()
    return any(marker in logs for marker in SANITIZER_ERROR_MARKERS)
