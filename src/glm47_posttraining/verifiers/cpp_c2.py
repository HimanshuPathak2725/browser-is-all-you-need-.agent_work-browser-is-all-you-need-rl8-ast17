"""Independent C2 (compile-time implementation correctness) verifier.

The verifier compiles complete candidate translation units to object files.  A
successful translation is immediately a C2 pass.  A failed translation is a
C2 failure only after two non-reward-bearing compiler gates rule out public
declaration (C1) and definition-binding (C4) ownership.

This module deliberately does not link or execute candidate code.  The local
subprocess runner is intended to run inside the repository's outer task
sandbox/container; callers can inject a stricter command runner without
changing the verifier semantics.

Namespace-scope initializer failures and unresolved angle-bracket dependencies
remain unscored: without a task-pinned definition-owner/dependency manifest,
neutralizing them could hide C4 or environment ownership.  This is intentional
fail-closed behavior rather than diagnostic-based guessing.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Protocol

C2_SCHEMA_VERSION = "c2-receipt-v1"
C2_CATEGORY = "C2"
C2_VERIFIER_ID = "implementation-translation"
_MAX_CANDIDATE_FILES = 256
_MAX_CANDIDATE_BYTES = 4 * 1024 * 1024
_MAX_DIAGNOSTIC_CHARS = 12_000
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_QUOTED_INCLUDE_RE = re.compile(r'^\s*\#\s*include\s*"(?P<path>[^"\r\n]+)"', re.MULTILINE)

Disposition = Literal[
    "scored",
    "candidate_format_invalid",
    "workspace_invalid",
    "infrastructure_invalid",
    "contract_invalid",
    "not_evaluated",
]
Status = Literal["passed", "failed", "invalid", "not_evaluated"]
InfrastructureFailure = Literal["unavailable", "timeout", "sandbox", "runner"]


@dataclass(frozen=True)
class CompilerProfile:
    """Pinned translation profile supplied by the task integration."""

    profile_id: str
    executable: str
    expected_identity: str
    arguments: tuple[str, ...]
    include_directories: tuple[str, ...] = (".",)
    timeout_seconds: float = 30.0

    def receipt(self, actual_identity: str | None = None) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "executable": self.executable,
            "expected_identity": self.expected_identity,
            "actual_identity": actual_identity,
            "arguments": list(self.arguments),
            "include_directories": list(self.include_directories),
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class C2Contract:
    """Task-owned inputs needed to evaluate implementation translation."""

    contract_version: str
    compiler: CompilerProfile
    required_files: tuple[str, ...]
    implementation_files: tuple[str, ...]
    public_declaration_probe: str


@dataclass(frozen=True)
class C2Candidate:
    """Parsed candidate response at the C2 integration boundary."""

    contract_version: str
    files: Mapping[str, str]


@dataclass(frozen=True)
class CommandOutcome:
    """Deterministic command result; infrastructure failures have no return code."""

    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    infrastructure_failure: InfrastructureFailure | None = None
    infrastructure_detail: str = ""


class CommandRunner(Protocol):
    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome: ...


class SubprocessCommandRunner:
    """No-shell subprocess runner for use inside an existing outer sandbox."""

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        try:
            completed = subprocess.run(
                [str(part) for part in command],
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            return CommandOutcome(
                returncode=None,
                infrastructure_failure="unavailable",
                infrastructure_detail=str(exc),
            )
        except subprocess.TimeoutExpired as exc:
            return CommandOutcome(
                returncode=None,
                stdout=_coerce_process_text(exc.stdout),
                stderr=_coerce_process_text(exc.stderr),
                infrastructure_failure="timeout",
                infrastructure_detail=f"command exceeded {timeout_seconds:g}s",
            )
        except OSError as exc:
            return CommandOutcome(
                returncode=None,
                infrastructure_failure="runner",
                infrastructure_detail=f"{type(exc).__name__}: {exc}",
            )
        if completed.returncode < 0:
            return CommandOutcome(
                returncode=None,
                stdout=completed.stdout,
                stderr=completed.stderr,
                infrastructure_failure="runner",
                infrastructure_detail=f"compiler terminated by signal {-completed.returncode}",
            )
        return CommandOutcome(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True)
class C2Receipt:
    schema_version: str
    category: str
    disposition: Disposition
    verifier: str
    status: Status
    kernel: int | None
    category_score: int | None
    attribution: dict[str, Any]
    compiler_profile: dict[str, Any]
    compile_phase: dict[str, Any]
    failure_code: str | None
    diagnostic: str
    contract_version: str

    def __post_init__(self) -> None:
        valid_dispositions = {
            "scored",
            "candidate_format_invalid",
            "workspace_invalid",
            "infrastructure_invalid",
            "contract_invalid",
            "not_evaluated",
        }
        if self.disposition not in valid_dispositions:
            raise ValueError("C2 receipt disposition is invalid")
        if self.schema_version != C2_SCHEMA_VERSION:
            raise ValueError("C2 receipt schema_version is unsupported")
        if self.category != C2_CATEGORY:
            raise ValueError("C2 receipt category is invalid")
        if self.verifier != C2_VERIFIER_ID:
            raise ValueError("C2 receipt verifier id is invalid")
        if not isinstance(self.contract_version, str) or not self.contract_version:
            raise ValueError("C2 receipt requires a contract version")
        required_gates = {"declaration_surface", "definition_binding"}
        if set(self.attribution) != required_gates or any(
            not isinstance(self.attribution[gate], Mapping)
            or self.attribution[gate].get("reward_bearing") is not False
            for gate in required_gates
        ):
            raise ValueError("C2 attribution gates must exist and be non-reward-bearing")
        if self.disposition == "scored":
            if type(self.kernel) is not int or self.kernel not in (-1, 1):
                raise ValueError("A scored C2 receipt must have a {-1,+1} kernel")
            if type(self.category_score) is not int or self.category_score != self.kernel:
                raise ValueError("With one C2 verifier, category_score must equal kernel")
            expected_status = "passed" if self.kernel == 1 else "failed"
            if self.status != expected_status:
                raise ValueError("C2 status and kernel disagree")
            if self.kernel == 1 and self.failure_code is not None:
                raise ValueError("A passing C2 receipt must not contain a failure code")
            if self.kernel == -1 and self.failure_code != "C2_TRANSLATION_FAILURE":
                raise ValueError("A failing C2 receipt requires the semantic C2 failure code")
        else:
            if self.kernel is not None or self.category_score is not None:
                raise ValueError("A non-scored C2 receipt must not contain reward values")
            expected_status = "not_evaluated" if self.disposition == "not_evaluated" else "invalid"
            if self.status != expected_status:
                raise ValueError("C2 non-scored disposition and status disagree")
            if not self.failure_code:
                raise ValueError("A non-scored C2 receipt requires a failure code")

    @property
    def kernels(self) -> tuple[int, ...] | None:
        return (self.kernel,) if self.kernel is not None else None

    @property
    def verifier_results(self) -> tuple[dict[str, Any], ...]:
        return (
            {
                "verifier": self.verifier,
                "status": self.status,
                "kernel": self.kernel,
                "phase": self.compile_phase.get("phase"),
                "failure_code": self.failure_code,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["verifier_results"] = [dict(item) for item in self.verifier_results]
        result["kernels"] = list(self.kernels) if self.kernels is not None else None
        return result


@dataclass(frozen=True)
class _CompileBatch:
    status: Literal["passed", "failed", "infrastructure_invalid"]
    records: tuple[dict[str, Any], ...]
    diagnostic: str
    infrastructure_failure: InfrastructureFailure | None = None
    infrastructure_detail: str = ""


@dataclass(frozen=True)
class _Neutralization:
    status: Literal["confident", "ambiguous", "infrastructure_invalid"]
    source: bytes | None
    body_count: int
    removed_missing_includes: tuple[str, ...]
    detail: str = ""


class C2ImplementationTranslationVerifier:
    """Exactly one reward-bearing C2 verifier with internal ownership gates."""

    def __init__(
        self,
        *,
        expected_contract_version: str,
        runner: CommandRunner | None = None,
        scratch_root: str | Path | None = None,
    ) -> None:
        self.expected_contract_version = expected_contract_version
        self.runner = runner or SubprocessCommandRunner()
        self.scratch_root = Path(scratch_root) if scratch_root is not None else None

    def evaluate_candidate(
        self,
        candidate_response: C2Candidate | Mapping[str, Any] | object,
        contract: C2Contract,
    ) -> C2Receipt:
        """Validate, materialize, and evaluate a structured candidate response."""

        contract_error = _validate_contract(contract, self.expected_contract_version)
        if contract_error:
            return self._unscored(
                contract,
                disposition="contract_invalid",
                failure_code="CONTRACT_INVALID",
                diagnostic=contract_error,
            )
        candidate, candidate_error, contract_mismatch = _parse_candidate(candidate_response)
        if contract_mismatch:
            return self._unscored(
                contract,
                disposition="contract_invalid",
                failure_code="CONTRACT_VERSION_MISMATCH",
                diagnostic=contract_mismatch,
            )
        if candidate_error or candidate is None:
            return self._unscored(
                contract,
                disposition="candidate_format_invalid",
                failure_code="CANDIDATE_FORMAT_INVALID",
                diagnostic=candidate_error or "candidate could not be parsed",
            )
        if candidate.contract_version != contract.contract_version:
            return self._unscored(
                contract,
                disposition="contract_invalid",
                failure_code="CONTRACT_VERSION_MISMATCH",
                diagnostic=("candidate contract version does not match the supplied task contract"),
            )
        missing = sorted(set(contract.required_files) - set(candidate.files))
        if missing:
            return self._unscored(
                contract,
                disposition="candidate_format_invalid",
                failure_code="CANDIDATE_REQUIRED_FILE_OMITTED",
                diagnostic=f"candidate omitted required files: {', '.join(missing)}",
            )
        try:
            with tempfile.TemporaryDirectory(
                prefix="w8-c2-candidate-", dir=self.scratch_root
            ) as temporary:
                workspace = Path(temporary) / "workspace"
                workspace.mkdir()
                _materialize_candidate(candidate.files, workspace)
                return self._evaluate_workspace(contract, workspace)
        except (OSError, UnicodeError) as exc:
            return self._unscored(
                contract,
                disposition="workspace_invalid",
                failure_code="WORKSPACE_MATERIALIZATION_FAILED",
                diagnostic=f"{type(exc).__name__}: {exc}",
            )

    def evaluate_workspace(
        self,
        workspace: str | Path,
        contract: C2Contract,
        *,
        candidate_contract_version: str,
    ) -> C2Receipt:
        """Evaluate a generic-infrastructure materialized candidate workspace."""

        contract_error = _validate_contract(contract, self.expected_contract_version)
        if contract_error:
            return self._unscored(
                contract,
                disposition="contract_invalid",
                failure_code="CONTRACT_INVALID",
                diagnostic=contract_error,
            )
        if candidate_contract_version != contract.contract_version:
            return self._unscored(
                contract,
                disposition="contract_invalid",
                failure_code="CONTRACT_VERSION_MISMATCH",
                diagnostic="materialized candidate contract version does not match",
            )
        return self._evaluate_workspace(contract, Path(workspace))

    def _evaluate_workspace(self, contract: C2Contract, workspace: Path) -> C2Receipt:
        workspace_error = _validate_workspace(workspace, contract.required_files)
        if workspace_error:
            return self._unscored(
                contract,
                disposition="workspace_invalid",
                failure_code="WORKSPACE_INVALID",
                diagnostic=workspace_error,
            )
        include_error = _validate_local_include_paths(workspace, contract.implementation_files)
        if include_error:
            return self._unscored(
                contract,
                disposition="candidate_format_invalid",
                failure_code="UNSAFE_CANDIDATE_INCLUDE_PATH",
                diagnostic=include_error,
            )

        identity_outcome = self.runner.run(
            (contract.compiler.executable, "--version"),
            cwd=workspace,
            env=_compiler_environment(),
            timeout_seconds=contract.compiler.timeout_seconds,
        )
        identity_error = _infrastructure_error(identity_outcome)
        if identity_error:
            code, detail = identity_error
            return self._unscored(
                contract,
                disposition="infrastructure_invalid",
                failure_code=code,
                diagnostic=detail,
            )
        if identity_outcome.returncode != 0:
            return self._unscored(
                contract,
                disposition="infrastructure_invalid",
                failure_code="COMPILER_IDENTITY_COMMAND_FAILED",
                diagnostic=_outcome_text(identity_outcome),
            )
        actual_identity = _first_nonempty_line(identity_outcome.stdout)
        if actual_identity != contract.compiler.expected_identity:
            return self._unscored(
                contract,
                disposition="infrastructure_invalid",
                failure_code="COMPILER_IDENTITY_MISMATCH",
                diagnostic=(
                    f"expected compiler identity {contract.compiler.expected_identity!r}; "
                    f"received {actual_identity!r}"
                ),
                actual_identity=actual_identity,
            )

        try:
            with tempfile.TemporaryDirectory(
                prefix="w8-c2-eval-", dir=self.scratch_root
            ) as temporary:
                evaluation_root = Path(temporary)
                full = self._compile_implementations(
                    root=workspace,
                    output_root=evaluation_root / "full-objects",
                    contract=contract,
                    diagnostic_roots=(workspace, evaluation_root),
                )
                if full.status == "infrastructure_invalid":
                    return self._batch_infrastructure_receipt(
                        contract, full, actual_identity, phase="compile"
                    )
                compile_phase = {
                    "phase": "compile_to_object",
                    "status": full.status,
                    "translation_units": list(full.records),
                    "linked": False,
                    "executed": False,
                }
                if full.status == "passed":
                    return C2Receipt(
                        schema_version=C2_SCHEMA_VERSION,
                        category=C2_CATEGORY,
                        disposition="scored",
                        verifier=C2_VERIFIER_ID,
                        status="passed",
                        kernel=1,
                        category_score=1,
                        attribution={
                            "declaration_surface": {
                                "status": "not_required_for_compile_pass",
                                "reward_bearing": False,
                            },
                            "definition_binding": {
                                "status": "not_required_for_compile_pass",
                                "reward_bearing": False,
                            },
                        },
                        compiler_profile=contract.compiler.receipt(actual_identity),
                        compile_phase=compile_phase,
                        failure_code=None,
                        diagnostic=full.diagnostic,
                        contract_version=contract.contract_version,
                    )

                declaration_gate = self._run_declaration_gate(
                    workspace=workspace,
                    evaluation_root=evaluation_root,
                    contract=contract,
                )
                if declaration_gate["infrastructure"] is not None:
                    return self._gate_infrastructure_receipt(
                        contract,
                        declaration_gate,
                        actual_identity,
                        compile_phase,
                        full.diagnostic,
                        attribution={
                            "declaration_surface": declaration_gate["evidence"],
                            "definition_binding": {
                                "status": "not_run",
                                "reward_bearing": False,
                            },
                        },
                    )
                binding_gate = self._run_binding_gate(
                    workspace=workspace,
                    evaluation_root=evaluation_root,
                    contract=contract,
                )
                if binding_gate["infrastructure"] is not None:
                    return self._gate_infrastructure_receipt(
                        contract,
                        binding_gate,
                        actual_identity,
                        compile_phase,
                        full.diagnostic,
                        attribution={
                            "declaration_surface": declaration_gate["evidence"],
                            "definition_binding": binding_gate["evidence"],
                        },
                    )

                attribution = {
                    "declaration_surface": declaration_gate["evidence"],
                    "definition_binding": binding_gate["evidence"],
                }
                r1 = bool(declaration_gate["ruled_out"])
                r4 = bool(binding_gate["ruled_out"])
                combined_diagnostic = _join_diagnostics(
                    full.diagnostic,
                    str(declaration_gate["diagnostic"]),
                    str(binding_gate["diagnostic"]),
                )
                if r1 and r4:
                    return C2Receipt(
                        schema_version=C2_SCHEMA_VERSION,
                        category=C2_CATEGORY,
                        disposition="scored",
                        verifier=C2_VERIFIER_ID,
                        status="failed",
                        kernel=-1,
                        category_score=-1,
                        attribution=attribution,
                        compiler_profile=contract.compiler.receipt(actual_identity),
                        compile_phase=compile_phase,
                        failure_code="C2_TRANSLATION_FAILURE",
                        diagnostic=combined_diagnostic,
                        contract_version=contract.contract_version,
                    )

                if not r1 and not r4:
                    failure_code = "C1_C4_OWNERSHIP_NOT_RULED_OUT"
                elif not r1:
                    failure_code = "C1_OWNERSHIP_NOT_RULED_OUT"
                else:
                    failure_code = "C4_OWNERSHIP_NOT_RULED_OUT"
                return C2Receipt(
                    schema_version=C2_SCHEMA_VERSION,
                    category=C2_CATEGORY,
                    disposition="not_evaluated",
                    verifier=C2_VERIFIER_ID,
                    status="not_evaluated",
                    kernel=None,
                    category_score=None,
                    attribution=attribution,
                    compiler_profile=contract.compiler.receipt(actual_identity),
                    compile_phase=compile_phase,
                    failure_code=failure_code,
                    diagnostic=combined_diagnostic,
                    contract_version=contract.contract_version,
                )
        except (OSError, UnicodeError) as exc:
            return self._unscored(
                contract,
                disposition="workspace_invalid",
                failure_code="EVALUATION_WORKSPACE_FAILED",
                diagnostic=f"{type(exc).__name__}: {exc}",
                actual_identity=actual_identity,
            )

    def _compile_implementations(
        self,
        *,
        root: Path,
        output_root: Path,
        contract: C2Contract,
        diagnostic_roots: tuple[Path, ...],
        extra_arguments: tuple[str, ...] = (),
    ) -> _CompileBatch:
        output_root.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        diagnostics: list[str] = []
        failed = False
        for index, relative in enumerate(contract.implementation_files):
            source = root / relative
            output = output_root / f"unit-{index:03d}.o"
            command = _compile_command(
                contract.compiler,
                root,
                source,
                output,
                extra_arguments=extra_arguments,
            )
            outcome = self.runner.run(
                command,
                cwd=root,
                env=_compiler_environment(),
                timeout_seconds=contract.compiler.timeout_seconds,
            )
            infrastructure_error = _infrastructure_error(outcome)
            if infrastructure_error:
                code, detail = infrastructure_error
                return _CompileBatch(
                    status="infrastructure_invalid",
                    records=tuple(records),
                    diagnostic=detail,
                    infrastructure_failure=outcome.infrastructure_failure,
                    infrastructure_detail=code,
                )
            if outcome.returncode == 0:
                try:
                    object_created = output.is_file() and not output.is_symlink()
                except OSError as exc:
                    return _CompileBatch(
                        status="infrastructure_invalid",
                        records=tuple(records),
                        diagnostic=f"cannot inspect compiler output: {type(exc).__name__}: {exc}",
                        infrastructure_failure="runner",
                        infrastructure_detail="COMPILER_OUTPUT_INSPECTION_FAILED",
                    )
                if not object_created:
                    return _CompileBatch(
                        status="infrastructure_invalid",
                        records=tuple(records),
                        diagnostic=(
                            "compiler reported successful translation without creating "
                            f"an object file for {relative}"
                        ),
                        infrastructure_failure="runner",
                        infrastructure_detail="COMPILER_OUTPUT_MISSING",
                    )
            diagnostic = _normalize_diagnostic(_outcome_text(outcome), diagnostic_roots)
            status = "passed" if outcome.returncode == 0 else "failed"
            records.append(
                {
                    "source": relative,
                    "status": status,
                    "returncode": outcome.returncode,
                    "diagnostic_sha256": hashlib.sha256(diagnostic.encode("utf-8")).hexdigest(),
                }
            )
            if diagnostic:
                diagnostics.append(f"[{relative}]\n{diagnostic}")
            failed = failed or outcome.returncode != 0
        return _CompileBatch(
            status="failed" if failed else "passed",
            records=tuple(records),
            diagnostic=_join_diagnostics(*diagnostics),
        )

    def _run_declaration_gate(
        self,
        *,
        workspace: Path,
        evaluation_root: Path,
        contract: C2Contract,
    ) -> dict[str, Any]:
        probe = evaluation_root / "declaration-gate.cpp"
        output = evaluation_root / "declaration-gate.o"
        probe.write_text(contract.public_declaration_probe, encoding="utf-8")
        command = _compile_command(contract.compiler, workspace, probe, output)
        outcome = self.runner.run(
            command,
            cwd=workspace,
            env=_compiler_environment(),
            timeout_seconds=contract.compiler.timeout_seconds,
        )
        infrastructure_error = _infrastructure_error(outcome)
        if infrastructure_error:
            code, detail = infrastructure_error
            return {
                "ruled_out": False,
                "infrastructure": (code, detail),
                "evidence": {
                    "status": "infrastructure_invalid",
                    "reward_bearing": False,
                },
                "diagnostic": detail,
            }
        if outcome.returncode == 0 and (not output.is_file() or output.is_symlink()):
            detail = "declaration gate compiler reported success without an object artifact"
            return {
                "ruled_out": False,
                "infrastructure": ("COMPILER_OUTPUT_MISSING", detail),
                "evidence": {
                    "status": "infrastructure_invalid",
                    "reward_bearing": False,
                },
                "diagnostic": detail,
            }
        diagnostic = _normalize_diagnostic(_outcome_text(outcome), (workspace, evaluation_root))
        ruled_out = outcome.returncode == 0
        return {
            "ruled_out": ruled_out,
            "infrastructure": None,
            "evidence": {
                "status": "ruled_out" if ruled_out else "not_ruled_out",
                "reward_bearing": False,
                "mechanism": "trusted_public_declaration_probe_compile",
                "returncode": outcome.returncode,
                "diagnostic_sha256": hashlib.sha256(diagnostic.encode("utf-8")).hexdigest(),
            },
            "diagnostic": diagnostic,
        }

    def _run_binding_gate(
        self,
        *,
        workspace: Path,
        evaluation_root: Path,
        contract: C2Contract,
    ) -> dict[str, Any]:
        binding_root = evaluation_root / "binding-workspace"
        _copy_workspace(workspace, binding_root)
        files: list[dict[str, Any]] = []
        for relative in contract.implementation_files:
            source_path = binding_root / relative
            neutralization = _neutralize_cpp_source(
                source_path.read_bytes(),
                source_relative=relative,
                binding_root=binding_root,
                include_directories=contract.compiler.include_directories,
            )
            files.append(
                {
                    "source": relative,
                    "parser_status": neutralization.status,
                    "neutralized_bodies": neutralization.body_count,
                    "removed_missing_quoted_includes": list(
                        neutralization.removed_missing_includes
                    ),
                    "detail": neutralization.detail,
                }
            )
            if neutralization.status == "infrastructure_invalid":
                return {
                    "ruled_out": False,
                    "infrastructure": (
                        "ATTRIBUTION_PARSER_UNAVAILABLE",
                        neutralization.detail,
                    ),
                    "evidence": {
                        "status": "infrastructure_invalid",
                        "reward_bearing": False,
                        "files": files,
                    },
                    "diagnostic": neutralization.detail,
                }
            if neutralization.status == "ambiguous" or neutralization.source is None:
                return {
                    "ruled_out": False,
                    "infrastructure": None,
                    "evidence": {
                        "status": "ambiguous",
                        "reward_bearing": False,
                        "mechanism": "parser_body_neutralization_then_compile",
                        "files": files,
                    },
                    "diagnostic": neutralization.detail,
                }
            source_path.write_bytes(neutralization.source)

        batch = self._compile_implementations(
            root=binding_root,
            output_root=evaluation_root / "binding-objects",
            contract=contract,
            diagnostic_roots=(workspace, evaluation_root, binding_root),
            extra_arguments=("-Wno-unused-parameter",),
        )
        if batch.status == "infrastructure_invalid":
            return {
                "ruled_out": False,
                "infrastructure": (
                    batch.infrastructure_detail or "COMPILER_INFRASTRUCTURE_FAILURE",
                    batch.diagnostic,
                ),
                "evidence": {
                    "status": "infrastructure_invalid",
                    "reward_bearing": False,
                    "files": files,
                },
                "diagnostic": batch.diagnostic,
            }
        ruled_out = batch.status == "passed"
        return {
            "ruled_out": ruled_out,
            "infrastructure": None,
            "evidence": {
                "status": "ruled_out" if ruled_out else "not_ruled_out",
                "reward_bearing": False,
                "mechanism": "parser_body_neutralization_then_compile",
                "files": files,
                "translation_units": list(batch.records),
            },
            "diagnostic": batch.diagnostic,
        }

    def _batch_infrastructure_receipt(
        self,
        contract: C2Contract,
        batch: _CompileBatch,
        actual_identity: str,
        *,
        phase: str,
    ) -> C2Receipt:
        return self._unscored(
            contract,
            disposition="infrastructure_invalid",
            failure_code=batch.infrastructure_detail or "COMPILER_INFRASTRUCTURE_FAILURE",
            diagnostic=batch.diagnostic,
            actual_identity=actual_identity,
            compile_phase={
                "phase": phase,
                "status": "infrastructure_invalid",
                "translation_units": list(batch.records),
                "linked": False,
                "executed": False,
            },
        )

    def _gate_infrastructure_receipt(
        self,
        contract: C2Contract,
        gate: dict[str, Any],
        actual_identity: str,
        compile_phase: dict[str, Any],
        full_diagnostic: str,
        attribution: dict[str, Any],
    ) -> C2Receipt:
        code, detail = gate["infrastructure"]
        return self._unscored(
            contract,
            disposition="infrastructure_invalid",
            failure_code=str(code),
            diagnostic=_join_diagnostics(full_diagnostic, str(detail)),
            actual_identity=actual_identity,
            compile_phase=compile_phase,
            attribution=attribution,
        )

    def _unscored(
        self,
        contract: C2Contract,
        *,
        disposition: Disposition,
        failure_code: str,
        diagnostic: str,
        actual_identity: str | None = None,
        compile_phase: dict[str, Any] | None = None,
        attribution: dict[str, Any] | None = None,
    ) -> C2Receipt:
        status: Status = "not_evaluated" if disposition == "not_evaluated" else "invalid"
        return C2Receipt(
            schema_version=C2_SCHEMA_VERSION,
            category=C2_CATEGORY,
            disposition=disposition,
            verifier=C2_VERIFIER_ID,
            status=status,
            kernel=None,
            category_score=None,
            attribution=attribution
            or {
                "declaration_surface": {
                    "status": "not_run",
                    "reward_bearing": False,
                },
                "definition_binding": {
                    "status": "not_run",
                    "reward_bearing": False,
                },
            },
            compiler_profile=contract.compiler.receipt(actual_identity),
            compile_phase=compile_phase
            or {
                "phase": "compile_to_object",
                "status": "not_run",
                "translation_units": [],
                "linked": False,
                "executed": False,
            },
            failure_code=failure_code,
            diagnostic=_normalize_diagnostic(diagnostic, ()),
            contract_version=contract.contract_version,
        )


def _validate_contract(contract: C2Contract, expected_version: str) -> str | None:
    if not contract.contract_version or contract.contract_version != expected_version:
        return "supplied task contract version is unsupported"
    profile = contract.compiler
    if not profile.profile_id or not profile.executable or not profile.expected_identity:
        return "compiler profile id, executable, and exact identity are required"
    if not Path(profile.executable).is_absolute():
        return "compiler executable must be an absolute path supplied by the task environment"
    if profile.timeout_seconds <= 0:
        return "compiler timeout must be positive"
    if "-std=c++17" not in profile.arguments or "-Werror" not in profile.arguments:
        return "C2 compiler profile must pin C++17 and warning-as-error semantics"
    forbidden = {"-c", "-E", "-S"}
    if forbidden.intersection(profile.arguments) or "-o" in profile.arguments:
        return "compile-stage control flags are owned by the C2 verifier"
    if not contract.required_files or not contract.implementation_files:
        return "required and implementation file lists must be non-empty"
    if not contract.public_declaration_probe.strip():
        return "a trusted public declaration probe is required for failure attribution"
    file_paths = (*contract.required_files, *contract.implementation_files)
    invalid_files = [path for path in file_paths if not _is_safe_file_path(path)]
    if invalid_files:
        return f"contract contains unsafe file paths: {', '.join(sorted(invalid_files))}"
    invalid_includes = [
        path for path in profile.include_directories if not _is_safe_directory_path(path)
    ]
    if invalid_includes:
        return (
            f"contract contains unsafe include directories: {', '.join(sorted(invalid_includes))}"
        )
    if not set(contract.implementation_files).issubset(contract.required_files):
        return "every implementation translation unit must be a required candidate file"
    if len(set(contract.required_files)) != len(contract.required_files):
        return "required file paths must be unique"
    if len(set(contract.implementation_files)) != len(contract.implementation_files):
        return "implementation file paths must be unique"
    return None


def _parse_candidate(
    value: C2Candidate | Mapping[str, Any] | object,
) -> tuple[C2Candidate | None, str | None, str | None]:
    if isinstance(value, C2Candidate):
        raw_version: object = value.contract_version
        raw_files: object = value.files
    elif isinstance(value, Mapping):
        raw_version = value.get("contract_version")
        raw_files = value.get("files")
    else:
        return None, "candidate response must be an object", None
    if not isinstance(raw_version, str) or not raw_version.strip():
        return None, "candidate response requires a non-empty contract_version", None
    if not isinstance(raw_files, Mapping):
        return None, "candidate response requires a files object", None
    if len(raw_files) > _MAX_CANDIDATE_FILES:
        return None, f"candidate exceeds {_MAX_CANDIDATE_FILES} files", None
    files: dict[str, str] = {}
    total_bytes = 0
    for raw_path, raw_source in raw_files.items():
        if not isinstance(raw_path, str) or not _is_safe_file_path(raw_path):
            return None, f"candidate contains an unsafe file path: {raw_path!r}", None
        if not isinstance(raw_source, str):
            return None, f"candidate file {raw_path!r} must contain UTF-8 text", None
        encoded = raw_source.encode("utf-8")
        total_bytes += len(encoded)
        if total_bytes > _MAX_CANDIDATE_BYTES:
            return None, f"candidate exceeds {_MAX_CANDIDATE_BYTES} encoded bytes", None
        files[raw_path] = raw_source
    return C2Candidate(contract_version=raw_version, files=files), None, None


def _materialize_candidate(files: Mapping[str, str], workspace: Path) -> None:
    for relative, source in sorted(files.items()):
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source, encoding="utf-8", newline="")


def _validate_workspace(workspace: Path, required_files: tuple[str, ...]) -> str | None:
    if not workspace.exists() or not workspace.is_dir() or workspace.is_symlink():
        return "candidate workspace is missing, not a directory, or is a symlink"
    file_count = 0
    total_bytes = 0
    try:
        for path in sorted(workspace.rglob("*")):
            if path.is_symlink():
                return f"candidate workspace contains a symlink: {path.relative_to(workspace)}"
            if path.is_dir():
                continue
            if not path.is_file():
                return f"candidate workspace contains a non-regular file: {path.relative_to(workspace)}"
            file_count += 1
            total_bytes += path.stat().st_size
            if file_count > _MAX_CANDIDATE_FILES or total_bytes > _MAX_CANDIDATE_BYTES:
                return "candidate workspace exceeds deterministic size limits"
        missing = [relative for relative in required_files if not (workspace / relative).is_file()]
    except OSError as exc:
        return f"workspace inspection failed: {type(exc).__name__}: {exc}"
    if missing:
        return f"materialized workspace is missing required files: {', '.join(missing)}"
    return None


def _validate_local_include_paths(
    workspace: Path, implementation_files: tuple[str, ...]
) -> str | None:
    for relative in implementation_files:
        try:
            source = (workspace / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return f"cannot read implementation {relative}: {type(exc).__name__}: {exc}"
        for match in _QUOTED_INCLUDE_RE.finditer(source):
            include = PurePosixPath(match.group("path"))
            if include.is_absolute() or ".." in include.parts:
                return f"implementation {relative} uses an unsafe quoted include path"
    return None


def _copy_workspace(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for candidate in sorted(source.rglob("*")):
        relative = candidate.relative_to(source)
        target = destination / relative
        if candidate.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif candidate.is_file() and not candidate.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate, target)
        else:
            raise OSError(f"unsupported workspace entry: {relative}")


def _neutralize_cpp_source(
    source: bytes,
    *,
    source_relative: str,
    binding_root: Path,
    include_directories: tuple[str, ...],
) -> _Neutralization:
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_cpp

        parser = Parser(Language(tree_sitter_cpp.language()))
        tree = parser.parse(source)
    except Exception as exc:  # pragma: no cover - dependency failures are injected in tests.
        return _Neutralization(
            status="infrastructure_invalid",
            source=None,
            body_count=0,
            removed_missing_includes=(),
            detail=f"C++ attribution parser unavailable: {type(exc).__name__}: {exc}",
        )

    function_bodies: list[tuple[int, int]] = []
    constructor_initializers: list[tuple[int, int]] = []
    unsupported: list[str] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            body = node.child_by_field_name("body")
            if body is None or body.type != "compound_statement":
                unsupported.append(f"unsupported function definition at byte {node.start_byte}")
            else:
                type_node = node.child_by_field_name("type")
                declarator = node.child_by_field_name("declarator")
                declarator_text = (
                    source[declarator.start_byte : declarator.end_byte]
                    if declarator is not None
                    else b""
                )
                type_text = (
                    source[type_node.start_byte : type_node.end_byte]
                    if type_node is not None
                    else b""
                )
                if b"auto" in type_text and b"->" not in declarator_text:
                    unsupported.append(
                        f"deduced return type cannot be neutralized at byte {node.start_byte}"
                    )
                function_bodies.append((body.start_byte, body.end_byte))
                initializers = [
                    child for child in node.children if child.type == "field_initializer_list"
                ]
                if len(initializers) > 1:
                    unsupported.append(
                        f"multiple constructor initializer lists at byte {node.start_byte}"
                    )
                elif initializers:
                    initializer = initializers[0]
                    constructor_initializers.append((initializer.start_byte, initializer.end_byte))
                for child in node.children:
                    if child.id != body.id and child not in initializers:
                        stack.append(child)
                continue
        stack.extend(reversed(node.children))

    if unsupported:
        return _Neutralization(
            status="ambiguous",
            source=None,
            body_count=len(function_bodies),
            removed_missing_includes=(),
            detail="; ".join(unsupported),
        )
    function_bodies.sort()
    constructor_initializers.sort()
    neutralized_regions = sorted((*function_bodies, *constructor_initializers))
    if any(
        previous[1] > current[0]
        for previous, current in zip(neutralized_regions, neutralized_regions[1:])
    ):
        return _Neutralization(
            status="ambiguous",
            source=None,
            body_count=len(function_bodies),
            removed_missing_includes=(),
            detail="overlapping parser body ranges",
        )

    parse_errors: list[tuple[int, int]] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.is_error or node.is_missing:
            parse_errors.append((node.start_byte, node.end_byte))
        stack.extend(reversed(node.children))
    for start, end in parse_errors:
        if not any(
            region_start <= start and end <= region_end
            for region_start, region_end in neutralized_regions
        ):
            return _Neutralization(
                status="ambiguous",
                source=None,
                body_count=len(function_bodies),
                removed_missing_includes=(),
                detail=(
                    "parser error crosses or lies outside an implementation body "
                    f"at bytes {start}:{end}"
                ),
            )

    replacements: list[tuple[int, int, bytes]] = []
    for start, end in function_bodies:
        original = source[start:end]
        replacement = b"{ __builtin_unreachable(); }" + b"\n" * original.count(b"\n")
        replacements.append((start, end, replacement))
    for start, end in constructor_initializers:
        original = source[start:end]
        replacement = bytes(byte if byte in (10, 13) else 32 for byte in original)
        replacements.append((start, end, replacement))

    removed: list[str] = []
    source_path = binding_root / source_relative
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "preproc_include":
            path_node = node.child_by_field_name("path")
            if path_node is not None:
                raw = source[path_node.start_byte : path_node.end_byte]
                if raw.startswith(b'"') and raw.endswith(b'"'):
                    include = raw[1:-1].decode("utf-8", errors="strict")
                    if not _quoted_include_exists(
                        include,
                        source_path=source_path,
                        binding_root=binding_root,
                        include_directories=include_directories,
                    ):
                        segment = source[node.start_byte : node.end_byte]
                        blank = bytes(byte if byte in (10, 13) else 32 for byte in segment)
                        replacements.append((node.start_byte, node.end_byte, blank))
                        removed.append(include)
        stack.extend(reversed(node.children))

    replacements.sort(key=lambda item: item[0])
    if any(previous[1] > current[0] for previous, current in zip(replacements, replacements[1:])):
        return _Neutralization(
            status="ambiguous",
            source=None,
            body_count=len(function_bodies),
            removed_missing_includes=tuple(sorted(set(removed))),
            detail="overlapping body/include transformation ranges",
        )
    result = source
    for start, end, replacement in reversed(replacements):
        result = result[:start] + replacement + result[end:]
    return _Neutralization(
        status="confident",
        source=result,
        body_count=len(function_bodies),
        removed_missing_includes=tuple(sorted(set(removed))),
    )


def _quoted_include_exists(
    include: str,
    *,
    source_path: Path,
    binding_root: Path,
    include_directories: tuple[str, ...],
) -> bool:
    candidates = [source_path.parent / include]
    candidates.extend(binding_root / directory / include for directory in include_directories)
    return any(candidate.is_file() for candidate in candidates)


def _compile_command(
    profile: CompilerProfile,
    root: Path,
    source: Path,
    output: Path,
    *,
    extra_arguments: tuple[str, ...] = (),
) -> tuple[str, ...]:
    include_args: list[str] = []
    for relative in profile.include_directories:
        include_args.extend(("-I", str(root / relative)))
    return (
        profile.executable,
        *profile.arguments,
        *extra_arguments,
        *include_args,
        "-x",
        "c++",
        "-c",
        str(source),
        "-o",
        str(output),
    )


def _compiler_environment() -> dict[str, str]:
    return {
        "LC_ALL": "C",
        "LANG": "C",
        "LANGUAGE": "C",
        "PATH": os.defpath,
        "TZ": "UTC",
    }


def _infrastructure_error(outcome: CommandOutcome) -> tuple[str, str] | None:
    codes = {
        "unavailable": "COMPILER_UNAVAILABLE",
        "timeout": "COMPILER_TIMEOUT",
        "sandbox": "SANDBOX_FAILURE",
        "runner": "COMMAND_RUNNER_FAILURE",
    }
    failure = outcome.infrastructure_failure
    if failure is not None:
        code = codes.get(failure)
        if code is None or outcome.returncode is not None:
            return "COMMAND_OUTCOME_INVALID", "runner returned contradictory failure evidence"
        return code, outcome.infrastructure_detail
    if type(outcome.returncode) is not int or outcome.returncode < 0:
        return "COMMAND_OUTCOME_INVALID", "runner returned no valid process return code"
    return None


def _outcome_text(outcome: CommandOutcome) -> str:
    return _join_diagnostics(outcome.stdout, outcome.stderr)


def _normalize_diagnostic(text: str, roots: tuple[Path, ...]) -> str:
    normalized = _ANSI_ESCAPE_RE.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    for root in sorted((str(path.resolve()) for path in roots), key=len, reverse=True):
        normalized = normalized.replace(root, "<workspace>")
    lines = [line.rstrip() for line in normalized.splitlines()]
    normalized = "\n".join(lines).strip()
    if len(normalized) > _MAX_DIAGNOSTIC_CHARS:
        normalized = normalized[-_MAX_DIAGNOSTIC_CHARS:]
    return normalized


def _join_diagnostics(*parts: str) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def _first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _is_safe_file_path(raw: str) -> bool:
    if not raw or "\x00" in raw or "\\" in raw:
        return False
    path = PurePosixPath(raw)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and "." not in path.parts
        and path.as_posix() == raw
    )


def _is_safe_directory_path(raw: str) -> bool:
    return raw == "." or _is_safe_file_path(raw)


def _coerce_process_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
