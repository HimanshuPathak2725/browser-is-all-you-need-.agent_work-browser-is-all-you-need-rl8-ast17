from __future__ import annotations

import json
from pathlib import Path

import pytest

from glm47_posttraining.aider_polyglot.charm_grpo import (
    CharmGRPOProjectionError,
    build_charm_grpo_dataset,
    validate_projected_dataset,
)
from glm47_posttraining.aider_polyglot.compiler_guided import (
    GENERIC_PRIVATE_FAILURE,
    PublicCompileResult,
    run_best_of_n_with_repair,
    sanitize_public_compiler_feedback,
)
from glm47_posttraining.aider_polyglot.parser import ParsedAiderResponse
from glm47_posttraining.aider_polyglot.reward import ProductionAiderRewardBreakdown
from glm47_posttraining.aider_polyglot.schema import AiderPolyglotTask, AiderTestResult


ROOT = Path(__file__).resolve().parents[1]
SELECTED = (
    ROOT
    / "artifacts/charm-task-generation-v1/v1-20260803T193513Z"
    / "sft-ready-v5-20260804T033850Z/independent-audit/selected-manifest.json"
)


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_certified_prompt_variants_project_without_private_leakage(tmp_path: Path) -> None:
    output = tmp_path / "data"
    paths = build_charm_grpo_dataset(SELECTED, output)
    receipt = validate_projected_dataset(output)
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    train = _rows(paths["grpo_train"])
    monitor = _rows(paths["eval"])

    assert receipt == {
        "decision": "PASS",
        "manifest_sha256": receipt["manifest_sha256"],
        "monitor_task_count": 12,
        "private_marker_count": 0,
        "row_count": 155,
        "task_overlap_count": 0,
        "train_task_count": 36,
    }
    assert manifest["counts"] == {
        "certified_source_tasks": 51,
        "excluded_calibration_tasks": 3,
        "gradient_rows": len(train),
        "gradient_tasks": 36,
        "monitor_rows": len(monitor),
        "monitor_tasks": 12,
    }
    assert set(manifest["prompt_variant_counts"]) == {
        "short",
        "medium",
        "detailed",
        "repair",
    }
    train_bases = {row["metadata"]["base_task_id"] for row in train}
    monitor_bases = {row["metadata"]["base_task_id"] for row in monitor}
    assert train_bases.isdisjoint(monitor_bases)
    assert {row["metadata"]["mechanism_monitor_id"] for row in monitor} - {None}
    for row in train + monitor:
        prompt = json.dumps(row["prompt"]).lower()
        assert ".reference/" not in prompt
        assert ".grader/" not in prompt
        assert "hidden_test_sha256" not in prompt


def test_projected_validator_rejects_reference_leak(tmp_path: Path) -> None:
    output = tmp_path / "data"
    build_charm_grpo_dataset(SELECTED, output)
    exercise = next((output / "shadow").iterdir())
    leaked = exercise / ".reference" / "answer.cpp"
    leaked.parent.mkdir()
    leaked.write_text("int answer = 1;\n", encoding="utf-8")
    with pytest.raises(CharmGRPOProjectionError, match="runtime exercise leakage"):
        validate_projected_dataset(output)


def test_public_compiler_feedback_returns_first_editable_error_only() -> None:
    logs = """
/private/run/.grader/test.cpp:44: error: expected secret value
/tmp/work/example.cpp:8:5: error: expected ';' before '}' token
    }
    ^
/tmp/work/example.cpp:9:1: note: to match this '{'
"""
    feedback = sanitize_public_compiler_feedback(logs, ["example.cpp"])
    assert feedback is not None
    assert "example.cpp:8:5: error:" in feedback
    assert ".grader" not in feedback
    assert "secret value" not in feedback
    assert "/tmp/work" not in feedback


class _Client:
    def __init__(self) -> None:
        self.calls: list[tuple[list[dict[str, str]], float, int]] = []

    def complete(self, messages, *, temperature: float, seed: int) -> str:
        self.calls.append((list(messages), temperature, seed))
        return "good" if len(messages) > 1 else "bad"


def test_best_of_n_uses_lower_temperature_repair_and_selects_pass(monkeypatch, tmp_path: Path) -> None:
    task = AiderPolyglotTask(
        task_id="charm-grpo/example/short",
        exercise="example",
        split="train",
        harness_kind="shadow_cpp17",
        exercise_dir="shadow/example",
        editable_files=["example.cpp"],
        prompt=[{"role": "user", "content": "repair example.cpp"}],
        hidden_test_sha256="a" * 64,
    )
    (tmp_path / "example.cpp").write_text("int value = 0;\n", encoding="utf-8")

    def fake_score(_task, _root, response, *, image):
        del image
        passed = response == "good"
        parsed = ParsedAiderResponse(files={"example.cpp": "int value = 1;\n"}, format_valid=True)
        harness = AiderTestResult(
            status="passed" if passed else "tests_failed",
            tests_passed=1 if passed else 0,
            tests_total=1,
        )
        return (
            ProductionAiderRewardBreakdown(
                reward=1.0 if passed else -0.2,
                reason="passed" if passed else "runtime_zero_pass",
                parsed=parsed,
                harness=harness,
            ),
            parsed,
        )

    monkeypatch.setattr(
        "glm47_posttraining.aider_polyglot.compiler_guided._score_response", fake_score
    )
    monkeypatch.setattr(
        "glm47_posttraining.aider_polyglot.compiler_guided._repair_feedback",
        lambda *args, **kwargs: (
            GENERIC_PRIVATE_FAILURE,
            PublicCompileResult(True, 0, "b" * 64, None),
        ),
    )
    client = _Client()
    selected, attempts = run_best_of_n_with_repair(
        task,
        tmp_path,
        client,
        candidates=2,
        repair_turns=1,
        temperature=0.7,
        repair_temperature=0.2,
    )
    assert selected.all_tests_pass is True
    assert selected.turn == 1
    assert len(attempts) == 4
    assert [call[1] for call in client.calls] == [0.7, 0.2, 0.7, 0.2]
    assert client.calls[1][0][-1]["content"] == GENERIC_PRIVATE_FAILURE
