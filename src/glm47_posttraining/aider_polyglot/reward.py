"""Pass@1-aligned reward for Aider-style shadow tasks and official evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Callable

from glm47_posttraining.cpp_perf.sandbox import SandboxInfrastructureError

from .ast_evaluator import AST17Evaluation, compute_ast17_score
from .harness import CandidatePolicyError, run_aider_tests
from .parser import AiderResponseError, ParsedAiderResponse, parse_whole_file_response
from .schema import AiderPolyglotTask, AiderTestResult


Runner = Callable[[Path, dict[str, str]], AiderTestResult]
FORBIDDEN_VIOLATION_REASON = "forbidden_file_or_primitive_violation"
FATAL_PARSE_REASON = "fatal_parse_failure"
COMPILATION_FAILURE_REASON = "compilation_failure"
SANITIZER_ERROR_REASON = "sanitizer_error"
CANDIDATE_TIMEOUT_REASON = "candidate_timeout"
INFRASTRUCTURE_FAULT_REASON = "infrastructure_fault"
PARTIAL_TEST_PASS_REASON = "partial_test_pass"
FORBIDDEN_REWARD = -1.0
FATAL_PARSE_REWARD = -0.8
COMPILATION_FAILURE_REWARD = -0.5
SANITIZER_ERROR_REWARD = -0.5
CANDIDATE_TIMEOUT_REWARD = -0.5
INFRASTRUCTURE_MASK_REWARD = 0.0
PARTIAL_TEST_SCALE = 0.6
EPS = 1e-9
SANITIZER_ERROR_MARKERS = (
    "addresssanitizer",
    "undefinedbehaviorsanitizer",
    "leaksanitizer",
    "runtime error:",
    "heap-buffer-overflow",
    "stack-buffer-overflow",
    "use-after-free",
)


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
    - fatal parse failure: -0.8
    - compile/timeout/sanitizer failure: -0.5
    - infrastructure fault: 0.0 with ``infrastructure_error=True``
    - partial tests: ``0.6 * f``
    - full pass: ``clamp(0.80*S_Aider + 0.10*S_AST17 + 0.10*S_style - bloat, 0, 1)``
    """

    try:
        parsed = parse_whole_file_response(model_output, task.editable_files)
    except AiderResponseError as exc:
        if exc.reason == "forbidden_file":
            return ProductionAiderRewardBreakdown(
                reward=FORBIDDEN_REWARD,
                reason=FORBIDDEN_VIOLATION_REASON,
            )
        return ProductionAiderRewardBreakdown(
            reward=FATAL_PARSE_REWARD,
            reason=FATAL_PARSE_REASON,
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
        return ProductionAiderRewardBreakdown(
            reward=COMPILATION_FAILURE_REWARD,
            reason=COMPILATION_FAILURE_REASON,
            parsed=parsed,
            harness=harness,
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
    if not harness.all_tests_pass:
        return ProductionAiderRewardBreakdown(
            reward=round(PARTIAL_TEST_SCALE * s_aider, 4),
            reason=PARTIAL_TEST_PASS_REASON,
            parsed=parsed,
            harness=harness,
            s_aider=s_aider,
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
    s_style = s_ast17
    anti_bloat = 0.02 * math.sqrt(max(0, line_count - 50))
    reward = 0.80 * s_aider + 0.10 * s_ast17 + 0.10 * s_style - anti_bloat
    reward = max(0.0, min(1.0, reward))
    return ProductionAiderRewardBreakdown(
        reward=round(reward, 4),
        reason="correct",
        parsed=parsed,
        harness=harness,
        s_aider=s_aider,
        s_ast17=s_ast17,
        s_style=s_style,
        anti_bloat=anti_bloat,
        line_count=line_count,
        ast17_checks=ast_checks,
    )


def _candidate_line_count(files: dict[str, str]) -> int:
    return sum(1 for contents in files.values() for line in contents.splitlines() if line.strip())


def _combined_harness_logs(harness: AiderTestResult) -> str:
    return "\n".join(str(value) for value in harness.logs.values())


def _harness_has_sanitizer_error(harness: AiderTestResult) -> bool:
    logs = _combined_harness_logs(harness).lower()
    return any(marker in logs for marker in SANITIZER_ERROR_MARKERS)
