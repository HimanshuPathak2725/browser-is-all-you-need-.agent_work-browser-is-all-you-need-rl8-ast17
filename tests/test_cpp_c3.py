from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from glm47_posttraining.verifiers.cpp_c3 import (
    BehavioralContract,
    C3Disposition,
    C3EvaluationContext,
    CommandObservation,
    CommandTermination,
    MaterializationStatus,
    SubprocessCommandRunner,
    evaluate_c3,
)


@dataclass
class Step:
    observation: CommandObservation
    report_factory: Callable[[Mapping[str, str]], object] | None = None


class FakeRunner:
    def __init__(self, *steps: Step, attest_reports: bool = True):
        self.steps = list(steps)
        self.attest_reports = attest_reports
        self.calls: list[tuple[tuple[str, ...], Path, float]] = []

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: Mapping[str, str] | None = None,
    ) -> CommandObservation:
        assert self.steps, "unexpected command"
        self.calls.append((tuple(command), cwd, timeout_seconds))
        step = self.steps.pop(0)
        if step.report_factory is not None:
            assert env is not None
            report_path = Path(env["W8_C3_REPORT_PATH"])
            report = step.report_factory(env)
            if isinstance(report, bytes):
                report_path.write_bytes(report)
            elif report is not None:
                report_path.write_text(json.dumps(report), encoding="utf-8")
            if self.attest_reports:
                return replace(step.observation, oracle_report_trusted=True)
        return step.observation


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract(
    tmp_path: Path,
    *,
    case_ids: tuple[str, ...] = ("behavior.primary", "behavior.edge"),
    required_paths: tuple[str, ...] = ("candidate.cpp",),
    artifact_contents: str = "trusted oracle placeholder\n",
) -> BehavioralContract:
    oracle_dir = tmp_path / "trusted-oracle"
    oracle_dir.mkdir(exist_ok=True)
    artifact = oracle_dir / "oracle.py"
    artifact.write_text(artifact_contents, encoding="utf-8")
    return BehavioralContract(
        contract_version="crypto-square-behavior-v1",
        oracle_id="trusted-behavior-oracle",
        oracle_version="1.0.0",
        oracle_artifact=artifact.resolve(),
        oracle_artifact_sha256=_sha256(artifact),
        required_case_ids=case_ids,
        required_candidate_paths=required_paths,
        build_command=(sys.executable, "--workspace", "{workspace}"),
        oracle_command=(sys.executable, "{oracle_artifact}"),
    )


def _context(tmp_path: Path, contract: BehavioralContract) -> C3EvaluationContext:
    workspace = tmp_path / "candidate"
    workspace.mkdir(exist_ok=True)
    (workspace / "candidate.cpp").write_text("// candidate\n", encoding="utf-8")
    return C3EvaluationContext(
        workspace=workspace,
        task_contract_version=contract.contract_version,
    )


def _report(
    contract: BehavioralContract,
    passed: Mapping[str, bool] | None = None,
    *,
    diagnostic: str = "",
) -> dict[str, object]:
    outcomes = passed or {case_id: True for case_id in contract.required_case_ids}
    return {
        "schema_version": "c3-oracle-report-v1",
        "contract_version": contract.contract_version,
        "contract_digest": contract.identity_digest,
        "oracle_id": contract.oracle_id,
        "oracle_version": contract.oracle_version,
        "cases": [
            {"id": case_id, "passed": outcome, "diagnostic": diagnostic}
            for case_id, outcome in outcomes.items()
        ],
    }


def _success_runner(contract: BehavioralContract, *, diagnostic: str = "") -> FakeRunner:
    return FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(
            CommandObservation.completed(0),
            lambda _env: _report(contract, diagnostic=diagnostic),
        ),
    )


def _failure_runner(
    contract: BehavioralContract,
    failed_case: str,
    *,
    diagnostic: str = "wrong answer",
) -> FakeRunner:
    outcomes = {case_id: case_id != failed_case for case_id in contract.required_case_ids}
    return FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(
            CommandObservation.completed(0),
            lambda _env: _report(contract, outcomes, diagnostic=diagnostic),
        ),
    )


def test_valid_implementation_scores_positive_one(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=_success_runner(contract))

    assert receipt.disposition is C3Disposition.SCORED
    assert receipt.verifier_results[0].kernel == 1
    assert receipt.category_score == 1
    assert receipt.verifier_results[0].failure_code is None


@pytest.mark.parametrize("failed_case", ["behavior.primary", "behavior.edge"])
def test_each_required_behavior_failure_scores_negative_one(
    tmp_path: Path,
    failed_case: str,
) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=_failure_runner(contract, failed_case),
    )

    assert receipt.disposition is C3Disposition.SCORED
    assert receipt.verifier_results[0].kernel == -1
    assert receipt.category_score == -1
    assert receipt.verifier_results[0].evidence["failed_case_ids"] == [failed_case]


