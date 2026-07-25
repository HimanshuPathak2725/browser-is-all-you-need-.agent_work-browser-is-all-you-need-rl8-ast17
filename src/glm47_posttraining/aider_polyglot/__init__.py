"""Aider Polyglot C++ tasks, verifier, and GRPO reward."""

from .ast_evaluator import AST17_CHECK_WEIGHTS, AST17Evaluation, compute_ast17_score
from .reward import (
    AiderRewardBreakdown,
    ProductionAiderRewardBreakdown,
    compute_aider_reward,
    compute_production_aider_reward,
    compute_weighted45_aider_reward,
)
from .schema import AiderPolyglotTask, AiderTestResult

__all__ = [
    "AST17_CHECK_WEIGHTS",
    "AST17Evaluation",
    "AiderPolyglotTask",
    "ProductionAiderRewardBreakdown",
    "AiderRewardBreakdown",
    "AiderTestResult",
    "compute_ast17_score",
    "compute_aider_reward",
    "compute_production_aider_reward",
    "compute_weighted45_aider_reward",
]
