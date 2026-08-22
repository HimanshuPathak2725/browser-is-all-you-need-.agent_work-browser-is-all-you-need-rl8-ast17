from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from glm47_posttraining.verifiers.p2 import (
    EvaluationValidity,
    P2Contract,
    P2Receipt,
    VerifierResult,
    evaluate_p2,
)


TARGET = "C2/implementation-translation"
OTHER = "C1/public-api"
VERIFIER_CONTRACTS = {TARGET: "c2-v1", OTHER: "c1-v1", "C3/behavior": "c3-v1"}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture
def contract() -> P2Contract:
    return P2Contract(
        version="crypto-square-repair-v1",
        task_id="crypto-square",
        trusted_sources=frozenset({"runner"}),
        verifier_contracts=VERIFIER_CONTRACTS,
    )


def history(
    *,
    previous: dict[str, int] | None = None,
    current: dict[str, int] | None = None,
    previous_digest: str = digest("candidate-a"),
    current_digest: str = digest("candidate-b"),
    targets: list[str] | None = None,
    **overrides: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "w8-biayn-category-receipt-v1",
        "contract_version": "crypto-square-repair-v1",
        "source": "runner",
        "task_id": "crypto-square",
        "lineage_id": "trial-1",
        "actionable_feedback": True,
        "feedback_id": "feedback-1",
        "feedback_for_attempt_id": "attempt-1",
        "targets": targets if targets is not None else [TARGET],
        "previous": {
            "attempt_id": "attempt-1",
            "candidate_digest": previous_digest,
            "outcomes": previous if previous is not None else {TARGET: -1},
            "outcome_contract_versions": {
                key: VERIFIER_CONTRACTS.get(key, "unknown-v1")
                for key in (previous if previous is not None else {TARGET: -1})
            },
        },
        "current": {
            "attempt_id": "attempt-2",
            "parent_attempt_id": "attempt-1",
            "candidate_digest": current_digest,
            "outcomes": current if current is not None else {TARGET: 1},
            "outcome_contract_versions": {
                key: VERIFIER_CONTRACTS.get(key, "unknown-v1")
                for key in (current if current is not None else {TARGET: 1})
            },
            "consumed_feedback_id": "feedback-1",
        },
        "diagnostic": "repair feedback",
    }
    value.update(overrides)
    return value


def assert_unscored(receipt: P2Receipt, disposition: str) -> None:
    assert receipt.disposition == disposition
    assert receipt.kernels is None
    assert receipt.category_score is None
    assert receipt.verifier_results[0].kernel is None


def test_genuine_semantic_repair_passes(contract: P2Contract) -> None:
    receipt = evaluate_p2(history(), contract)
    assert receipt.disposition == "scored"
    assert receipt.kernels == (1,)
    assert receipt.category_score == 1.0


@pytest.mark.parametrize("current_digest", [digest("candidate-a"), digest("candidate-b")])
def test_same_semantic_failure_is_no_progress(contract: P2Contract, current_digest: str) -> None:
    receipt = evaluate_p2(
        history(current={TARGET: -1}, current_digest=current_digest),
        contract,
    )
    assert receipt.kernels == (-1,)
    assert receipt.category_score == -1.0


def test_regression_without_fix_is_no_progress(contract: P2Contract) -> None:
    other = OTHER
    receipt = evaluate_p2(
        history(
            previous={TARGET: -1, other: 1},
            current={TARGET: -1, other: -1},
        ),
        contract,
    )
    assert receipt.kernels == (-1,)


def test_fix_with_unrelated_regression_is_ambiguous(contract: P2Contract) -> None:
    other = OTHER
    assert_unscored(
        evaluate_p2(
            history(
                previous={TARGET: -1, other: 1},
                current={TARGET: 1, other: -1},
            ),
            contract,
        ),
        "not_evaluated",
    )


def test_newly_evaluable_outcome_does_not_block_progress(contract: P2Contract) -> None:
    receipt = evaluate_p2(
        history(current={TARGET: 1, "C3/behavior": -1}),
        contract,
    )
    assert receipt.kernels == (1,)


def test_targeted_progress_does_not_require_complete_solution(contract: P2Contract) -> None:
    receipt = evaluate_p2(
        history(
            previous={TARGET: -1, OTHER: -1},
            current={TARGET: 1, OTHER: -1},
        ),
        contract,
    )
    assert receipt.kernels == (1,)


