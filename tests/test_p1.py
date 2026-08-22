from __future__ import annotations

from dataclasses import replace
from enum import Enum

import pytest

from glm47_posttraining.verifiers.p1 import (
    RECEIPT_SCHEMA_VERSION,
    EvaluationValidity,
    P1Contract,
    P1Receipt,
    Termination,
    VerifierResult,
    evaluate_p1,
)


@pytest.fixture
def contract() -> P1Contract:
    return P1Contract(version="crypto-square-generation-v1", trusted_sources=frozenset({"adapter"}))


def evidence(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": "crypto-square-generation-v1",
        "attempt_id": "attempt-1",
        "source": "adapter",
        "termination": "completed",
        "generation_started": True,
        "delivery_complete": True,
        "diagnostic": "normal stop",
    }
    value.update(overrides)
    return value


def assert_unscored(receipt: P1Receipt, disposition: str) -> None:
    assert receipt.disposition == disposition
    assert receipt.kernels is None
    assert receipt.category_score is None
    assert receipt.verifier_results[0].kernel is None


def test_completed_generation_passes(contract: P1Contract) -> None:
    receipt = evaluate_p1(evidence(), contract)
    assert receipt.disposition == "scored"
    assert receipt.kernels == (1,)
    assert receipt.category_score == 1.0


def test_trusted_model_limit_fails(contract: P1Contract) -> None:
    receipt = evaluate_p1(evidence(termination="model_limit"), contract)
    assert receipt.disposition == "scored"
    assert receipt.kernels == (-1,)
    assert receipt.category_score == -1.0
    assert receipt.verifier_results[0].failure_code == "P1_CONTEXT_EXHAUSTED"


@pytest.mark.parametrize("termination", ["transport_interrupted", "provider_error", "cancelled"])
def test_nonsemantic_termination_is_infrastructure_invalid(
    contract: P1Contract, termination: str
) -> None:
    assert_unscored(
        evaluate_p1(evidence(termination=termination), contract),
        "infrastructure_invalid",
    )


def test_unknown_termination_is_ambiguous(contract: P1Contract) -> None:
    assert_unscored(evaluate_p1(evidence(termination="unknown"), contract), "not_evaluated")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("attempt_id", None),
        ("source", 3),
        ("termination", "made-up"),
        ("generation_started", 1),
        ("delivery_complete", "yes"),
        ("diagnostic", 4),
    ],
)
def test_malformed_evidence_has_no_score(contract: P1Contract, field: str, value: object) -> None:
    assert_unscored(
        evaluate_p1(evidence(**{field: value}), contract),
        "infrastructure_invalid",
    )


def test_missing_evidence_field_has_no_score(contract: P1Contract) -> None:
    value = evidence()
    del value["termination"]
    assert_unscored(evaluate_p1(value, contract), "infrastructure_invalid")


def test_candidate_format_invalid_is_distinct_from_malformed_adapter_evidence(
    contract: P1Contract,
) -> None:
    receipt = evaluate_p1({}, contract, EvaluationValidity(candidate_format_valid=False))
    assert_unscored(receipt, "candidate_format_invalid")
    assert receipt.verifier_results[0].failure_code == "P1_CANDIDATE_FORMAT_INVALID"


@pytest.mark.parametrize(
    "invalid_contract",
    [
        P1Contract(version="", trusted_sources=frozenset({"adapter"})),
        P1Contract(version="v1", trusted_sources=frozenset()),
        P1Contract(
            version="v1",
            trusted_sources=frozenset({"adapter"}),
            schema_version="unsupported-schema",
        ),
    ],
)
def test_invalid_local_contract_has_no_score(invalid_contract: P1Contract) -> None:
    receipt = evaluate_p1(evidence(), invalid_contract)
    assert_unscored(receipt, "contract_invalid")
    assert receipt.schema_version == RECEIPT_SCHEMA_VERSION
    assert receipt.verifier_results[0].failure_code == "P1_LOCAL_CONTRACT_INVALID"


def test_contract_mismatch_has_no_score(contract: P1Contract) -> None:
    assert_unscored(
        evaluate_p1(evidence(contract_version="other"), contract),
        "contract_invalid",
    )


