"""Independent C3 verifier for C++ functional and behavioral correctness.

C3 is deliberately evaluated only after a non-reward-bearing build/applicability
gate succeeds.  A trusted, versioned oracle then reports every required
behavioral case through a strict machine-readable protocol.  The module never
links compiler diagnostics, test names, or partial case counts to reward.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import string
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

C3_SCHEMA_VERSION = "c3-receipt-v1"
C3_CONTRACT_SCHEMA_VERSION = "c3-contract-v1"
C3_ORACLE_REPORT_SCHEMA_VERSION = "c3-oracle-report-v1"
C3_VERIFIER_ID = "functional-behavior"
_MAX_REPORT_BYTES = 1_048_576
_MAX_DIAGNOSTIC_TAIL_BYTES = 16_384
_ALLOWED_PLACEHOLDERS = frozenset({"workspace", "oracle_artifact"})


class C3Disposition(str, Enum):
    """Scored and non-scored C3 receipt dispositions."""

    SCORED = "scored"
    CANDIDATE_FORMAT_INVALID = "candidate_format_invalid"
    WORKSPACE_INVALID = "workspace_invalid"
    INFRASTRUCTURE_INVALID = "infrastructure_invalid"
    CONTRACT_INVALID = "contract_invalid"
    NOT_EVALUATED = "not_evaluated"


class MaterializationStatus(str, Enum):
    """Cause established by candidate response/materialization infrastructure."""

    VALID = "valid"
    CANDIDATE_FORMAT_INVALID = "candidate_format_invalid"
    WORKSPACE_INVALID = "workspace_invalid"
    INFRASTRUCTURE_INVALID = "infrastructure_invalid"


class CommandTermination(str, Enum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    EXECUTABLE_MISSING = "executable_missing"
    SPAWN_FAILED = "spawn_failed"
    SIGNALLED = "signalled"


@dataclass(frozen=True)
class CommandObservation:
    """Outcome from a command runner; output is diagnostic evidence only."""

    termination: CommandTermination
    returncode: int | None = None
    stdout_sha256: str = field(default_factory=lambda: _sha256_bytes(b""))
    stderr_sha256: str = field(default_factory=lambda: _sha256_bytes(b""))
    stdout_tail: str = ""
    stderr_tail: str = ""
    output_truncated: bool = False
    oracle_report_trusted: bool = False

    @classmethod
    def completed(
        cls,
        returncode: int,
        *,
        stdout: str = "",
        stderr: str = "",
        oracle_report_trusted: bool = False,
    ) -> CommandObservation:
        termination = (
            CommandTermination.SIGNALLED if returncode < 0 else CommandTermination.COMPLETED
        )
        stdout_bytes = stdout.encode("utf-8", errors="replace")
        stderr_bytes = stderr.encode("utf-8", errors="replace")
        return cls(
            termination=termination,
            returncode=returncode,
            stdout_sha256=_sha256_bytes(stdout_bytes),
            stderr_sha256=_sha256_bytes(stderr_bytes),
            stdout_tail=_decode_tail(stdout_bytes),
            stderr_tail=_decode_tail(stderr_bytes),
            output_truncated=(
                len(stdout_bytes) > _MAX_DIAGNOSTIC_TAIL_BYTES
                or len(stderr_bytes) > _MAX_DIAGNOSTIC_TAIL_BYTES
            ),
            oracle_report_trusted=oracle_report_trusted,
        )

    def to_evidence(self) -> dict[str, Any]:
        return {
            "termination": self.termination.value,
            "returncode": self.returncode,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "output_truncated": self.output_truncated,
            "oracle_report_trusted": self.oracle_report_trusted,
        }


class CommandRunner(Protocol):
    """Injection boundary for the repository's outer sandbox/executor."""

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: Mapping[str, str] | None = None,
    ) -> CommandObservation: ...


