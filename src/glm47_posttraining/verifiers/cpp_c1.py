"""C1 public-API contract verification for C++ candidate workspaces.

A trusted task contract supplies isolated source probes for each required API
atom. Probes compile against the submitted header without candidate
implementation code, keeping C2 translation, C4 definitions/linkage, and C3
behaviour outside C1. All checks belong to one reward-bearing verifier.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Protocol

SCHEMA_VERSION = "w8-c1-receipt-v1"
CATEGORY = "C1"
VERIFIER_ID = "public-api-contract"
_IDENTIFIER = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*$")
_FAILURE_CODE = re.compile(r"^C1_[A-Z0-9_]+$")
_HEADER_PATH = re.compile(r"^[a-zA-Z0-9_./+-]+$")
_MAX_DIAGNOSTIC_CHARS = 4000


class InputDisposition(str, Enum):
    """Cause established by candidate parsing/materialization before C1."""

    READY = "ready"
    CANDIDATE_FORMAT_INVALID = "candidate_format_invalid"
    WORKSPACE_INVALID = "workspace_invalid"
    INFRASTRUCTURE_INVALID = "infrastructure_invalid"
    CONTRACT_INVALID = "contract_invalid"
    NOT_EVALUATED = "not_evaluated"


class ReceiptDisposition(str, Enum):
    SCORED = "scored"
    CANDIDATE_FORMAT_INVALID = "candidate_format_invalid"
    WORKSPACE_INVALID = "workspace_invalid"
    INFRASTRUCTURE_INVALID = "infrastructure_invalid"
    CONTRACT_INVALID = "contract_invalid"
    NOT_EVALUATED = "not_evaluated"


class RunState(str, Enum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    LAUNCH_FAILED = "launch_failed"


@dataclass(frozen=True)
class CompilerProfile:
    """Pinned task compiler and symbol-inspector command profile."""

    profile_id: str
    compiler: str
    identity_sha256: str
    flags: tuple[str, ...] = (
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-pthread",
    )
    symbol_inspector: str | None = None
    symbol_identity_sha256: str | None = None
    timeout_seconds: float = 20.0


@dataclass(frozen=True)
class CompileContractProbe:
    """One compiler observation inside the single C1 verifier.

    ``source`` is appended after the submitted header include. Positive probes
    typically use exact pointer-to-member casts and construction expressions.
    Negative probes can prove properties such as an explicit constructor.
    """

    probe_id: str
    source: str
    failure_code: str
    expect_success: bool = True


@dataclass(frozen=True)
class SymbolContractProbe:
    """Exact binding probe for declarations C++17 cannot address.

    A consumer is compiled against the submitted header. A trusted provider
    independently defines the canonical symbol; its baseline contains identical
    support declarations without that definition. Raw external-symbol overlap
    proves that overload resolution selected the exact declaration. Candidate
    implementation objects are never compiled or linked.
    """

    probe_id: str
    consumer_source: str
    provider_source: str
    baseline_source: str
    failure_code: str
    minimum_symbol_matches: int = 1
    expected_symbol_count: int | None = None


@dataclass(frozen=True)
class PublicApiContract:
    contract_version: str
    public_header: str
    compiler: CompilerProfile
    compile_probes: tuple[CompileContractProbe, ...]
    symbol_probes: tuple[SymbolContractProbe, ...] = ()


@dataclass(frozen=True)
class CommandOutcome:
    state: RunState
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    error_type: str = ""


class CommandRunner(Protocol):
    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str],
    ) -> CommandOutcome: ...


class SubprocessCommandRunner:
    """Shell-free runner intended to execute inside the task's outer sandbox."""

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str],
    ) -> CommandOutcome:
        try:
            result = subprocess.run(
                [str(arg) for arg in args],
                cwd=cwd,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandOutcome(
                state=RunState.TIMED_OUT,
                stdout=_coerce_output(exc.stdout),
                stderr=_coerce_output(exc.stderr),
                error_type="TimeoutExpired",
            )
        except OSError as exc:
            return CommandOutcome(
                state=RunState.LAUNCH_FAILED,
                stderr=str(exc),
                error_type=type(exc).__name__,
            )
        return CommandOutcome(
            state=RunState.COMPLETED,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )


def fingerprint_tool(
    executable: str,
    *,
    runner: CommandRunner | None = None,
    cwd: Path | None = None,
    timeout_seconds: float = 10.0,
) -> str:
    """Fingerprint an absolute tool path using its normalized version output."""

    if not Path(executable).is_absolute():
        raise ValueError("tool executable must be an absolute path")
    outcome = (runner or SubprocessCommandRunner()).run(
        [executable, "--version"],
        cwd=cwd or Path.cwd(),
        timeout_seconds=timeout_seconds,
        env=_compiler_env(),
    )
    if outcome.state is not RunState.COMPLETED or outcome.returncode != 0:
        raise RuntimeError("tool identity command failed")
    normalized = _normalize_diagnostic(outcome.stdout + outcome.stderr)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DiagnosticEvidence:
    digest_sha256: str
    excerpt: str
    returncode: int | None
    run_state: str


@dataclass(frozen=True)
class VerifierResult:
    verifier: str
    status: str
    kernel: int | None
    phase: str
    failure_code: str | None
    probe_id: str | None
    evidence: DiagnosticEvidence


@dataclass(frozen=True)
class C1Receipt:
    schema_version: str
    category: str
    disposition: str
    verifier_results: tuple[VerifierResult, ...]
    category_score: int | None
    contract_version: str
    compiler_profile: str

    def __post_init__(self) -> None:
        valid_dispositions = {item.value for item in ReceiptDisposition}
        if self.schema_version != SCHEMA_VERSION or self.category != CATEGORY:
            raise ValueError("invalid C1 receipt identity")
        if self.disposition not in valid_dispositions:
            raise ValueError("invalid C1 receipt disposition")
        if len(self.verifier_results) != 1:
            raise ValueError("C1 has exactly one reward-bearing verifier")
        result = self.verifier_results[0]
        if result.verifier != VERIFIER_ID:
            raise ValueError("unexpected C1 verifier id")
        if self.disposition == ReceiptDisposition.SCORED.value:
            if result.kernel not in (-1, 1) or self.category_score != result.kernel:
                raise ValueError("scored C1 receipt must have category_score == kernel")
            expected_status = "passed" if result.kernel == 1 else "failed"
            if result.status != expected_status:
                raise ValueError("C1 status and kernel disagree")
            if result.kernel == 1 and result.failure_code is not None:
                raise ValueError("passing C1 result cannot contain a failure code")
            if result.kernel == -1 and not result.failure_code:
                raise ValueError("failing C1 result requires a failure code")
        else:
            if result.kernel is not None or self.category_score is not None:
                raise ValueError("non-scored C1 receipt cannot contain reward")
            expected_status = (
                "not_evaluated"
                if self.disposition == ReceiptDisposition.NOT_EVALUATED.value
                else "invalid"
            )
            if result.status != expected_status or not result.failure_code:
                raise ValueError("non-scored C1 result is inconsistent")

    @property
    def kernel(self) -> int | None:
        return self.verifier_results[0].kernel

    @property
    def kernels(self) -> tuple[int, ...] | None:
        return (self.kernel,) if self.kernel is not None else None

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["kernels"] = list(self.kernels) if self.kernels is not None else None
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class C1Verifier:
    """Evaluate one independently materialized candidate workspace for C1."""

    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner or SubprocessCommandRunner()

    def evaluate(
        self,
        workspace: str | Path,
        contract: PublicApiContract,
        *,
        input_disposition: InputDisposition = InputDisposition.READY,
        input_failure_code: str | None = None,
        expected_contract_version: str | None = None,
    ) -> C1Receipt:
        contract_error = _validate_contract(contract)
        if contract_error:
            return _unscored(
                contract,
                ReceiptDisposition.CONTRACT_INVALID,
                "contract_validation",
                contract_error,
            )
        if (
            expected_contract_version is not None
            and expected_contract_version != contract.contract_version
        ):
            return _unscored(
                contract,
                ReceiptDisposition.CONTRACT_INVALID,
                "contract_validation",
                "C1_CONTRACT_VERSION_MISMATCH",
            )
        if input_disposition is not InputDisposition.READY:
            return _unscored(
                contract,
                ReceiptDisposition(input_disposition.value),
                "input_validation",
                input_failure_code or f"C1_{input_disposition.value.upper()}",
            )

        root = Path(workspace)
        if not root.exists() or not root.is_dir():
            return _unscored(
                contract,
                ReceiptDisposition.WORKSPACE_INVALID,
                "workspace_validation",
                "C1_WORKSPACE_ROOT_INVALID",
            )
        root = root.resolve()
        header = root / PurePosixPath(contract.public_header)
        try:
            header.resolve(strict=False).relative_to(root)
        except ValueError:
            return _unscored(
                contract,
                ReceiptDisposition.WORKSPACE_INVALID,
                "workspace_validation",
                "C1_PUBLIC_HEADER_ESCAPES_WORKSPACE",
            )
        if header.is_symlink():
            return _unscored(
                contract,
                ReceiptDisposition.WORKSPACE_INVALID,
                "workspace_validation",
                "C1_PUBLIC_HEADER_SYMLINK_UNTRUSTED",
            )
        if not header.exists():
            return _scored_failure(
                contract, "header_presence", "C1_REQUIRED_HEADER_MISSING", "header-presence"
            )
        if not header.is_file():
            return _unscored(
                contract,
                ReceiptDisposition.WORKSPACE_INVALID,
                "workspace_validation",
                "C1_PUBLIC_HEADER_NOT_REGULAR_FILE",
            )

        env = _compiler_env()
        with tempfile.TemporaryDirectory(prefix="w8-c1-") as temp_name:
            temp = Path(temp_name)
            identity = self._run([contract.compiler.compiler, "--version"], temp, contract, env)
            invalid = _identity_error(identity, contract.compiler.identity_sha256)
            if invalid:
                return _unscored_outcome(
                    contract,
                    ReceiptDisposition.INFRASTRUCTURE_INVALID,
                    "toolchain_validation",
                    invalid,
                    identity,
                    temp,
                    root,
                )

            calibration = self._compile_source(
                "int c1_toolchain_calibration = 0;\n",
                temp / "calibration.cpp",
                temp / "calibration.o",
                root,
                contract,
                env,
            )
            if not _compile_succeeded(calibration):
                disposition = (
                    ReceiptDisposition.CONTRACT_INVALID
                    if _semantic_return(calibration)
                    else ReceiptDisposition.INFRASTRUCTURE_INVALID
                )
                return _unscored_outcome(
                    contract,
                    disposition,
                    "toolchain_validation",
                    "C1_COMPILER_PROFILE_INVALID",
                    calibration,
                    temp,
                    root,
                )

            include = f'#include "{contract.public_header}"\n'
            header_result = self._compile_source(
                include,
                temp / "header_self_contained.cpp",
                temp / "header_self_contained.o",
                root,
                contract,
                env,
            )
            classified = self._classify_compile_observation(
                contract,
                header_result,
                expect_success=True,
                phase="header_self_containment",
                failure_code="C1_HEADER_NOT_SELF_CONTAINED",
                probe_id="header-self-containment",
                temp=temp,
                root=root,
                env=env,
            )
            if classified is not None:
                return classified

            for index, probe in enumerate(contract.compile_probes):
                outcome = self._compile_source(
                    include + probe.source,
                    temp / f"compile_probe_{index}.cpp",
                    temp / f"compile_probe_{index}.o",
                    root,
                    contract,
                    env,
                )
                classified = self._classify_compile_observation(
                    contract,
                    outcome,
                    expect_success=probe.expect_success,
                    phase="public_api_probe",
                    failure_code=probe.failure_code,
                    probe_id=probe.probe_id,
                    temp=temp,
                    root=root,
                    env=env,
                )
                if classified is not None:
                    return classified

            if contract.symbol_probes:
                assert contract.compiler.symbol_inspector is not None
                assert contract.compiler.symbol_identity_sha256 is not None
                symbol_identity = self._run(
                    [contract.compiler.symbol_inspector, "--version"], temp, contract, env
                )
                invalid = _identity_error(symbol_identity, contract.compiler.symbol_identity_sha256)
                if invalid:
                    return _unscored_outcome(
                        contract,
                        ReceiptDisposition.INFRASTRUCTURE_INVALID,
                        "symbol_tool_validation",
                        invalid,
                        symbol_identity,
                        temp,
                        root,
                    )
                for index, probe in enumerate(contract.symbol_probes):
                    result = self._evaluate_symbol_probe(
                        probe, index, include, root, temp, contract, env
                    )
                    if result is not None:
                        return result

        return _scored_pass(contract)

    def _evaluate_symbol_probe(
        self,
        probe: SymbolContractProbe,
        index: int,
        include: str,
        root: Path,
        temp: Path,
        contract: PublicApiContract,
        env: dict[str, str],
    ) -> C1Receipt | None:
        paths = {
            role: (temp / f"symbol_{role}_{index}.cpp", temp / f"symbol_{role}_{index}.o")
            for role in ("consumer", "provider", "baseline")
        }
        sources = {
            "consumer": include + probe.consumer_source,
            "provider": probe.provider_source,
            "baseline": probe.baseline_source,
        }
        for role in ("provider", "baseline", "consumer"):
            source_path, object_path = paths[role]
            outcome = self._compile_source(
                sources[role], source_path, object_path, root, contract, env
            )
            if _compile_succeeded(outcome):
                continue
            if role == "consumer":
                return self._classify_compile_observation(
                    contract,
                    outcome,
                    expect_success=True,
                    phase="public_symbol_consumer",
                    failure_code=probe.failure_code,
                    probe_id=probe.probe_id,
                    temp=temp,
                    root=root,
                    env=env,
                )
            disposition = (
                ReceiptDisposition.CONTRACT_INVALID
                if _semantic_return(outcome)
                else ReceiptDisposition.INFRASTRUCTURE_INVALID
            )
            return _unscored_outcome(
                contract,
                disposition,
                "symbol_contract_validation",
                "C1_SYMBOL_PROBE_CONTRACT_INVALID",
                outcome,
                temp,
                root,
                probe.probe_id,
            )

        provider = self._read_symbols(
            paths["provider"][1],
            defined_only=True,
            temp=temp,
            contract=contract,
            env=env,
        )
        baseline = self._read_symbols(
            paths["baseline"][1],
            defined_only=True,
            temp=temp,
            contract=contract,
            env=env,
        )
        consumer = self._read_symbols(
            paths["consumer"][1],
            defined_only=False,
            temp=temp,
            contract=contract,
            env=env,
        )
        for outcome, _symbols in (provider, baseline, consumer):
            if outcome.state is not RunState.COMPLETED or outcome.returncode != 0:
                return _unscored_outcome(
                    contract,
                    ReceiptDisposition.INFRASTRUCTURE_INVALID,
                    "symbol_inspection",
                    "C1_SYMBOL_INSPECTION_INVALID",
                    outcome,
                    temp,
                    root,
                    probe.probe_id,
                )

        expected = provider[1] - baseline[1]
        if not expected or (
            probe.expected_symbol_count is not None and len(expected) != probe.expected_symbol_count
        ):
            return _unscored(
                contract,
                ReceiptDisposition.CONTRACT_INVALID,
                "symbol_contract_validation",
                "C1_SYMBOL_PROBE_EXPECTATION_INVALID",
                probe.probe_id,
            )
        matches = expected & consumer[1]
        if len(matches) < probe.minimum_symbol_matches:
            evidence = _evidence_from_text(
                "expected=" + ",".join(sorted(expected)) + "\nmatched=" + ",".join(sorted(matches)),
                returncode=0,
                run_state=RunState.COMPLETED,
                temp=temp,
                root=root,
            )
            return _scored_failure(
                contract,
                "public_symbol_contract",
                probe.failure_code,
                probe.probe_id,
                evidence,
            )
        return None

    def _read_symbols(
        self,
        object_path: Path,
        *,
        defined_only: bool,
        temp: Path,
        contract: PublicApiContract,
        env: dict[str, str],
    ) -> tuple[CommandOutcome, set[str]]:
        assert contract.compiler.symbol_inspector is not None
        command = [contract.compiler.symbol_inspector, "-P", "--extern-only"]
        if defined_only:
            command.append("--defined-only")
        command.append(str(object_path))
        outcome = self._run(command, temp, contract, env)
        if outcome.state is not RunState.COMPLETED or outcome.returncode != 0:
            return outcome, set()
        symbols: set[str] = set()
        for line in outcome.stdout.splitlines():
            fields = line.split()
            if len(fields) < 2 or len(fields[1]) != 1:
                return CommandOutcome(
                    RunState.LAUNCH_FAILED,
                    stderr="symbol inspector returned an unparseable POSIX record",
                    error_type="SymbolRecordError",
                ), set()
            symbols.add(fields[0])
        return outcome, symbols

    def _classify_compile_observation(
        self,
        contract: PublicApiContract,
        outcome: CommandOutcome,
        *,
        expect_success: bool,
        phase: str,
        failure_code: str,
        probe_id: str,
        temp: Path,
        root: Path,
        env: dict[str, str],
    ) -> C1Receipt | None:
        actual_success = _compile_succeeded(outcome)
        if outcome.state is not RunState.COMPLETED or (outcome.returncode or 0) < 0:
            return _unscored_outcome(
                contract,
                ReceiptDisposition.INFRASTRUCTURE_INVALID,
                phase,
                "C1_COMPILER_EXECUTION_INVALID",
                outcome,
                temp,
                root,
                probe_id,
            )
        if actual_success == expect_success:
            return None

        # A second known-good translation distinguishes a semantic probe result
        # from a toolchain/resource failure without reading diagnostic text.
        post = self._compile_source(
            "int c1_post_failure_calibration = 0;\n",
            temp / "post_failure_calibration.cpp",
            temp / "post_failure_calibration.o",
            root,
            contract,
            env,
        )
        if not _compile_succeeded(post):
            return _unscored_outcome(
                contract,
                ReceiptDisposition.INFRASTRUCTURE_INVALID,
                phase,
                "C1_COMPILER_BECAME_UNHEALTHY",
                post,
                temp,
                root,
                probe_id,
            )
        return _scored_failure(
            contract,
            phase,
            failure_code,
            probe_id,
            _evidence(outcome, temp, root),
        )

    def _compile_source(
        self,
        source: str,
        source_path: Path,
        object_path: Path,
        root: Path,
        contract: PublicApiContract,
        env: dict[str, str],
    ) -> CommandOutcome:
        source_path.write_text(source, encoding="utf-8")
        command = [
            contract.compiler.compiler,
            *contract.compiler.flags,
            "-I",
            str(root),
            "-x",
            "c++",
            "-c",
            str(source_path),
            "-o",
            str(object_path),
        ]
        outcome = self._run(command, source_path.parent, contract, env)
        if _compile_succeeded(outcome) and (not object_path.is_file() or object_path.is_symlink()):
            return CommandOutcome(
                state=RunState.LAUNCH_FAILED,
                returncode=outcome.returncode,
                stdout=outcome.stdout,
                stderr="compiler reported success without producing the required object artifact",
                error_type="ArtifactMissing",
            )
        return outcome

    def _run(
        self,
        command: Sequence[str],
        cwd: Path,
        contract: PublicApiContract,
        env: dict[str, str],
    ) -> CommandOutcome:
        return self._runner.run(
            command,
            cwd=cwd,
            timeout_seconds=contract.compiler.timeout_seconds,
            env=env,
        )


def _validate_contract(contract: PublicApiContract) -> str | None:
    header = PurePosixPath(contract.public_header)
    if (
        not contract.contract_version
        or not _IDENTIFIER.fullmatch(contract.contract_version)
        or not contract.compiler.profile_id
        or not _IDENTIFIER.fullmatch(contract.compiler.profile_id)
    ):
        return "C1_CONTRACT_IDENTITY_INVALID"
    if (
        not contract.public_header
        or header.is_absolute()
        or ".." in header.parts
        or "\\" in contract.public_header
        or not _HEADER_PATH.fullmatch(contract.public_header)
    ):
        return "C1_PUBLIC_HEADER_PATH_INVALID"
    compiler = contract.compiler
    if (
        not compiler.compiler
        or not Path(compiler.compiler).is_absolute()
        or not re.fullmatch(r"[0-9a-f]{64}", compiler.identity_sha256)
        or compiler.timeout_seconds <= 0
        or any("\x00" in flag for flag in compiler.flags)
        or any(flag in {"-c", "-o", "-fsyntax-only"} for flag in compiler.flags)
    ):
        return "C1_COMPILER_PROFILE_INVALID"
    if contract.symbol_probes and (
        not compiler.symbol_inspector
        or not Path(compiler.symbol_inspector).is_absolute()
        or compiler.symbol_identity_sha256 is None
        or not re.fullmatch(r"[0-9a-f]{64}", compiler.symbol_identity_sha256)
    ):
        return "C1_SYMBOL_PROFILE_INVALID"
    probe_ids: set[str] = set()
    if not contract.compile_probes and not contract.symbol_probes:
        return "C1_API_PROBES_EMPTY"
    for probe in (*contract.compile_probes, *contract.symbol_probes):
        if not _IDENTIFIER.fullmatch(probe.probe_id) or probe.probe_id in probe_ids:
            return "C1_PROBE_ID_INVALID"
        probe_ids.add(probe.probe_id)
        if not _FAILURE_CODE.fullmatch(probe.failure_code):
            return "C1_PROBE_FAILURE_CODE_INVALID"
    for probe in contract.compile_probes:
        if not probe.source.strip():
            return "C1_COMPILE_PROBE_EMPTY"
    for probe in contract.symbol_probes:
        if (
            not probe.consumer_source.strip()
            or not probe.provider_source.strip()
            or not probe.baseline_source.strip()
            or probe.minimum_symbol_matches < 1
            or (probe.expected_symbol_count is not None and probe.expected_symbol_count < 1)
        ):
            return "C1_SYMBOL_PROBE_INVALID"
    return None


def _compiler_env() -> dict[str, str]:
    return {
        "LANG": "C",
        "LANGUAGE": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "TZ": "UTC",
    }


def _identity_error(outcome: CommandOutcome, expected_sha256: str) -> str | None:
    if outcome.state is not RunState.COMPLETED or outcome.returncode != 0:
        return "C1_TOOLCHAIN_UNAVAILABLE"
    normalized = _normalize_diagnostic(outcome.stdout + outcome.stderr)
    if hashlib.sha256(normalized.encode("utf-8")).hexdigest() != expected_sha256:
        return "C1_TOOLCHAIN_IDENTITY_MISMATCH"
    return None


def _compile_succeeded(outcome: CommandOutcome) -> bool:
    return outcome.state is RunState.COMPLETED and outcome.returncode == 0


def _semantic_return(outcome: CommandOutcome) -> bool:
    return (
        outcome.state is RunState.COMPLETED
        and outcome.returncode is not None
        and outcome.returncode > 0
    )


def _coerce_output(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _evidence(outcome: CommandOutcome, temp: Path, root: Path) -> DiagnosticEvidence:
    return _evidence_from_text(
        outcome.stdout + outcome.stderr,
        returncode=outcome.returncode,
        run_state=outcome.state,
        temp=temp,
        root=root,
    )


def _evidence_from_text(
    text: str,
    *,
    returncode: int | None,
    run_state: RunState,
    temp: Path,
    root: Path,
) -> DiagnosticEvidence:
    normalized = _normalize_diagnostic(text)
    for original, replacement in sorted(
        ((str(temp), "<probe>"), (str(root), "<workspace>")),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        normalized = normalized.replace(original, replacement)
    return DiagnosticEvidence(
        digest_sha256=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        excerpt=normalized[:_MAX_DIAGNOSTIC_CHARS],
        returncode=returncode,
        run_state=run_state.value,
    )


def _normalize_diagnostic(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.splitlines()).strip()


def _empty_evidence() -> DiagnosticEvidence:
    return DiagnosticEvidence(
        digest_sha256=hashlib.sha256(b"").hexdigest(),
        excerpt="",
        returncode=None,
        run_state="not_run",
    )


def _scored_pass(contract: PublicApiContract) -> C1Receipt:
    return _receipt(
        contract,
        ReceiptDisposition.SCORED,
        "passed",
        1,
        "complete",
        None,
        None,
        _empty_evidence(),
    )


def _scored_failure(
    contract: PublicApiContract,
    phase: str,
    failure_code: str,
    probe_id: str,
    evidence: DiagnosticEvidence | None = None,
) -> C1Receipt:
    return _receipt(
        contract,
        ReceiptDisposition.SCORED,
        "failed",
        -1,
        phase,
        failure_code,
        probe_id,
        evidence or _empty_evidence(),
    )


def _unscored(
    contract: PublicApiContract,
    disposition: ReceiptDisposition,
    phase: str,
    failure_code: str,
    probe_id: str | None = None,
) -> C1Receipt:
    status = "not_evaluated" if disposition is ReceiptDisposition.NOT_EVALUATED else "invalid"
    return _receipt(
        contract,
        disposition,
        status,
        None,
        phase,
        failure_code,
        probe_id,
        _empty_evidence(),
    )


def _unscored_outcome(
    contract: PublicApiContract,
    disposition: ReceiptDisposition,
    phase: str,
    failure_code: str,
    outcome: CommandOutcome,
    temp: Path,
    root: Path,
    probe_id: str | None = None,
) -> C1Receipt:
    status = "not_evaluated" if disposition is ReceiptDisposition.NOT_EVALUATED else "invalid"
    return _receipt(
        contract,
        disposition,
        status,
        None,
        phase,
        failure_code,
        probe_id,
        _evidence(outcome, temp, root),
    )


def _receipt(
    contract: PublicApiContract,
    disposition: ReceiptDisposition,
    status: str,
    kernel: int | None,
    phase: str,
    failure_code: str | None,
    probe_id: str | None,
    evidence: DiagnosticEvidence,
) -> C1Receipt:
    if kernel not in {-1, 1, None}:
        raise ValueError("C1 kernels must be -1, +1, or absent")
    result = VerifierResult(
        verifier=VERIFIER_ID,
        status=status,
        kernel=kernel,
        phase=phase,
        failure_code=failure_code,
        probe_id=probe_id,
        evidence=evidence,
    )
    return C1Receipt(
        schema_version=SCHEMA_VERSION,
        category=CATEGORY,
        disposition=disposition.value,
        verifier_results=(result,),
        category_score=kernel,
        contract_version=contract.contract_version,
        compiler_profile=contract.compiler.profile_id,
    )
