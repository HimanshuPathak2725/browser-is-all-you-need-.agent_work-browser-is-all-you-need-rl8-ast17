from __future__ import annotations

from glm47_posttraining.aider_polyglot.policy45 import PROCESS_EXEC_RE, SYSTEM_CALL_RE
from glm47_posttraining.aider_polyglot.harness import _validate_candidate_source


def test_execute_method_is_not_misclassified_as_process_exec() -> None:
    source = "bool execute(const Plan& plan) { return plan.valid(); }"
    assert SYSTEM_CALL_RE.search(source) is None
    _validate_candidate_source("answer.cpp", source)
    assert PROCESS_EXEC_RE.search(source) is None


def test_real_exec_family_calls_remain_forbidden() -> None:
    for source in ('execve("/bin/x", argv, envp);', 'execlp("sh", "sh", nullptr);'):
        assert SYSTEM_CALL_RE.search(source) is not None
        assert PROCESS_EXEC_RE.search(source) is not None