def test_target_order_does_not_change_semantic_result(contract: P2Contract) -> None:
    outcomes_before = {TARGET: -1, OTHER: -1}
    outcomes_after = {TARGET: 1, OTHER: 1}
    first = evaluate_p2(
        history(previous=outcomes_before, current=outcomes_after, targets=[TARGET, OTHER]),
        contract,
    )
    second = evaluate_p2(
        history(previous=outcomes_before, current=outcomes_after, targets=[OTHER, TARGET]),
        contract,
    )
    assert first.to_dict() == second.to_dict()


def test_duplicate_target_evidence_is_invalid(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(history(targets=[TARGET, TARGET]), contract),
        "evidence_invalid",
    )


def test_disappearing_prior_outcome_is_not_comparable(contract: P2Contract) -> None:
    other = "C1/public-api"
    assert_unscored(
        evaluate_p2(
            history(previous={TARGET: -1, other: 1}, current={TARGET: 1}),
            contract,
        ),
        "not_evaluated",
    )


def test_identical_candidate_with_changed_outcome_is_evidence_invalid(
    contract: P2Contract,
) -> None:
    assert_unscored(
        evaluate_p2(history(current_digest=digest("candidate-a")), contract),
        "evidence_invalid",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"actionable_feedback": False},
        {"targets": []},
    ],
)
def test_single_or_nonrepair_history_has_no_score(
    contract: P2Contract, change: dict[str, object]
) -> None:
    assert_unscored(evaluate_p2(history(**change), contract), "not_evaluated")


def test_unrelated_attempt_is_not_a_repair_pair(contract: P2Contract) -> None:
    value = history()
    current = dict(value["current"])  # type: ignore[arg-type]
    current["parent_attempt_id"] = "unrelated"
    value["current"] = current
    assert_unscored(evaluate_p2(value, contract), "not_evaluated")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("feedback_for_attempt_id", "unrelated"),
        ("feedback_id", "other-feedback"),
    ],
)
def test_feedback_must_be_causally_bound_to_attempt_pair(
    contract: P2Contract, field: str, value: str
) -> None:
    assert_unscored(evaluate_p2(history(**{field: value}), contract), "not_evaluated")


def test_missing_prior_attempt_is_malformed(contract: P2Contract) -> None:
    value = history()
    del value["previous"]
    assert_unscored(evaluate_p2(value, contract), "evidence_invalid")


def test_missing_target_outcome_has_no_score(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(
            history(
                previous={TARGET: -1, OTHER: -1},
                current={TARGET: 1},
                targets=[OTHER],
            ),
            contract,
        ),
        "not_evaluated",
    )


def test_no_failed_repair_target_has_no_score(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(history(previous={TARGET: 1}, current={TARGET: 1}), contract),
        "not_evaluated",
    )


@pytest.mark.parametrize("target", ["P2/repair-progress", "C2/invented-verifier"])
def test_unknown_or_recursive_target_is_contract_invalid(contract: P2Contract, target: str) -> None:
    assert_unscored(
        evaluate_p2(
            history(
                previous={target: -1},
                current={target: 1},
                targets=[target],
            ),
            contract,
        ),
        "contract_invalid",
    )


def test_contract_mismatch_has_no_score(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(history(contract_version="other"), contract),
        "contract_invalid",
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": "other-schema"},
        {"task_id": "other-task"},
    ],
)
def test_schema_or_task_mismatch_has_no_score(
    contract: P2Contract, overrides: dict[str, object]
) -> None:
    assert_unscored(evaluate_p2(history(**overrides), contract), "contract_invalid")


def test_untrusted_history_has_no_score(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(history(source="candidate"), contract),
        "evidence_invalid",
    )


def test_changed_verifier_contract_is_not_comparable(contract: P2Contract) -> None:
    value = history()
    current = dict(value["current"])  # type: ignore[arg-type]
    versions = dict(current["outcome_contract_versions"])  # type: ignore[arg-type]
    versions[TARGET] = "c2-v2"
    current["outcome_contract_versions"] = versions
    value["current"] = current
    assert_unscored(evaluate_p2(value, contract), "contract_invalid")


def test_unknown_nontarget_outcome_cannot_affect_progress(contract: P2Contract) -> None:
    assert_unscored(
        evaluate_p2(
            history(
                previous={TARGET: -1, "C4/invented": 1},
                current={TARGET: 1, "C4/invented": -1},
            ),
            contract,
        ),
        "contract_invalid",
    )


@pytest.mark.parametrize("bad_digest", ["candidate-a", "", "A" * 64, "0" * 63])
def test_noncanonical_candidate_digest_is_malformed(contract: P2Contract, bad_digest: str) -> None:
    assert_unscored(
        evaluate_p2(history(previous_digest=bad_digest), contract),
        "evidence_invalid",
    )