class SubprocessCommandRunner:
    """Bounded, shell-free local runner intended to live inside an outer sandbox."""

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: Mapping[str, str] | None = None,
    ) -> CommandObservation:
        merged_env = {
            "LANG": "C",
            "LANGUAGE": "C",
            "LC_ALL": "C",
            "PATH": os.defpath,
            "TZ": "UTC",
        }
        merged_env.update({str(key): str(value) for key, value in (env or {}).items()})
        try:
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    [str(part) for part in command],
                    cwd=cwd,
                    env=merged_env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    start_new_session=True,
                )
                termination = CommandTermination.COMPLETED
                try:
                    returncode = process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    termination = CommandTermination.TIMED_OUT
                    _terminate_process_group(process)
                    returncode = process.returncode

                if termination is CommandTermination.COMPLETED and returncode < 0:
                    termination = CommandTermination.SIGNALLED
                stdout_sha256, stdout_tail, stdout_truncated = _summarize_file(stdout_file)
                stderr_sha256, stderr_tail, stderr_truncated = _summarize_file(stderr_file)
                return CommandObservation(
                    termination=termination,
                    returncode=returncode,
                    stdout_sha256=stdout_sha256,
                    stderr_sha256=stderr_sha256,
                    stdout_tail=stdout_tail,
                    stderr_tail=stderr_tail,
                    output_truncated=stdout_truncated or stderr_truncated,
                )
        except FileNotFoundError:
            return CommandObservation(termination=CommandTermination.EXECUTABLE_MISSING)
        except OSError as exc:
            evidence = str(exc).encode("utf-8", errors="replace")
            return CommandObservation(
                termination=CommandTermination.SPAWN_FAILED,
                stderr_sha256=_sha256_bytes(evidence),
                stderr_tail=_decode_tail(evidence),
            )


@dataclass(frozen=True)
class BehavioralContract:
    """Pinned behavioral oracle contract supplied by the task package."""

    contract_version: str
    oracle_id: str
    oracle_version: str
    oracle_artifact: Path
    oracle_artifact_sha256: str
    required_case_ids: tuple[str, ...]
    required_candidate_paths: tuple[str, ...]
    build_command: tuple[str, ...]
    oracle_command: tuple[str, ...]
    build_timeout_seconds: float = 120.0
    oracle_timeout_seconds: float = 120.0
    schema_version: str = C3_CONTRACT_SCHEMA_VERSION

    def validation_error(self) -> str | None:
        if self.schema_version != C3_CONTRACT_SCHEMA_VERSION:
            return "unsupported_contract_schema"
        for field_name, value in (
            ("contract_version", self.contract_version),
            ("oracle_id", self.oracle_id),
            ("oracle_version", self.oracle_version),
        ):
            if not value or value.strip() != value:
                return f"invalid_{field_name}"
        if not self.oracle_artifact.is_absolute():
            return "oracle_artifact_must_be_absolute"
        if not self.oracle_artifact.is_file() or self.oracle_artifact.is_symlink():
            return "oracle_artifact_missing_or_untrusted"
        if not _is_sha256(self.oracle_artifact_sha256):
            return "invalid_oracle_artifact_sha256"
        if _sha256_file(self.oracle_artifact) != self.oracle_artifact_sha256:
            return "oracle_artifact_digest_mismatch"
        if not self.required_case_ids:
            return "required_cases_empty"
        if any(not case_id or case_id.strip() != case_id for case_id in self.required_case_ids):
            return "invalid_required_case_id"
        if len(set(self.required_case_ids)) != len(self.required_case_ids):
            return "duplicate_required_case_id"
        if len(set(self.required_candidate_paths)) != len(self.required_candidate_paths):
            return "duplicate_required_candidate_path"
        for path in self.required_candidate_paths:
            if not _valid_relative_path(path):
                return "invalid_required_candidate_path"
        for name, command in (
            ("build_command", self.build_command),
            ("oracle_command", self.oracle_command),
        ):
            command_error = _validate_command(command)
            if command_error:
                return f"{name}_{command_error}"
        if not (0 < self.build_timeout_seconds <= 3600):
            return "invalid_build_timeout"
        if not (0 < self.oracle_timeout_seconds <= 3600):
            return "invalid_oracle_timeout"
        return None

    @property
    def identity_digest(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "oracle_id": self.oracle_id,
            "oracle_version": self.oracle_version,
            "oracle_artifact_sha256": self.oracle_artifact_sha256,
            "required_case_ids": sorted(self.required_case_ids),
            "required_candidate_paths": sorted(self.required_candidate_paths),
            "build_command": list(self.build_command),
            "oracle_command": list(self.oracle_command),
            "build_timeout_seconds": self.build_timeout_seconds,
            "oracle_timeout_seconds": self.oracle_timeout_seconds,
        }
        return _sha256_bytes(_canonical_json_bytes(payload))

    def expand_command(self, command: Sequence[str], workspace: Path) -> tuple[str, ...]:
        values = {
            "workspace": str(workspace),
            "oracle_artifact": str(self.oracle_artifact),
        }
        return tuple(part.format_map(values) for part in command)