@pytest.mark.parametrize(
    "semantic_evidence",
    [
        "wrong result",
        "required edge behavior violated",
        "candidate runtime exception captured by oracle",
        "candidate execution limit captured by oracle",
        "required determinism invariant violated",
    ],
)
def test_behavioral_failure_subtype_never_changes_kernel(
    tmp_path: Path,
    semantic_evidence: str,
) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=_failure_runner(
            contract,
            "behavior.primary",
            diagnostic=semantic_evidence,
        ),
    )

    assert receipt.verifier_results[0].kernel == -1
    assert receipt.category_score == -1


@pytest.mark.parametrize("owner", ["C1", "C2", "C4"])
def test_build_failure_from_neighboring_category_is_not_scored(
    tmp_path: Path,
    owner: str,
) -> None:
    contract = _contract(tmp_path)
    runner = FakeRunner(Step(CommandObservation.completed(1, stderr=f"{owner} failure")))

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.NOT_EVALUATED
    assert receipt.verifier_results[0].kernel is None
    assert receipt.category_score is None
    assert receipt.verifier_results[0].evidence["blocking_owners"] == ["C1", "C2", "C4"]


def test_neighboring_category_defect_does_not_block_independently_applicable_c3(
    tmp_path: Path,
) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    # A neighboring verifier may reject an invariant outside this oracle's execution path.
    # C3 itself uses only its applicability gate and authoritative behavioral report.
    receipt = evaluate_c3(context, contract, runner=_success_runner(contract))

    assert receipt.category_score == 1


def test_wrong_algorithm_is_negative_c3_after_successful_build(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=_failure_runner(contract, "behavior.primary"),
    )

    assert receipt.category_score == -1


def test_p1_candidate_format_cause_is_unscored(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = C3EvaluationContext(
        workspace=tmp_path / "absent",
        task_contract_version=contract.contract_version,
        candidate_response_valid=False,
        materialization_evidence="response truncated before file block closed",
    )

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.CANDIDATE_FORMAT_INVALID
    assert receipt.category_score is None


def test_p2_attempt_history_does_not_change_single_candidate_c3(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    first = evaluate_c3(context, contract, runner=_failure_runner(contract, "behavior.edge"))
    retry = evaluate_c3(context, contract, runner=_failure_runner(contract, "behavior.edge"))

    assert first.to_dict() == retry.to_dict()
    assert first.category_score == retry.category_score == -1


@pytest.mark.parametrize(
    ("termination", "code"),
    [
        (CommandTermination.EXECUTABLE_MISSING, "C3_BUILD_EXECUTABLE_MISSING"),
        (CommandTermination.SPAWN_FAILED, "C3_BUILD_SPAWN_FAILED"),
        (CommandTermination.TIMED_OUT, "C3_BUILD_TIMED_OUT"),
        (CommandTermination.SIGNALLED, "C3_BUILD_SIGNALLED"),
    ],
)
def test_build_infrastructure_failure_is_unscored(
    tmp_path: Path,
    termination: CommandTermination,
    code: str,
) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=FakeRunner(Step(CommandObservation(termination=termination))),
    )

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.verifier_results[0].failure_code == code
    assert receipt.verifier_results[0].kernel is None
    assert receipt.category_score is None


@pytest.mark.parametrize(
    "termination",
    [
        CommandTermination.EXECUTABLE_MISSING,
        CommandTermination.SPAWN_FAILED,
        CommandTermination.TIMED_OUT,
        CommandTermination.SIGNALLED,
    ],
)
def test_oracle_infrastructure_failure_is_unscored(
    tmp_path: Path,
    termination: CommandTermination,
) -> None:
    contract = _contract(tmp_path)
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation(termination=termination)),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.verifier_results[0].kernel is None


def test_oracle_nonzero_exit_is_protocol_failure_not_semantic_failure(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation.completed(2, stderr="harness broke")),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None


@pytest.mark.parametrize(
    ("status", "disposition"),
    [
        (MaterializationStatus.CANDIDATE_FORMAT_INVALID, C3Disposition.CANDIDATE_FORMAT_INVALID),
        (MaterializationStatus.WORKSPACE_INVALID, C3Disposition.WORKSPACE_INVALID),
        (MaterializationStatus.INFRASTRUCTURE_INVALID, C3Disposition.INFRASTRUCTURE_INVALID),
    ],
)
def test_materialization_failure_preserves_established_cause(
    tmp_path: Path,
    status: MaterializationStatus,
    disposition: C3Disposition,
) -> None:
    contract = _contract(tmp_path)
    context = C3EvaluationContext(
        workspace=tmp_path / "absent",
        task_contract_version=contract.contract_version,
        materialization_status=status,
        materialization_evidence="cause established upstream",
    )

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is disposition
    assert receipt.category_score is None


