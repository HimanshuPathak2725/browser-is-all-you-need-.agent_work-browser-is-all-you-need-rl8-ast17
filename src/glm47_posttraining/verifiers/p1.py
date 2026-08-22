"""P1 verifier for causally established generation incompleteness.

P1 is deliberately based on trusted, structured generation termination evidence.
Candidate contents, missing files, token estimates, and diagnostic wording cannot
establish context exhaustion by themselves.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


RECEIPT_SCHEMA_VERSION = "w8-biayn-category-receipt-v1"
CATEGORY = "P1"
VERIFIER_ID = "generation-completeness"


class Termination(str, Enum):
    """Normalized termination causes supplied by a trusted generation adapter."""

    COMPLETED = "completed"
    MODEL_LIMIT = "model_limit"
    TRANSPORT_INTERRUPTED = "transport_interrupted"
    PROVIDER_ERROR = "provider_error"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class P1Contract:
    """Pinned P1 evidence contract."""

    version: str
    trusted_sources: frozenset[str]
    schema_version: str = RECEIPT_SCHEMA_VERSION


@dataclass(frozen=True)
class EvaluationValidity:
    """Generic preconditions established outside the semantic verifier."""

    candidate_format_valid: bool = True
    workspace_valid: bool = True
    infrastructure_valid: bool = True


@dataclass(frozen=True)
class GenerationEvidence:
    """Structured evidence for one completed generation attempt."""

    contract_version: str
    attempt_id: str
    source: str
    termination: Termination
    generation_started: bool
    delivery_complete: bool
    diagnostic: str = ""

    @classmethod
    def parse(cls, value: Mapping[str, Any]) -> GenerationEvidence:
        """Parse strictly and fail closed on missing or incorrectly typed fields."""

        required = {
            "contract_version": str,
            "attempt_id": str,
            "source": str,
            "termination": str,
            "generation_started": bool,
            "delivery_complete": bool,
        }
        if not isinstance(value, Mapping):
            raise ValueError("generation evidence must be a mapping")
        for key, expected_type in required.items():
            if key not in value or type(value[key]) is not expected_type:
                raise ValueError(f"invalid or missing evidence field: {key}")
        if not value["attempt_id"] or not value["source"]:
            raise ValueError("attempt_id and source must be non-empty")
        diagnostic = value.get("diagnostic", "")
        if type(diagnostic) is not str:
            raise ValueError("diagnostic must be a string")
        try:
            termination = Termination(value["termination"])
        except ValueError as exc:
            raise ValueError("unsupported normalized termination") from exc
        return cls(
            contract_version=value["contract_version"],
            attempt_id=value["attempt_id"],
            source=value["source"],
            termination=termination,
            generation_started=value["generation_started"],
            delivery_complete=value["delivery_complete"],
            diagnostic=diagnostic,
        )


@dataclass(frozen=True)
class VerifierResult:
    verifier: str
    status: str
    kernel: int | None
    failure_code: str | None


@dataclass(frozen=True)
class P1Receipt:
    schema_version: str
    category: str
    contract_version: str
    disposition: str
    verifier_results: tuple[VerifierResult, ...]
    kernels: tuple[int, ...] | None
    category_score: float | None
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        valid_dispositions = {
            "scored",
            "candidate_format_invalid",
            "workspace_invalid",
            "infrastructure_invalid",
            "contract_invalid",
            "not_evaluated",
        }
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise ValueError("unsupported P1 receipt schema")
        if self.category != CATEGORY:
            raise ValueError("P1 receipt category must be P1")
        if self.disposition not in valid_dispositions:
            raise ValueError("invalid P1 receipt disposition")
        if len(self.verifier_results) != 1:
            raise ValueError("a P1 receipt must contain exactly one verifier result")
        result = self.verifier_results[0]
        if result.verifier != VERIFIER_ID:
            raise ValueError("unexpected P1 verifier id")
        if self.disposition == "scored":
            if self.kernels is None or len(self.kernels) != 1:
                raise ValueError("a scored P1 receipt must contain exactly one kernel")
            if self.kernels[0] not in (-1, 1):
                raise ValueError("semantic kernels must be -1 or +1")
            if self.category_score != float(self.kernels[0]):
                raise ValueError("P1 score must equal its sole kernel")
            if result.kernel != self.kernels[0]:
                raise ValueError("verifier and category kernels must agree")
            expected_status = "passed" if self.kernels[0] == 1 else "failed"
            if result.status != expected_status:
                raise ValueError("verifier status must agree with its kernel")
            if self.kernels[0] == 1 and result.failure_code is not None:
                raise ValueError("a passing verifier cannot contain a failure code")
            if self.kernels[0] == -1 and not result.failure_code:
                raise ValueError("a failing verifier must contain a failure code")
        elif self.kernels is not None or self.category_score is not None:
            raise ValueError("a non-scored receipt cannot contain reward values")
        elif result.kernel is not None or result.status != "not_evaluated":
            raise ValueError("a non-scored verifier result must be not-evaluated")
        elif not result.failure_code:
            raise ValueError("a non-scored P1 result requires a failure code")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "category": self.category,
            "contract_version": self.contract_version,
            "disposition": self.disposition,
            "verifier_results": [
                {
                    "verifier": result.verifier,
                    "status": result.status,
                    "kernel": result.kernel,
                    "failure_code": result.failure_code,
                }
                for result in self.verifier_results
            ],
            "kernels": list(self.kernels) if self.kernels is not None else None,
            "category_score": self.category_score,
            "evidence": dict(self.evidence),
        }


def _diagnostic_fingerprint(diagnostic: str) -> str:
    normalized = re.sub(r"\s+", " ", diagnostic).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _receipt(
    contract: P1Contract,
    disposition: str,
    status: str,
    failure_code: str | None,
    *,
    kernel: int | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> P1Receipt:
    scored = disposition == "scored"
    return P1Receipt(
        schema_version=RECEIPT_SCHEMA_VERSION,
        category=CATEGORY,
        contract_version=contract.version,
        disposition=disposition,
        verifier_results=(
            VerifierResult(
                verifier=VERIFIER_ID,
                status=status,
                kernel=kernel if scored else None,
                failure_code=failure_code,
            ),
        ),
        kernels=(kernel,) if scored and kernel is not None else None,
        category_score=float(kernel) if scored and kernel is not None else None,
        evidence=evidence or {},
    )


def _contract_is_valid(contract: P1Contract) -> bool:
    return (
        type(contract.version) is str
        and bool(contract.version.strip())
        and contract.schema_version == RECEIPT_SCHEMA_VERSION
        and isinstance(contract.trusted_sources, frozenset)
        and bool(contract.trusted_sources)
        and all(type(source) is str and bool(source.strip()) for source in contract.trusted_sources)
    )


def evaluate_p1(
    raw_evidence: Mapping[str, Any] | Any,
    contract: P1Contract,
    validity: EvaluationValidity | None = None,
) -> P1Receipt:
    """Evaluate P1 without inferring termination cause from candidate contents."""

    validity = validity or EvaluationValidity()
    if not _contract_is_valid(contract):
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P1_LOCAL_CONTRACT_INVALID",
        )
    if not validity.candidate_format_valid:
        return _receipt(
            contract,
            "candidate_format_invalid",
            "not_evaluated",
            "P1_CANDIDATE_FORMAT_INVALID",
        )
    if not validity.workspace_valid:
        return _receipt(
            contract,
            "workspace_invalid",
            "not_evaluated",
            "P1_WORKSPACE_INVALID",
        )
    if not validity.infrastructure_valid:
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P1_INFRASTRUCTURE_INVALID",
        )

    try:
        evidence = GenerationEvidence.parse(raw_evidence)
    except (TypeError, ValueError):
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P1_EVIDENCE_MALFORMED",
        )

    metadata = {
        "attempt_id": evidence.attempt_id,
        "source": evidence.source,
        "termination": evidence.termination.value,
        "generation_started": evidence.generation_started,
        "delivery_complete": evidence.delivery_complete,
        "diagnostic_sha256": _diagnostic_fingerprint(evidence.diagnostic),
    }
    if evidence.contract_version != contract.version:
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P1_CONTRACT_VERSION_MISMATCH",
            evidence=metadata,
        )
    if evidence.source not in contract.trusted_sources:
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P1_UNTRUSTED_EVIDENCE_SOURCE",
            evidence=metadata,
        )
    if not evidence.generation_started or not evidence.delivery_complete:
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P1_INCOMPLETE_GENERATION_EVIDENCE",
            evidence=metadata,
        )

    if evidence.termination is Termination.COMPLETED:
        return _receipt(
            contract,
            "scored",
            "passed",
            None,
            kernel=1,
            evidence=metadata,
        )
    if evidence.termination is Termination.MODEL_LIMIT:
        return _receipt(
            contract,
            "scored",
            "failed",
            "P1_CONTEXT_EXHAUSTED",
            kernel=-1,
            evidence=metadata,
        )
    if evidence.termination in {
        Termination.TRANSPORT_INTERRUPTED,
        Termination.PROVIDER_ERROR,
        Termination.CANCELLED,
    }:
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P1_NON_SEMANTIC_TERMINATION",
            evidence=metadata,
        )
    return _receipt(
        contract,
        "not_evaluated",
        "not_evaluated",
        "P1_TERMINATION_CAUSE_AMBIGUOUS",
        evidence=metadata,
    )