@dataclass(frozen=True)
class C3EvaluationContext:
    """Cause-aware input from response parsing and workspace materialization."""

    workspace: Path
    task_contract_version: str
    candidate_response_valid: bool = True
    materialization_status: MaterializationStatus = MaterializationStatus.VALID
    materialization_evidence: str = ""


@dataclass(frozen=True)
class C3VerifierResult:
    verifier: str
    status: str
    kernel: int | None
    failure_code: str | None
    phase: str
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.verifier != C3_VERIFIER_ID:
            raise ValueError("unexpected C3 verifier id")
        if self.kernel not in (-1, 1, None):
            raise ValueError("C3 semantic kernels must be exactly -1 or +1")
        if self.kernel == 1 and (self.status != "passed" or self.failure_code is not None):
            raise ValueError("passing C3 result is inconsistent")
        if self.kernel == -1 and (self.status != "failed" or not self.failure_code):
            raise ValueError("failing C3 result is inconsistent")
        if self.kernel is None and self.status not in {"invalid", "not_evaluated"}:
            raise ValueError("non-scored C3 result is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": self.verifier,
            "status": self.status,
            "kernel": self.kernel,
            "failure_code": self.failure_code,
            "phase": self.phase,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class C3Receipt:
    schema_version: str
    category: str
    disposition: C3Disposition
    verifier_results: tuple[C3VerifierResult, ...]
    category_score: int | None
    contract_version: str
    contract_digest: str | None
    oracle_id: str
    oracle_version: str

    def __post_init__(self) -> None:
        if self.schema_version != C3_SCHEMA_VERSION or self.category != "C3":
            raise ValueError("invalid C3 receipt identity")
        if len(self.verifier_results) != 1:
            raise ValueError("C3 has exactly one reward-bearing verifier")
        kernel = self.verifier_results[0].kernel
        if self.disposition is C3Disposition.SCORED:
            if kernel not in (-1, 1) or self.category_score != kernel:
                raise ValueError("scored C3 receipt must have category_score == kernel")
        elif kernel is not None or self.category_score is not None:
            raise ValueError("non-scored C3 receipt cannot contain reward")
        else:
            expected_status = (
                "not_evaluated" if self.disposition is C3Disposition.NOT_EVALUATED else "invalid"
            )
            if self.verifier_results[0].status != expected_status:
                raise ValueError("C3 disposition and verifier status disagree")

    @property
    def kernels(self) -> tuple[int, ...] | None:
        kernel = self.verifier_results[0].kernel
        return (kernel,) if kernel is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "category": self.category,
            "disposition": self.disposition.value,
            "verifier_results": [result.to_dict() for result in self.verifier_results],
            "kernels": list(self.kernels) if self.kernels is not None else None,
            "category_score": self.category_score,
            "contract_version": self.contract_version,
            "contract_digest": self.contract_digest,
            "oracle_id": self.oracle_id,
            "oracle_version": self.oracle_version,
        }