def test_corrupted_workspace_is_unscored(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = C3EvaluationContext(
        workspace=tmp_path / "missing-workspace",
        task_contract_version=contract.contract_version,
    )

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.WORKSPACE_INVALID
    assert receipt.category_score is None


def test_missing_required_path_after_valid_materialization_is_workspace_invalid(
    tmp_path: Path,
) -> None:
    contract = _contract(tmp_path)
    workspace = tmp_path / "candidate"
    workspace.mkdir()
    context = C3EvaluationContext(workspace, contract.contract_version)

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.WORKSPACE_INVALID
    assert receipt.category_score is None


def test_contract_version_mismatch_is_unscored(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    context = C3EvaluationContext(context.workspace, "unexpected-version")

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.CONTRACT_INVALID
    assert receipt.category_score is None


def test_oracle_artifact_digest_mismatch_is_contract_invalid(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    contract.oracle_artifact.write_text("tampered\n", encoding="utf-8")

    receipt = evaluate_c3(context, contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.CONTRACT_INVALID
    assert receipt.category_score is None


@pytest.mark.parametrize(
    "report_factory",
    [
        lambda _env: None,
        lambda _env: b"not json",
        lambda _env: [],
    ],
)
def test_missing_or_malformed_oracle_report_is_unscored(
    tmp_path: Path,
    report_factory: Callable[[Mapping[str, str]], object],
) -> None:
    contract = _contract(tmp_path)
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation.completed(0), report_factory),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None


def test_ambiguous_incomplete_case_report_is_unscored(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    incomplete = {"behavior.primary": True}
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation.completed(0), lambda _env: _report(contract, incomplete)),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None


def test_extra_inactive_case_cannot_change_reward(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    cases = {case_id: True for case_id in contract.required_case_ids}
    cases["inactive.extra"] = True
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation.completed(0), lambda _env: _report(contract, cases)),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None


def test_duplicate_contract_cases_are_rejected_not_double_counted(tmp_path: Path) -> None:
    contract = _contract(
        tmp_path,
        case_ids=("behavior.primary", "behavior.primary"),
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=FakeRunner())

    assert receipt.disposition is C3Disposition.CONTRACT_INVALID
    assert receipt.category_score is None


def test_diagnostic_wording_does_not_change_kernel(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    first = evaluate_c3(
        context,
        contract,
        runner=_failure_runner(contract, "behavior.primary", diagnostic="wording A"),
    )
    second = evaluate_c3(
        context,
        contract,
        runner=_failure_runner(contract, "behavior.primary", diagnostic="localized wording B"),
    )

    assert first.verifier_results[0].kernel == second.verifier_results[0].kernel == -1
    assert first.category_score == second.category_score == -1


def test_repeated_equivalent_evaluation_is_deterministic(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    first = evaluate_c3(context, contract, runner=_success_runner(contract))
    second = evaluate_c3(context, contract, runner=_success_runner(contract))

    assert first.to_dict() == second.to_dict()


def test_all_scored_kernels_are_binary_and_score_equals_kernel(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    context = _context(tmp_path, contract)
    receipts = [
        evaluate_c3(context, contract, runner=_success_runner(contract)),
        evaluate_c3(
            context,
            contract,
            runner=_failure_runner(contract, "behavior.primary"),
        ),
    ]

    assert {receipt.verifier_results[0].kernel for receipt in receipts} == {-1, 1}
    assert all(receipt.category_score == receipt.verifier_results[0].kernel for receipt in receipts)


def test_relative_command_contract_is_rejected(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    invalid = replace(contract, build_command=("ambient-build-tool",))
    receipt = evaluate_c3(_context(tmp_path, contract), invalid, runner=_success_runner(invalid))

    assert receipt.disposition is C3Disposition.CONTRACT_INVALID
    assert receipt.category_score is None


def test_receipt_serializes_kernels_and_rejects_inconsistent_status(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=_success_runner(contract))

    assert receipt.to_dict()["kernels"] == [1]
    with pytest.raises(ValueError, match="inconsistent"):
        replace(
            receipt,
            verifier_results=(replace(receipt.verifier_results[0], status="failed"),),
        )


def test_unattested_local_subprocess_oracle_is_unscored(tmp_path: Path) -> None:
    script = """
import json
import os
from pathlib import Path

report = {
    "schema_version": "c3-oracle-report-v1",
    "contract_version": os.environ["W8_C3_CONTRACT_VERSION"],
    "contract_digest": os.environ["W8_C3_CONTRACT_DIGEST"],
    "oracle_id": os.environ["W8_C3_ORACLE_ID"],
    "oracle_version": os.environ["W8_C3_ORACLE_VERSION"],
    "cases": [{"id": "behavior.primary", "passed": True}],
}
Path(os.environ["W8_C3_REPORT_PATH"]).write_text(json.dumps(report), encoding="utf-8")
""".lstrip()
    contract = _contract(
        tmp_path,
        case_ids=("behavior.primary",),
        artifact_contents=script,
    )
    contract = BehavioralContract(
        contract_version=contract.contract_version,
        oracle_id=contract.oracle_id,
        oracle_version=contract.oracle_version,
        oracle_artifact=contract.oracle_artifact,
        oracle_artifact_sha256=contract.oracle_artifact_sha256,
        required_case_ids=contract.required_case_ids,
        required_candidate_paths=contract.required_candidate_paths,
        build_command=(sys.executable, "-c", "raise SystemExit(0)"),
        oracle_command=(sys.executable, "{oracle_artifact}"),
    )

    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=SubprocessCommandRunner(),
    )

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None
    assert receipt.verifier_results[0].failure_code == "C3_ORACLE_REPORT_CHANNEL_UNTRUSTED"


def test_valid_looking_unattested_report_cannot_score(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    runner = FakeRunner(
        Step(CommandObservation.completed(0)),
        Step(CommandObservation.completed(0), lambda _env: _report(contract)),
        attest_reports=False,
    )

    receipt = evaluate_c3(_context(tmp_path, contract), contract, runner=runner)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.category_score is None
    assert receipt.verifier_results[0].failure_code == "C3_ORACLE_REPORT_CHANNEL_UNTRUSTED"


def test_real_missing_executable_is_infrastructure_invalid(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    contract = BehavioralContract(
        contract_version=contract.contract_version,
        oracle_id=contract.oracle_id,
        oracle_version=contract.oracle_version,
        oracle_artifact=contract.oracle_artifact,
        oracle_artifact_sha256=contract.oracle_artifact_sha256,
        required_case_ids=contract.required_case_ids,
        required_candidate_paths=contract.required_candidate_paths,
        build_command=("/definitely/missing/w8-c3-compiler",),
        oracle_command=contract.oracle_command,
    )

    receipt = evaluate_c3(
        _context(tmp_path, contract),
        contract,
        runner=SubprocessCommandRunner(),
    )

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.verifier_results[0].kernel is None


def test_subprocess_runner_does_not_forward_host_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("W8_SECRET_SENTINEL", "must-not-leak")

    observation = SubprocessCommandRunner().run(
        (
            sys.executable,
            "-c",
            "import os; print(os.environ.get('W8_SECRET_SENTINEL', 'absent'))",
        ),
        cwd=tmp_path,
        timeout_seconds=10,
    )

    assert observation.termination is CommandTermination.COMPLETED
    assert observation.stdout_tail.strip() == "absent"


def test_contract_validation_precedes_workspace_validation(tmp_path: Path) -> None:
    contract = _contract(tmp_path)
    invalid = replace(
        contract,
        required_case_ids=("behavior.duplicate", "behavior.duplicate"),
    )
    context = C3EvaluationContext(
        workspace=tmp_path / "missing-workspace",
        task_contract_version=invalid.contract_version,
    )
    runner = FakeRunner()

    receipt = evaluate_c3(context, invalid, runner=runner)

    assert receipt.disposition is C3Disposition.CONTRACT_INVALID
    assert receipt.verifier_results[0].failure_code == "C3_DUPLICATE_REQUIRED_CASE_ID"
    assert receipt.category_score is None
    assert runner.calls == []


def test_omitted_runner_fails_closed_without_host_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _contract(tmp_path)

    def forbidden_run(*_args: object, **_kwargs: object) -> CommandObservation:
        raise AssertionError("the default host subprocess runner must not execute")

    monkeypatch.setattr(SubprocessCommandRunner, "run", forbidden_run)

    receipt = evaluate_c3(_context(tmp_path, contract), contract)

    assert receipt.disposition is C3Disposition.INFRASTRUCTURE_INVALID
    assert receipt.verifier_results[0].failure_code == "C3_SANDBOX_RUNNER_REQUIRED"
    assert receipt.verifier_results[0].phase == "execution_setup"
    assert receipt.verifier_results[0].kernel is None
    assert receipt.category_score is None
