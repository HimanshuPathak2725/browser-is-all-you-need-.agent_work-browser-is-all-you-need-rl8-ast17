"""P2 verifier for effective repair progress across comparable attempts.

P2 never scores a single candidate. It compares trusted normalized semantic
outcomes for a parent attempt and its direct repair attempt. Source changes,
diagnostic changes, and failure-message changes are not progress.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


RECEIPT_SCHEMA_VERSION = "w8-biayn-category-receipt-v1"
CATEGORY = "P2"
VERIFIER_ID = "repair-progress"


@dataclass(frozen=True)
class P2Contract:
    """Pinned contract for comparable repair evidence."""

    version: str
    task_id: str
    trusted_sources: frozenset[str]
    verifier_contracts: Mapping[str, str]
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.version.strip() or not self.task_id.strip():
            raise ValueError("contract identifiers must be non-empty")
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise ValueError("unsupported P2 contract schema")
        if not self.trusted_sources or any(
            type(source) is not str or not source.strip() for source in self.trusted_sources
        ):
            raise ValueError("the contract requires non-empty trusted sources")
        if not isinstance(self.verifier_contracts, Mapping) or not self.verifier_contracts:
            raise ValueError("the contract requires at least one comparable verifier")
        for verifier, version in self.verifier_contracts.items():
            if (
                type(verifier) is not str
                or type(version) is not str
                or not verifier.strip()
                or not version.strip()
                or "/" not in verifier
                or verifier.split("/", 1)[0] not in {"C1", "C2", "C3", "C4", "P1"}
            ):
                raise ValueError("invalid verifier contract")
        object.__setattr__(self, "trusted_sources", frozenset(self.trusted_sources))
        object.__setattr__(
            self, "verifier_contracts", MappingProxyType(dict(self.verifier_contracts))
        )


@dataclass(frozen=True)
class EvaluationValidity:
    candidate_format_valid: bool = True
    workspace_valid: bool = True
    infrastructure_valid: bool = True


@dataclass(frozen=True)
class AttemptSnapshot:
    attempt_id: str
    parent_attempt_id: str | None
    candidate_digest: str
    outcomes: Mapping[str, int]
    outcome_contract_versions: Mapping[str, str]
    consumed_feedback_id: str | None

    @classmethod
    def parse(cls, value: Any, *, current: bool) -> AttemptSnapshot:
        if not isinstance(value, Mapping):
            raise ValueError("attempt snapshot must be a mapping")
        required = {
            "attempt_id": str,
            "candidate_digest": str,
            "outcomes": Mapping,
            "outcome_contract_versions": Mapping,
        }
        for key, expected_type in required.items():
            if key not in value or not isinstance(value[key], expected_type):
                raise ValueError(f"invalid or missing attempt field: {key}")
        if not value["attempt_id"].strip() or not re.fullmatch(
            r"[0-9a-f]{64}", value["candidate_digest"]
        ):
            raise ValueError("attempt id must be non-empty and candidate digest must be SHA-256")
        parent = value.get("parent_attempt_id")
        if current and (type(parent) is not str or not parent.strip()):
            raise ValueError("current attempt requires a parent_attempt_id")
        if not current and parent is not None and (type(parent) is not str or not parent.strip()):
            raise ValueError("parent_attempt_id must be a string or null")
        consumed_feedback_id = value.get("consumed_feedback_id")
        if current and (type(consumed_feedback_id) is not str or not consumed_feedback_id.strip()):
            raise ValueError("current attempt requires a consumed_feedback_id")
        if not current and consumed_feedback_id is not None:
            raise ValueError("previous attempt cannot consume current repair feedback")
        outcomes: dict[str, int] = {}
        for key, kernel in value["outcomes"].items():
            if type(key) is not str or not key or type(kernel) is not int or kernel not in (-1, 1):
                raise ValueError("outcomes must map stable verifier keys to -1 or +1")
            outcomes[key] = kernel
        if not outcomes:
            raise ValueError("an attempt must contain at least one semantic outcome")
        versions: dict[str, str] = {}
        for key, version in value["outcome_contract_versions"].items():
            if type(key) is not str or type(version) is not str or not key or not version.strip():
                raise ValueError("outcome contract versions must be non-empty strings")
            versions[key] = version
        if set(versions) != set(outcomes):
            raise ValueError("every semantic outcome requires exactly one contract version")
        return cls(
            attempt_id=value["attempt_id"],
            parent_attempt_id=parent,
            candidate_digest=value["candidate_digest"],
            outcomes=outcomes,
            outcome_contract_versions=versions,
            consumed_feedback_id=consumed_feedback_id,
        )


@dataclass(frozen=True)
class RepairEvidence:
    schema_version: str
    contract_version: str
    source: str
    task_id: str
    lineage_id: str
    actionable_feedback: bool
    feedback_id: str
    feedback_for_attempt_id: str
    targets: tuple[str, ...]
    previous: AttemptSnapshot
    current: AttemptSnapshot
    diagnostic: str = ""

    @classmethod
    def parse(cls, value: Any) -> RepairEvidence:
        if not isinstance(value, Mapping):
            raise ValueError("repair evidence must be a mapping")
        required = {
            "schema_version": str,
            "contract_version": str,
            "source": str,
            "task_id": str,
            "lineage_id": str,
            "actionable_feedback": bool,
            "feedback_id": str,
            "feedback_for_attempt_id": str,
            "targets": list,
        }
        for key, expected_type in required.items():
            if key not in value or type(value[key]) is not expected_type:
                raise ValueError(f"invalid or missing repair field: {key}")
        if any(
            not value[key].strip()
            for key in (
                "schema_version",
                "contract_version",
                "source",
                "task_id",
                "lineage_id",
                "feedback_id",
                "feedback_for_attempt_id",
            )
        ):
            raise ValueError("repair identifiers must be non-empty")
        targets = value["targets"]
        if any(type(target) is not str or not target for target in targets):
            raise ValueError("repair targets must be non-empty strings")
        if len(targets) != len(set(targets)):
            raise ValueError("repair targets must be unique")
        diagnostic = value.get("diagnostic", "")
        if type(diagnostic) is not str:
            raise ValueError("diagnostic must be a string")
        return cls(
            schema_version=value["schema_version"],
            contract_version=value["contract_version"],
            source=value["source"],
            task_id=value["task_id"],
            lineage_id=value["lineage_id"],
            actionable_feedback=value["actionable_feedback"],
            feedback_id=value["feedback_id"],
            feedback_for_attempt_id=value["feedback_for_attempt_id"],
            targets=tuple(sorted(targets)),
            previous=AttemptSnapshot.parse(value.get("previous"), current=False),
            current=AttemptSnapshot.parse(value.get("current"), current=True),
            diagnostic=diagnostic,
        )


@dataclass(frozen=True)
class VerifierResult:
    verifier: str
    status: str
    kernel: int | None
    failure_code: str | None


@dataclass(frozen=True)
class P2Receipt:
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
            "evidence_invalid",
            "not_evaluated",
        }
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise ValueError("unsupported P2 receipt schema")
        if self.category != CATEGORY:
            raise ValueError("P2 receipt category must be P2")
        if self.disposition not in valid_dispositions:
            raise ValueError("invalid P2 receipt disposition")
        if len(self.verifier_results) != 1 or self.verifier_results[0].verifier != VERIFIER_ID:
            raise ValueError("P2 receipt must contain exactly the repair-progress verifier")
        if self.disposition == "scored":
            if self.kernels is None or len(self.kernels) != 1:
                raise ValueError("a scored P2 receipt must contain exactly one kernel")
            if self.kernels[0] not in (-1, 1):
                raise ValueError("semantic kernels must be -1 or +1")
            if self.category_score != float(self.kernels[0]):
                raise ValueError("P2 score must equal its sole kernel")
            result = self.verifier_results[0]
            expected_status = "passed" if self.kernels[0] == 1 else "failed"
            if result.kernel != self.kernels[0] or result.status != expected_status:
                raise ValueError("verifier result must agree with the P2 kernel")
            if self.kernels[0] == 1 and result.failure_code is not None:
                raise ValueError("a passing P2 result cannot contain a failure code")
            if self.kernels[0] == -1 and not result.failure_code:
                raise ValueError("a failing P2 result requires a failure code")
        elif self.kernels is not None or self.category_score is not None:
            raise ValueError("a non-scored receipt cannot contain reward values")
        else:
            result = self.verifier_results[0]
            if result.kernel is not None:
                raise ValueError("a non-scored verifier result cannot contain a kernel")
            if result.status != "not_evaluated":
                raise ValueError("a non-scored verifier result must be not_evaluated")
            if not result.failure_code:
                raise ValueError("a non-scored P2 result requires a failure code")

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


def _fingerprint(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _invalid_contract_receipt() -> P2Receipt:
    """Return a deterministic no-score receipt without trusting contract input."""

    return P2Receipt(
        schema_version=RECEIPT_SCHEMA_VERSION,
        category=CATEGORY,
        contract_version="invalid",
        disposition="contract_invalid",
        verifier_results=(
            VerifierResult(
                verifier=VERIFIER_ID,
                status="not_evaluated",
                kernel=None,
                failure_code="P2_CONTRACT_INVALID",
            ),
        ),
        kernels=None,
        category_score=None,
        evidence={},
    )


def _receipt(
    contract: P2Contract,
    disposition: str,
    status: str,
    failure_code: str | None,
    *,
    kernel: int | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> P2Receipt:
    scored = disposition == "scored"
    return P2Receipt(
        schema_version=contract.schema_version,
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


def evaluate_p2(
    raw_evidence: Any,
    contract: Any,
    validity: EvaluationValidity | None = None,
) -> P2Receipt:
    """Score only comparable, direct repair attempts with semantic evidence."""

    if type(contract) is not P2Contract:
        return _invalid_contract_receipt()

    validity = validity or EvaluationValidity()
    if not validity.candidate_format_valid:
        return _receipt(
            contract,
            "candidate_format_invalid",
            "not_evaluated",
            "P2_CANDIDATE_FORMAT_INVALID",
        )
    if not validity.workspace_valid:
        return _receipt(
            contract,
            "workspace_invalid",
            "not_evaluated",
            "P2_WORKSPACE_INVALID",
        )
    if not validity.infrastructure_valid:
        return _receipt(
            contract,
            "infrastructure_invalid",
            "not_evaluated",
            "P2_INFRASTRUCTURE_INVALID",
        )
    try:
        evidence = RepairEvidence.parse(raw_evidence)
    except (TypeError, ValueError):
        return _receipt(
            contract,
            "evidence_invalid",
            "not_evaluated",
            "P2_HISTORY_MALFORMED",
        )

    metadata = {
        "source": evidence.source,
        "task_id": evidence.task_id,
        "lineage_id": evidence.lineage_id,
        "previous_attempt_id": evidence.previous.attempt_id,
        "current_attempt_id": evidence.current.attempt_id,
        "feedback_id": evidence.feedback_id,
        "targets": list(evidence.targets),
        "diagnostic_sha256": _fingerprint(evidence.diagnostic),
    }
    if evidence.schema_version != contract.schema_version:
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P2_SCHEMA_VERSION_MISMATCH",
            evidence=metadata,
        )
    if evidence.contract_version != contract.version:
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P2_CONTRACT_VERSION_MISMATCH",
            evidence=metadata,
        )
    if evidence.source not in contract.trusted_sources:
        return _receipt(
            contract,
            "evidence_invalid",
            "not_evaluated",
            "P2_UNTRUSTED_HISTORY_SOURCE",
            evidence=metadata,
        )
    if evidence.task_id != contract.task_id:
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P2_TASK_ID_MISMATCH",
            evidence=metadata,
        )
    all_outcomes = set(evidence.previous.outcomes) | set(evidence.current.outcomes)
    if any(verifier not in contract.verifier_contracts for verifier in all_outcomes):
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P2_OUTCOME_OUTSIDE_CONTRACT",
            evidence=metadata,
        )
    for snapshot in (evidence.previous, evidence.current):
        if any(
            snapshot.outcome_contract_versions[verifier] != contract.verifier_contracts[verifier]
            for verifier in snapshot.outcomes
        ):
            return _receipt(
                contract,
                "contract_invalid",
                "not_evaluated",
                "P2_OUTCOME_CONTRACT_MISMATCH",
                evidence=metadata,
            )
    if any(target not in contract.verifier_contracts for target in evidence.targets):
        return _receipt(
            contract,
            "contract_invalid",
            "not_evaluated",
            "P2_TARGET_OUTSIDE_CONTRACT",
            evidence=metadata,
        )
    if (
        not evidence.actionable_feedback
        or not evidence.targets
        or evidence.feedback_for_attempt_id != evidence.previous.attempt_id
        or evidence.current.consumed_feedback_id != evidence.feedback_id
        or evidence.current.parent_attempt_id != evidence.previous.attempt_id
        or evidence.current.attempt_id == evidence.previous.attempt_id
    ):
        return _receipt(
            contract,
            "not_evaluated",
            "not_evaluated",
            "P2_REPAIR_HISTORY_INSUFFICIENT",
            evidence=metadata,
        )

    previous = evidence.previous.outcomes
    current = evidence.current.outcomes
    if any(target not in previous or target not in current for target in evidence.targets):
        return _receipt(
            contract,
            "not_evaluated",
            "not_evaluated",
            "P2_TARGET_OUTCOME_NOT_COMPARABLE",
            evidence=metadata,
        )
    if not any(previous[target] == -1 for target in evidence.targets):
        return _receipt(
            contract,
            "not_evaluated",
            "not_evaluated",
            "P2_NO_FAILED_REPAIR_TARGET",
            evidence=metadata,
        )

    disappeared = set(previous).difference(current)
    if disappeared:
        return _receipt(
            contract,
            "not_evaluated",
            "not_evaluated",
            "P2_SEMANTIC_OUTCOMES_NOT_COMPARABLE",
            evidence={**metadata, "missing_current_outcomes": sorted(disappeared)},
        )

    fixes = {
        target for target in evidence.targets if previous[target] == -1 and current[target] == 1
    }
    regressions = {key for key in previous if previous[key] == 1 and current[key] == -1}
    changed_candidate = evidence.previous.candidate_digest != evidence.current.candidate_digest

    result_metadata = {
        **metadata,
        "fixed_targets": sorted(fixes),
        "regressed_outcomes": sorted(regressions),
        "candidate_changed": changed_candidate,
    }
    if fixes and regressions:
        return _receipt(
            contract,
            "not_evaluated",
            "not_evaluated",
            "P2_MIXED_PROGRESS_AND_REGRESSION",
            evidence=result_metadata,
        )
    if fixes and not changed_candidate:
        return _receipt(
            contract,
            "evidence_invalid",
            "not_evaluated",
            "P2_NONDETERMINISTIC_OUTCOME_EVIDENCE",
            evidence=result_metadata,
        )
    if fixes:
        return _receipt(
            contract,
            "scored",
            "passed",
            None,
            kernel=1,
            evidence=result_metadata,
        )
    return _receipt(
        contract,
        "scored",
        "failed",
        "P2_NO_SEMANTIC_PROGRESS",
        kernel=-1,
        evidence=result_metadata,
    )