@pytest.mark.parametrize(
    ("validity", "disposition"),
    [
        (EvaluationValidity(candidate_format_valid=False), "candidate_format_invalid"),
        (EvaluationValidity(workspace_valid=False), "workspace_invalid"),
        (EvaluationValidity(infrastructure_valid=False), "infrastructure_invalid"),
    ],
)
def test_invalid_preconditions_have_no_score(
    contract: P2Contract, validity: EvaluationValidity, disposition: str
) -> None:
    assert_unscored(evaluate_p2(history(), contract, validity), disposition)


@pytest.mark.parametrize("bad_kernel", [-2, 0, 2, None, "-1"])
def test_malformed_semantic_outcome_has_no_score(contract: P2Contract, bad_kernel: object) -> None:
    assert_unscored(
        evaluate_p2(history(previous={TARGET: bad_kernel}), contract),  # type: ignore[dict-item]
        "evidence_invalid",
    )


def test_diagnostic_wording_does_not_change_kernel(contract: P2Contract) -> None:
    first = evaluate_p2(history(current={TARGET: -1}, diagnostic="same error"), contract)
    second = evaluate_p2(
        history(current={TARGET: -1}, diagnostic="different locale and formatting"),
        contract,
    )
    assert first.kernels == second.kernels == (-1,)


def test_equivalent_history_is_deterministic(contract: P2Contract) -> None:
    value = history(diagnostic=" deterministic\n input ")
    assert evaluate_p2(value, contract).to_dict() == evaluate_p2(value, contract).to_dict()


def test_receipt_rejects_zero_kernel(contract: P2Contract) -> None:
    with pytest.raises(ValueError, match=r"-1 or \+1"):
        P2Receipt(
            schema_version=contract.schema_version,
            category="P2",
            contract_version=contract.version,
            disposition="scored",
            verifier_results=(VerifierResult("repair-progress", "passed", 0, None),),
            kernels=(0,),
            category_score=0.0,
            evidence={},
        )


def test_receipt_rejects_reward_on_unscored_disposition(contract: P2Contract) -> None:
    valid = evaluate_p2(history(), contract)
    with pytest.raises(ValueError, match="cannot contain reward"):
        replace(valid, disposition="not_evaluated")


def test_receipt_rejects_inconsistent_verifier_result(contract: P2Contract) -> None:
    valid = evaluate_p2(history(), contract)
    with pytest.raises(ValueError, match="agree with the P2 kernel"):
        replace(
            valid,
            verifier_results=(VerifierResult("repair-progress", "failed", -1, None),),
        )


def test_contract_rejects_unpinned_or_recursive_verifiers() -> None:
    with pytest.raises(ValueError, match="invalid verifier contract"):
        P2Contract(
            version="p2-v1",
            task_id="task",
            trusted_sources=frozenset({"runner"}),
            verifier_contracts={"P2/repair-progress": "p2-v1"},
        )


def test_contract_copies_mutable_verifier_mapping() -> None:
    mutable = {TARGET: "c2-v1"}
    contract = P2Contract(
        version="p2-v1",
        task_id="task",
        trusted_sources=frozenset({"runner"}),
        verifier_contracts=mutable,
    )
    mutable[TARGET] = "changed"
    assert contract.verifier_contracts[TARGET] == "c2-v1"


def test_contract_rejects_unknown_receipt_schema() -> None:
    with pytest.raises(ValueError, match="unsupported P2 contract schema"):
        P2Contract(
            version="p2-v1",
            task_id="task",
            trusted_sources=frozenset({"runner"}),
            verifier_contracts={TARGET: "c2-v1"},
            schema_version="invented",
        )


@pytest.mark.parametrize("invalid_contract", [None, {}, object()])
def test_invalid_contract_input_returns_structured_no_score(invalid_contract: object) -> None:
    receipt = evaluate_p2(history(), invalid_contract)

    assert receipt.schema_version == "w8-biayn-category-receipt-v1"
    assert receipt.category == "P2"
    assert receipt.contract_version == "invalid"
    assert receipt.disposition == "contract_invalid"
    assert receipt.verifier_results[0].status == "not_evaluated"
    assert receipt.verifier_results[0].failure_code == "P2_CONTRACT_INVALID"
    assert receipt.verifier_results[0].kernel is None
    assert receipt.kernels is None
    assert receipt.category_score is None