def test_untrusted_evidence_source_has_no_score(contract: P1Contract) -> None:
    assert_unscored(
        evaluate_p1(evidence(source="candidate"), contract),
        "infrastructure_invalid",
    )


@pytest.mark.parametrize("field", ["generation_started", "delivery_complete"])
def test_incomplete_delivery_cannot_establish_cause(contract: P1Contract, field: str) -> None:
    assert_unscored(
        evaluate_p1(evidence(**{field: False}), contract),
        "infrastructure_invalid",
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
    contract: P1Contract, validity: EvaluationValidity, disposition: str
) -> None:
    assert_unscored(evaluate_p1(evidence(), contract, validity), disposition)


def test_missing_candidate_file_does_not_imply_p1_failure(contract: P1Contract) -> None:
    # Candidate content is intentionally not an input to P1. A structurally valid
    # response that omitted a task file belongs to ordinary candidate evaluation elsewhere.
    receipt = evaluate_p1(evidence(diagnostic="candidate omitted cipher.cpp"), contract)
    assert receipt.kernels == (1,)


def test_diagnostic_wording_does_not_change_kernel(contract: P1Contract) -> None:
    first = evaluate_p1(evidence(termination="model_limit", diagnostic="max tokens"), contract)
    second = evaluate_p1(
        evidence(termination="model_limit", diagnostic="localized and reformatted"), contract
    )
    assert first.kernels == second.kernels == (-1,)
    assert first.category_score == second.category_score == -1.0


def test_python_310_compatible_string_enum() -> None:
    assert issubclass(Termination, str)
    assert issubclass(Termination, Enum)


def test_equivalent_evaluation_is_deterministic(contract: P1Contract) -> None:
    value = evidence(termination="model_limit", diagnostic="  repeated\n whitespace ")
    assert evaluate_p1(value, contract).to_dict() == evaluate_p1(value, contract).to_dict()


def test_receipt_rejects_zero_kernel(contract: P1Contract) -> None:
    with pytest.raises(ValueError, match=r"-1 or \+1"):
        P1Receipt(
            schema_version=contract.schema_version,
            category="P1",
            contract_version=contract.version,
            disposition="scored",
            verifier_results=(VerifierResult("generation-completeness", "passed", 0, None),),
            kernels=(0,),
            category_score=0.0,
            evidence={},
        )


def test_receipt_rejects_reward_on_unscored_disposition(contract: P1Contract) -> None:
    valid = evaluate_p1(evidence(), contract)
    with pytest.raises(ValueError, match="cannot contain reward"):
        replace(valid, disposition="not_evaluated")


def test_receipt_rejects_disagreement_between_result_and_category_kernel(
    contract: P1Contract,
) -> None:
    with pytest.raises(ValueError, match="kernels must agree"):
        P1Receipt(
            schema_version=RECEIPT_SCHEMA_VERSION,
            category="P1",
            contract_version=contract.version,
            disposition="scored",
            verifier_results=(
                VerifierResult("generation-completeness", "failed", -1, "P1_CONTEXT_EXHAUSTED"),
            ),
            kernels=(1,),
            category_score=1.0,
            evidence={},
        )


def test_receipt_rejects_reward_bearing_non_scored_verifier(contract: P1Contract) -> None:
    valid = evaluate_p1(evidence(termination="unknown"), contract)
    with pytest.raises(ValueError, match="not-evaluated"):
        replace(
            valid,
            verifier_results=(VerifierResult("generation-completeness", "passed", 1, None),),
        )


def test_duplicate_verifier_results_cannot_change_reward(contract: P1Contract) -> None:
    valid = evaluate_p1(evidence(), contract)
    with pytest.raises(ValueError, match="exactly one verifier result"):
        replace(valid, verifier_results=valid.verifier_results * 2)


def test_receipt_rejects_unknown_disposition(contract: P1Contract) -> None:
    valid = evaluate_p1(evidence(termination="unknown"), contract)
    with pytest.raises(ValueError, match="invalid P1 receipt disposition"):
        replace(valid, disposition="invented")