def evaluate_c3(
    context: C3EvaluationContext,
    contract: BehavioralContract,
    *,
    runner: CommandRunner | None = None,
) -> C3Receipt:
    """Evaluate one C3 verifier without linking diagnostics to its kernel."""

    contract_error = contract.validation_error()
    if contract_error:
        return _unscored(
            contract,
            C3Disposition.CONTRACT_INVALID,
            f"C3_{contract_error.upper()}",
            "contract_validation",
            {},
        )
    if context.task_contract_version != contract.contract_version:
        return _unscored(
            contract,
            C3Disposition.CONTRACT_INVALID,
            "C3_CONTRACT_VERSION_MISMATCH",
            "contract_validation",
            {
                "expected_version_sha256": _sha256_text(contract.contract_version),
                "observed_version_sha256": _sha256_text(context.task_contract_version),
            },
        )

    if not context.candidate_response_valid:
        return _unscored(
            contract,
            C3Disposition.CANDIDATE_FORMAT_INVALID,
            "C3_CANDIDATE_FORMAT_INVALID",
            "candidate_validation",
            {"materialization_evidence_sha256": _sha256_text(context.materialization_evidence)},
        )
    if context.materialization_status is not MaterializationStatus.VALID:
        disposition = {
            MaterializationStatus.CANDIDATE_FORMAT_INVALID: (
                C3Disposition.CANDIDATE_FORMAT_INVALID
            ),
            MaterializationStatus.WORKSPACE_INVALID: C3Disposition.WORKSPACE_INVALID,
            MaterializationStatus.INFRASTRUCTURE_INVALID: (C3Disposition.INFRASTRUCTURE_INVALID),
        }[context.materialization_status]
        return _unscored(
            contract,
            disposition,
            f"C3_{context.materialization_status.value.upper()}",
            "materialization",
            {"materialization_evidence_sha256": _sha256_text(context.materialization_evidence)},
        )

    workspace_error = _workspace_validation_error(context.workspace, contract)
    if workspace_error:
        return _unscored(
            contract,
            C3Disposition.WORKSPACE_INVALID,
            f"C3_{workspace_error.upper()}",
            "workspace_validation",
            {},
        )
    workspace = context.workspace.resolve()

    if _is_relative_to(contract.oracle_artifact.resolve(), workspace):
        return _unscored(
            contract,
            C3Disposition.CONTRACT_INVALID,
            "C3_ORACLE_INSIDE_CANDIDATE_WORKSPACE",
            "contract_validation",
            {},
        )

    if runner is None:
        return _unscored(
            contract,
            C3Disposition.INFRASTRUCTURE_INVALID,
            "C3_SANDBOX_RUNNER_REQUIRED",
            "execution_setup",
            {"required_capability": "sandboxed-command-runner"},
        )

    command_runner = runner
    common_env = {
        "W8_C3_CONTRACT_DIGEST": contract.identity_digest,
        "W8_C3_CONTRACT_VERSION": contract.contract_version,
        "W8_C3_ORACLE_ID": contract.oracle_id,
        "W8_C3_ORACLE_VERSION": contract.oracle_version,
    }
    build = command_runner.run(
        contract.expand_command(contract.build_command, workspace),
        cwd=workspace,
        timeout_seconds=contract.build_timeout_seconds,
        env=common_env,
    )
    if build.termination is not CommandTermination.COMPLETED:
        return _unscored(
            contract,
            C3Disposition.INFRASTRUCTURE_INVALID,
            f"C3_BUILD_{build.termination.value.upper()}",
            "build_applicability",
            {"build": build.to_evidence()},
        )
    if build.returncode != 0:
        return _unscored(
            contract,
            C3Disposition.NOT_EVALUATED,
            "C3_BUILD_APPLICABILITY_FAILED",
            "build_applicability",
            {
                "blocking_owners": ["C1", "C2", "C4"],
                "build": build.to_evidence(),
            },
        )

    with tempfile.TemporaryDirectory(prefix="w8-c3-oracle-") as report_dir_name:
        report_path = Path(report_dir_name) / "behavior-report.json"
        oracle_env = dict(common_env)
        oracle_env["W8_C3_REPORT_PATH"] = str(report_path)
        oracle = command_runner.run(
            contract.expand_command(contract.oracle_command, workspace),
            cwd=workspace,
            timeout_seconds=contract.oracle_timeout_seconds,
            env=oracle_env,
        )
        if oracle.termination is not CommandTermination.COMPLETED:
            return _unscored(
                contract,
                C3Disposition.INFRASTRUCTURE_INVALID,
                f"C3_ORACLE_{oracle.termination.value.upper()}",
                "behavior_oracle",
                {"build": build.to_evidence(), "oracle": oracle.to_evidence()},
            )
        if oracle.returncode != 0:
            return _unscored(
                contract,
                C3Disposition.INFRASTRUCTURE_INVALID,
                "C3_ORACLE_PROTOCOL_FAILURE",
                "behavior_oracle",
                {"build": build.to_evidence(), "oracle": oracle.to_evidence()},
            )
        if not oracle.oracle_report_trusted:
            return _unscored(
                contract,
                C3Disposition.INFRASTRUCTURE_INVALID,
                "C3_ORACLE_REPORT_CHANNEL_UNTRUSTED",
                "behavior_oracle",
                {"build": build.to_evidence(), "oracle": oracle.to_evidence()},
            )
        report, report_error, report_digest = _read_oracle_report(report_path, contract)
        if report_error or report is None:
            return _unscored(
                contract,
                C3Disposition.INFRASTRUCTURE_INVALID,
                f"C3_ORACLE_REPORT_{(report_error or 'INVALID').upper()}",
                "behavior_oracle",
                {
                    "build": build.to_evidence(),
                    "oracle": oracle.to_evidence(),
                    "report_sha256": report_digest,
                },
            )

    case_results = {str(case["id"]): bool(case["passed"]) for case in report["cases"]}
    failed_cases = sorted(case_id for case_id, passed in case_results.items() if not passed)
    kernel = 1 if not failed_cases else -1
    status = "passed" if kernel == 1 else "failed"
    failure_code = None if kernel == 1 else "C3_BEHAVIOR_MISMATCH"
    evidence = {
        "build_gate": "passed",
        "build": build.to_evidence(),
        "oracle": oracle.to_evidence(),
        "oracle_report_sha256": report_digest,
        "required_case_count": len(contract.required_case_ids),
        "failed_case_ids": failed_cases,
    }
    result = C3VerifierResult(
        verifier=C3_VERIFIER_ID,
        status=status,
        kernel=kernel,
        failure_code=failure_code,
        phase="behavior_oracle",
        evidence=evidence,
    )
    return C3Receipt(
        schema_version=C3_SCHEMA_VERSION,
        category="C3",
        disposition=C3Disposition.SCORED,
        verifier_results=(result,),
        category_score=kernel,
        contract_version=contract.contract_version,
        contract_digest=contract.identity_digest,
        oracle_id=contract.oracle_id,
        oracle_version=contract.oracle_version,
    )


def _unscored(
    contract: BehavioralContract,
    disposition: C3Disposition,
    failure_code: str,
    phase: str,
    evidence: Mapping[str, Any],
) -> C3Receipt:
    result = C3VerifierResult(
        verifier=C3_VERIFIER_ID,
        status="not_evaluated" if disposition is C3Disposition.NOT_EVALUATED else "invalid",
        kernel=None,
        failure_code=failure_code,
        phase=phase,
        evidence=evidence,
    )
    contract_digest = None
    if contract.validation_error() is None:
        contract_digest = contract.identity_digest
    return C3Receipt(
        schema_version=C3_SCHEMA_VERSION,
        category="C3",
        disposition=disposition,
        verifier_results=(result,),
        category_score=None,
        contract_version=contract.contract_version,
        contract_digest=contract_digest,
        oracle_id=contract.oracle_id,
        oracle_version=contract.oracle_version,
    )


def _read_oracle_report(
    report_path: Path,
    contract: BehavioralContract,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    try:
        if report_path.is_symlink() or not report_path.is_file():
            return None, "missing", None
        size = report_path.stat().st_size
        if size > _MAX_REPORT_BYTES:
            return None, "oversized", None
        raw = report_path.read_bytes()
    except OSError:
        return None, "unreadable", None
    digest = _sha256_bytes(raw)
    try:
        report = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "malformed", digest
    if not isinstance(report, dict):
        return None, "not_object", digest
    identity = {
        "schema_version": C3_ORACLE_REPORT_SCHEMA_VERSION,
        "contract_version": contract.contract_version,
        "contract_digest": contract.identity_digest,
        "oracle_id": contract.oracle_id,
        "oracle_version": contract.oracle_version,
    }
    for key, expected in identity.items():
        if report.get(key) != expected:
            return None, f"identity_{key}_mismatch", digest
    cases = report.get("cases")
    if not isinstance(cases, list):
        return None, "cases_missing", digest
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            return None, "case_not_object", digest
        case_id = case.get("id")
        passed = case.get("passed")
        if not isinstance(case_id, str) or not case_id or not isinstance(passed, bool):
            return None, "case_invalid", digest
        if case_id in seen:
            return None, "case_duplicate", digest
        seen.add(case_id)
    if seen != set(contract.required_case_ids):
        return None, "case_set_mismatch", digest
    return report, None, digest


def _workspace_validation_error(
    workspace: Path,
    contract: BehavioralContract,
) -> str | None:
    if workspace.is_symlink() or not workspace.is_dir():
        return "workspace_missing_or_untrusted"
    root = workspace.resolve()
    for relative in contract.required_candidate_paths:
        if not _valid_relative_path(relative):
            return "required_candidate_path_invalid"
        candidate = root / relative
        if not candidate.exists() or candidate.is_symlink():
            return "required_candidate_path_missing"
        if not _is_relative_to(candidate.resolve(), root):
            return "required_candidate_path_escape"
    return None


def _validate_command(command: Sequence[str]) -> str | None:
    if not command:
        return "empty"
    formatter = string.Formatter()
    for part in command:
        if not isinstance(part, str) or not part or "\x00" in part:
            return "invalid_part"
        try:
            fields = {field for _, field, _, _ in formatter.parse(part) if field is not None}
        except ValueError:
            return "invalid_format"
        if not fields.issubset(_ALLOWED_PLACEHOLDERS):
            return "unsupported_placeholder"
    try:
        executable = command[0].format_map(
            {"workspace": "/candidate", "oracle_artifact": "/trusted/oracle"}
        )
    except (KeyError, ValueError):
        return "invalid_executable"
    if not Path(executable).is_absolute():
        return "executable_not_absolute"
    return None


def _valid_relative_path(value: str) -> bool:
    if not value or "\x00" in value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and path.as_posix() == value


def _terminate_process_group(process: subprocess.Popen[Any]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def _summarize_file(file: Any) -> tuple[str, str, bool]:
    file.seek(0)
    digest = hashlib.sha256()
    tail = bytearray()
    size = 0
    while True:
        chunk = file.read(65_536)
        if not chunk:
            break
        size += len(chunk)
        digest.update(chunk)
        tail.extend(chunk)
        if len(tail) > _MAX_DIAGNOSTIC_TAIL_BYTES:
            del tail[: len(tail) - _MAX_DIAGNOSTIC_TAIL_BYTES]
    return digest.hexdigest(), _decode_tail(bytes(tail)), size > _MAX_DIAGNOSTIC_TAIL_BYTES


def _decode_tail(value: bytes) -> str:
    return value[-_MAX_DIAGNOSTIC_TAIL_BYTES:].decode("utf-8", errors="replace")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8", errors="replace"))


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
