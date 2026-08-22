"""Independent C4 verifier for C++ declaration/definition and linkage contracts.

The module intentionally accepts a trusted, task-specific contract.  It does not
infer a public API from compiler diagnostics and it never executes candidate code.
Definition binding and exhaustive linkage are validation stages of one semantic
verifier, not separate reward-bearing verifiers.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

import tree_sitter_cpp
from tree_sitter import Language, Node, Parser

SCHEMA_VERSION = "w8-cpp-category-receipt-v1"
CATEGORY = "C4"
VERIFIER_ID = "implementation-contract-linkage"
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_SAFE_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9_.+/@-]+$")


class InputDisposition(str, Enum):
    """Cause established by generic parsing/materialization infrastructure."""

    READY = "ready"
    CANDIDATE_FORMAT_INVALID = "candidate_format_invalid"
    WORKSPACE_INVALID = "workspace_invalid"
    INFRASTRUCTURE_INVALID = "infrastructure_invalid"
    CONTRACT_INVALID = "contract_invalid"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class CompilerProfile:
    """Pinned compiler identity and flags supplied by the trusted task contract."""

    executable: str
    identity_sha256: str
    compile_flags: tuple[str, ...] = (
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-fno-diagnostics-color",
    )
    link_flags: tuple[str, ...] = ()
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class C4Contract:
    """Trusted C4 contract; candidate content is never used to construct it."""

    contract_version: str
    header: str
    implementation_units: tuple[str, ...]
    definition_owners: tuple[str, ...]
    declaration_probe_source: str
    exhaustive_link_harness_source: str
    compiler: CompilerProfile
    include_directories: tuple[str, ...] = (".",)
    binding_preamble: str = ""


@dataclass(frozen=True)
class CommandOutcome:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class ExecutionInfrastructureError(RuntimeError):
    """Raised when command execution cannot yield trustworthy semantic evidence."""

    failure_code = "C4_INFRASTRUCTURE_EXECUTION_FAILURE"


class SandboxExecutionError(ExecutionInfrastructureError):
    failure_code = "C4_SANDBOX_FAILURE"


class CommandRunner(Protocol):
    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float,
    ) -> CommandOutcome: ...


class SubprocessRunner:
    """No-shell runner intended to execute inside the caller's outer sandbox."""

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float,
    ) -> CommandOutcome:
        try:
            completed = subprocess.run(
                [str(part) for part in args],
                cwd=cwd,
                env=dict(env),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise ExecutionInfrastructureError(f"executable unavailable: {args[0]}") from exc
        except PermissionError as exc:
            raise ExecutionInfrastructureError(f"executable is not runnable: {args[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ExecutionInfrastructureError(
                f"command exceeded the {timeout:g}s infrastructure timeout"
            ) from exc
        except OSError as exc:
            raise ExecutionInfrastructureError(f"command execution failed: {exc}") from exc
        if completed.returncode < 0:
            raise ExecutionInfrastructureError(
                f"command terminated by signal {-completed.returncode}"
            )
        return CommandOutcome(completed.returncode, completed.stdout, completed.stderr)


@dataclass(frozen=True)
class StageEvidence:
    stage: str
    status: str
    reward_bearing: bool = False
    failure_code: str | None = None
    command: tuple[str, ...] = ()
    diagnostic_sha256: str | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.reward_bearing:
            raise ValueError("C4 validation stages must never be reward-bearing")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "reward_bearing": self.reward_bearing,
            "failure_code": self.failure_code,
            "command": list(self.command),
            "diagnostic_sha256": self.diagnostic_sha256,
            "diagnostic": self.diagnostic,
        }


@dataclass(frozen=True)
class VerifierResult:
    verifier: str
    status: str
    kernel: int | None
    phase: str | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        if self.verifier != VERIFIER_ID:
            raise ValueError("unexpected C4 verifier id")
        if self.kernel not in (-1, 1, None):
            raise ValueError("semantic verifier kernels must be exactly -1, +1, or absent")
        if self.kernel == 1 and (self.status != "passed" or self.failure_code is not None):
            raise ValueError("passing C4 result is inconsistent")
        if self.kernel == -1 and (self.status != "failed" or not self.failure_code):
            raise ValueError("failing C4 result is inconsistent")
        if self.kernel is None and (self.status != "not_evaluated" or not self.failure_code):
            raise ValueError("non-scored C4 result is inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": self.verifier,
            "status": self.status,
            "kernel": self.kernel,
            "phase": self.phase,
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True)
class C4Receipt:
    disposition: str
    contract_version: str | None
    verifier_result: VerifierResult
    attribution_evidence: tuple[StageEvidence, ...] = field(default_factory=tuple)
    compiler_profile: dict[str, Any] | None = None
    schema_version: str = SCHEMA_VERSION
    category: str = CATEGORY

    def __post_init__(self) -> None:
        valid_dispositions = {
            "scored",
            "candidate_format_invalid",
            "workspace_invalid",
            "infrastructure_invalid",
            "contract_invalid",
            "not_evaluated",
        }
        if self.schema_version != SCHEMA_VERSION or self.category != CATEGORY:
            raise ValueError("invalid C4 receipt identity")
        if self.disposition not in valid_dispositions:
            raise ValueError("invalid C4 receipt disposition")
        if any(item.reward_bearing for item in self.attribution_evidence):
            raise ValueError("C4 attribution stages cannot carry reward")
        if self.disposition == "scored":
            if self.kernel not in (-1, 1) or not self.contract_version:
                raise ValueError("scored C4 receipt is incomplete")
        elif self.kernel is not None:
            raise ValueError("non-scored C4 receipt cannot contain reward")

    @property
    def kernel(self) -> int | None:
        return self.verifier_result.kernel

    @property
    def category_score(self) -> int | None:
        return self.kernel

    @property
    def kernels(self) -> tuple[int, ...] | None:
        return (self.kernel,) if self.kernel is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "category": self.category,
            "disposition": self.disposition,
            "contract_version": self.contract_version,
            "verifier_results": [self.verifier_result.to_dict()],
            "kernels": list(self.kernels) if self.kernels is not None else None,
            "kernel": self.kernel,
            "category_score": self.category_score,
            "attribution_evidence": [item.to_dict() for item in self.attribution_evidence],
            "compiler_profile": self.compiler_profile,
        }


class _AmbiguousTransformation(ValueError):
    pass


def _parser() -> Parser:
    return Parser(Language(tree_sitter_cpp.language()))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _normalized_diagnostic(
    stdout: str,
    stderr: str,
    *,
    workspace: Path | None = None,
    scratch: Path | None = None,
) -> tuple[str, str]:
    text = _ANSI_ESCAPE.sub("", "\n".join(part for part in (stdout, stderr) if part))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    replacements: list[tuple[str, str]] = []
    if workspace is not None:
        replacements.append((str(workspace), "<workspace>"))
    if scratch is not None:
        replacements.append((str(scratch), "<scratch>"))
    for source, replacement in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, replacement)
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    digest = _sha256_text(text)
    return text[:4000], digest


def _normalized_command(args: Sequence[str], workspace: Path, scratch: Path) -> tuple[str, ...]:
    result: list[str] = []
    for arg in args:
        value = str(arg).replace(str(workspace), "<workspace>").replace(str(scratch), "<scratch>")
        result.append(value)
    return tuple(result)


def _evidence(
    stage: str,
    status: str,
    *,
    args: Sequence[str] = (),
    outcome: CommandOutcome | None = None,
    failure_code: str | None = None,
    workspace: Path | None = None,
    scratch: Path | None = None,
) -> StageEvidence:
    diagnostic = None
    digest = None
    command: tuple[str, ...] = tuple(str(arg) for arg in args)
    if workspace is not None and scratch is not None:
        command = _normalized_command(args, workspace, scratch)
    if outcome is not None:
        diagnostic, digest = _normalized_diagnostic(
            outcome.stdout, outcome.stderr, workspace=workspace, scratch=scratch
        )
    return StageEvidence(
        stage=stage,
        status=status,
        failure_code=failure_code,
        command=command,
        diagnostic_sha256=digest,
        diagnostic=diagnostic,
    )


def fingerprint_compiler(
    executable: str,
    *,
    runner: CommandRunner | None = None,
    cwd: Path | None = None,
    timeout: float = 10.0,
) -> str:
    """Return the exact compiler identity digest used by a trusted contract."""

    command_runner = runner or SubprocessRunner()
    run_cwd = cwd or Path.cwd()
    outcome = command_runner.run(
        [executable, "--version"],
        cwd=run_cwd,
        env={"LANG": "C", "LC_ALL": "C", "PATH": os.defpath, "TZ": "UTC"},
        timeout=timeout,
    )
    if outcome.returncode != 0:
        raise ExecutionInfrastructureError("compiler identity command failed")
    identity, _ = _normalized_diagnostic(outcome.stdout, outcome.stderr)
    return _sha256_text(identity)


def _invalid_receipt(
    disposition: str,
    failure_code: str,
    *,
    contract_version: str | None,
    evidence: Sequence[StageEvidence] = (),
    compiler_profile: dict[str, Any] | None = None,
) -> C4Receipt:
    return C4Receipt(
        disposition=disposition,
        contract_version=contract_version,
        verifier_result=VerifierResult(
            verifier=VERIFIER_ID,
            status="not_evaluated",
            kernel=None,
            failure_code=failure_code,
        ),
        attribution_evidence=tuple(evidence),
        compiler_profile=compiler_profile,
    )


def _validate_relative_path(value: str) -> PurePosixPath:
    if not value or not _SAFE_RELATIVE_PATH.fullmatch(value):
        raise ValueError(f"unsafe or empty contract path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"contract path escapes the candidate workspace: {value!r}")
    return path


def _validate_contract(contract: C4Contract) -> None:
    if not contract.contract_version.strip():
        raise ValueError("contract_version is required")
    _validate_relative_path(contract.header)
    if not contract.implementation_units:
        raise ValueError("at least one implementation translation unit is required")
    for path in (*contract.implementation_units, *contract.include_directories):
        _validate_relative_path(path)
    if not contract.definition_owners or any(
        not owner.strip() for owner in contract.definition_owners
    ):
        raise ValueError("definition_owners must identify at least one contract-owned symbol root")
    if not contract.declaration_probe_source.strip():
        raise ValueError("declaration_probe_source is required")
    if not contract.exhaustive_link_harness_source.strip():
        raise ValueError("exhaustive_link_harness_source is required")
    profile = contract.compiler
    if not profile.executable or not Path(profile.executable).is_absolute():
        raise ValueError("the compiler executable must be an absolute pinned path")
    if not re.fullmatch(r"[0-9a-f]{64}", profile.identity_sha256):
        raise ValueError("compiler identity_sha256 must be a lowercase SHA-256 digest")
    if profile.timeout_seconds <= 0:
        raise ValueError("compiler timeout must be positive")
    forbidden = {"-c", "-o", "-E", "-S"}
    if forbidden.intersection(profile.compile_flags):
        raise ValueError("compile_flags must not control verifier phases or outputs")


def _workspace_path_is_safe(path: Path, workspace: Path) -> bool:
    try:
        relative = path.relative_to(workspace)
        if not path.resolve().is_relative_to(workspace):
            return False
    except (OSError, ValueError):
        return False
    current = workspace
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    return True


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _contains(outer: Node, inner: Node) -> bool:
    return outer.start_byte <= inner.start_byte and inner.end_byte <= outer.end_byte


def _definition_declarator_name(node: Node, source: bytes) -> str:
    declarator = node.child_by_field_name("declarator")
    if declarator is None:
        raise _AmbiguousTransformation("function definition has no declarator")
    current = declarator
    while True:
        child = current.child_by_field_name("declarator")
        if child is None:
            break
        current = child
    raw = source[current.start_byte : current.end_byte].decode("utf-8", errors="strict")
    return re.sub(r"\s+", "", raw).lstrip(":")


def _namespace_chain(node: Node, source: bytes) -> tuple[str, ...]:
    names: list[str] = []
    parent = node.parent
    while parent is not None and parent.type != "translation_unit":
        if parent.type == "namespace_definition":
            name = parent.child_by_field_name("name")
            if name is None:
                raise _AmbiguousTransformation("anonymous namespace around contract definition")
            value = source[name.start_byte : name.end_byte].decode("utf-8", errors="strict")
            names.append(re.sub(r"\s+", "", value))
        elif parent.type not in {"declaration_list"}:
            raise _AmbiguousTransformation(
                f"unsupported contract definition ancestor: {parent.type}"
            )
        parent = parent.parent
    names.reverse()
    return tuple(names)


def _qualified_definition_name(node: Node, source: bytes) -> str:
    raw = _definition_declarator_name(node, source)
    namespaces = _namespace_chain(node, source)
    namespace_prefix = "::".join(namespaces)
    if namespace_prefix and not (
        raw == namespace_prefix or raw.startswith(namespace_prefix + "::")
    ):
        return namespace_prefix + "::" + raw
    return raw


def _contract_owned(name: str, owners: Sequence[str]) -> bool:
    return any(name == owner or name.startswith(owner + "::") for owner in owners)


def _transform_definition(node: Node, source: bytes) -> bytes:
    body = node.child_by_field_name("body")
    if body is None:
        clauses = [child for child in node.named_children if child.type.endswith("method_clause")]
        if len(clauses) == 1 and clauses[0].type in {
            "default_method_clause",
            "delete_method_clause",
        }:
            return source[node.start_byte : node.end_byte]
        raise _AmbiguousTransformation("unsupported definition without a compound body")
    if body.type != "compound_statement":
        raise _AmbiguousTransformation(f"unsupported function body node: {body.type}")
    prefix = bytearray(source[node.start_byte : body.start_byte])
    initializer = next(
        (child for child in node.children if child.type == "field_initializer_list"), None
    )
    if initializer is not None:
        relative_start = initializer.start_byte - node.start_byte
        relative_end = initializer.end_byte - node.start_byte
        prefix[relative_start:relative_end] = b" " * (relative_end - relative_start)
    return bytes(prefix) + b"{ for (;;) {} }"


def _binding_probe(source: bytes, contract: C4Contract) -> tuple[bytes, tuple[str, ...]]:
    tree = _parser().parse(source)
    if any(
        node.type.startswith("preproc_") and node.type != "preproc_include"
        for node in _walk(tree.root_node)
    ):
        raise _AmbiguousTransformation("preprocessor constructs may hide or synthesize definitions")
    definitions = [node for node in _walk(tree.root_node) if node.type == "function_definition"]
    allowed_error_regions: list[Node] = []
    for definition in definitions:
        body = definition.child_by_field_name("body")
        if body is not None:
            allowed_error_regions.append(body)
        initializer = next(
            (child for child in definition.children if child.type == "field_initializer_list"), None
        )
        if initializer is not None:
            allowed_error_regions.append(initializer)
    for syntax_node in _walk(tree.root_node):
        if (syntax_node.is_error or syntax_node.is_missing) and not any(
            _contains(region, syntax_node) for region in allowed_error_regions
        ):
            raise _AmbiguousTransformation(
                "syntax recovery escaped implementation bodies; definition attribution is ambiguous"
            )

    selected: list[tuple[str, bytes, tuple[str, ...]]] = []
    for definition in definitions:
        qualified_name = _qualified_definition_name(definition, source)
        if _contract_owned(qualified_name, contract.definition_owners):
            selected.append(
                (
                    qualified_name,
                    _transform_definition(definition, source),
                    _namespace_chain(definition, source),
                )
            )
    selected.sort(key=lambda item: (item[0], item[1]))

    chunks = [f'#include "{contract.header}"\n'.encode()]
    if contract.binding_preamble:
        chunks.append(contract.binding_preamble.encode("utf-8") + b"\n")
    names: list[str] = []
    for qualified_name, definition, namespaces in selected:
        names.append(qualified_name)
        for namespace in namespaces:
            chunks.append(f"namespace {namespace} {{\n".encode())
        chunks.append(definition + b"\n")
        for _ in reversed(namespaces):
            chunks.append(b"}\n")
    return b"".join(chunks), tuple(names)


def _compiler_profile_doc(profile: CompilerProfile, identity: str | None = None) -> dict[str, Any]:
    return {
        "executable": profile.executable,
        "identity_sha256": identity or profile.identity_sha256,
        "compile_flags": list(profile.compile_flags),
        "link_flags": list(profile.link_flags),
        "timeout_seconds": profile.timeout_seconds,
    }


def _command_environment(scratch: Path) -> dict[str, str]:
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "TMPDIR": str(scratch),
        "TZ": "UTC",
    }


def _run_stage(
    runner: CommandRunner,
    stage: str,
    args: Sequence[str],
    *,
    workspace: Path,
    scratch: Path,
    timeout: float,
    expected_artifact: Path | None = None,
) -> tuple[CommandOutcome, StageEvidence]:
    outcome = runner.run(
        args,
        cwd=scratch,
        env=_command_environment(scratch),
        timeout=timeout,
    )
    if (
        outcome.returncode == 0
        and expected_artifact is not None
        and (not expected_artifact.is_file() or expected_artifact.is_symlink())
    ):
        raise ExecutionInfrastructureError(
            f"stage {stage} reported success without producing its required artifact"
        )
    status = "passed" if outcome.returncode == 0 else "failed"
    return outcome, _evidence(
        stage,
        status,
        args=args,
        outcome=outcome,
        workspace=workspace,
        scratch=scratch,
    )


def evaluate_cpp_c4(
    candidate_workspace: object,
    contract: C4Contract,
    *,
    expected_contract_version: str,
    runner: CommandRunner | None = None,
    input_disposition: InputDisposition = InputDisposition.READY,
    input_failure_code: str | None = None,
) -> C4Receipt:
    """Evaluate one C4 kernel, or return a non-scored disposition.

    The caller must materialize candidate files in an isolated workspace and
    provide a trusted exhaustive contract.  Candidate code is compiled and linked
    after bodies and constructor initializers are neutralized; it is never run.
    """

    if not isinstance(contract, C4Contract):
        return _invalid_receipt(
            "contract_invalid",
            "C4_CONTRACT_INVALID",
            contract_version=getattr(contract, "contract_version", None),
        )
    try:
        _validate_contract(contract)
    except (TypeError, ValueError) as exc:
        evidence = (_evidence("contract-validation", "invalid", failure_code=str(exc)),)
        return _invalid_receipt(
            "contract_invalid",
            "C4_CONTRACT_INVALID",
            contract_version=getattr(contract, "contract_version", None),
            evidence=evidence,
        )
    if contract.contract_version != expected_contract_version:
        return _invalid_receipt(
            "contract_invalid",
            "C4_CONTRACT_VERSION_MISMATCH",
            contract_version=contract.contract_version,
        )
    if input_disposition is not InputDisposition.READY:
        return _invalid_receipt(
            input_disposition.value,
            input_failure_code or f"C4_{input_disposition.value.upper()}",
            contract_version=contract.contract_version,
        )
    if not isinstance(candidate_workspace, (str, os.PathLike)):
        return _invalid_receipt(
            "candidate_format_invalid",
            "C4_CANDIDATE_RESPONSE_MALFORMED",
            contract_version=contract.contract_version,
        )
    workspace_input = Path(candidate_workspace)
    if not workspace_input.exists() or not workspace_input.is_dir() or workspace_input.is_symlink():
        return _invalid_receipt(
            "workspace_invalid",
            "C4_WORKSPACE_INVALID",
            contract_version=contract.contract_version,
        )
    workspace = workspace_input.resolve()

    header = workspace / contract.header
    if not header.is_file() or not _workspace_path_is_safe(header, workspace):
        return _invalid_receipt(
            "not_evaluated",
            "C4_BLOCKED_BY_DECLARATION_SURFACE",
            contract_version=contract.contract_version,
        )
    implementation_paths = [workspace / relative for relative in contract.implementation_units]
    if any(
        not path.is_file() or not _workspace_path_is_safe(path, workspace)
        for path in implementation_paths
    ):
        return _invalid_receipt(
            "candidate_format_invalid",
            "C4_IMPLEMENTATION_UNIT_MISSING",
            contract_version=contract.contract_version,
        )
    include_paths = [workspace / relative for relative in contract.include_directories]
    if any(
        not path.is_dir() or not _workspace_path_is_safe(path, workspace) for path in include_paths
    ):
        return _invalid_receipt(
            "workspace_invalid",
            "C4_INCLUDE_WORKSPACE_INVALID",
            contract_version=contract.contract_version,
        )

    command_runner = runner or SubprocessRunner()
    profile = contract.compiler
    evidence: list[StageEvidence] = []
    try:
        identity = fingerprint_compiler(
            profile.executable,
            runner=command_runner,
            cwd=workspace,
            timeout=min(profile.timeout_seconds, 10.0),
        )
    except ExecutionInfrastructureError as exc:
        evidence.append(
            _evidence(
                "infrastructure",
                "invalid",
                failure_code=getattr(exc, "failure_code", "C4_INFRASTRUCTURE_EXECUTION_FAILURE"),
            )
        )
        return _invalid_receipt(
            "infrastructure_invalid",
            getattr(exc, "failure_code", "C4_INFRASTRUCTURE_EXECUTION_FAILURE"),
            contract_version=contract.contract_version,
            evidence=evidence,
            compiler_profile=_compiler_profile_doc(profile),
        )
    if identity != profile.identity_sha256:
        return _invalid_receipt(
            "infrastructure_invalid",
            "C4_COMPILER_PROFILE_MISMATCH",
            contract_version=contract.contract_version,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )

    try:
        binding_sources: list[tuple[bytes, tuple[str, ...]]] = []
        for path in implementation_paths:
            source = path.read_bytes()
            binding_sources.append(_binding_probe(source, contract))
    except UnicodeDecodeError:
        return _invalid_receipt(
            "candidate_format_invalid",
            "C4_SOURCE_ENCODING_INVALID",
            contract_version=contract.contract_version,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )
    except _AmbiguousTransformation as exc:
        evidence.append(
            _evidence(
                "definition-transformation",
                "ambiguous",
                failure_code=str(exc),
            )
        )
        return _invalid_receipt(
            "not_evaluated",
            "C4_ATTRIBUTION_AMBIGUOUS",
            contract_version=contract.contract_version,
            evidence=evidence,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )
    except OSError as exc:
        evidence.append(_evidence("materialization", "invalid", failure_code=str(exc)))
        return _invalid_receipt(
            "workspace_invalid",
            "C4_WORKSPACE_READ_FAILURE",
            contract_version=contract.contract_version,
            evidence=evidence,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )

    include_args = [flag for path in include_paths for flag in ("-I", str(path))]
    compile_prefix = [profile.executable, *profile.compile_flags, *include_args]
    try:
        with tempfile.TemporaryDirectory(prefix="w8-c4-") as scratch_name:
            scratch = Path(scratch_name)
            declaration_source = scratch / "declaration_probe.cpp"
            declaration_object = scratch / "declaration_probe.o"
            declaration_source.write_text(contract.declaration_probe_source, encoding="utf-8")
            declaration_args = [
                *compile_prefix,
                "-c",
                str(declaration_source),
                "-o",
                str(declaration_object),
            ]
            outcome, item = _run_stage(
                command_runner,
                "declaration-surface",
                declaration_args,
                workspace=workspace,
                scratch=scratch,
                timeout=profile.timeout_seconds,
                expected_artifact=declaration_object,
            )
            evidence.append(item)
            if outcome.returncode != 0:
                return _invalid_receipt(
                    "not_evaluated",
                    "C4_BLOCKED_BY_DECLARATION_SURFACE",
                    contract_version=contract.contract_version,
                    evidence=evidence,
                    compiler_profile=_compiler_profile_doc(profile, identity),
                )

            binding_objects: list[Path] = []
            for index, (source, names) in enumerate(binding_sources):
                source_path = scratch / f"definition_binding_{index}.cpp"
                object_path = scratch / f"definition_binding_{index}.o"
                source_path.write_bytes(source)
                # Neutralization intentionally removes parameter uses.  Suppress only
                # the warning introduced by that transformation; contract and harness
                # probes retain the exact pinned warning profile.
                args = [
                    *compile_prefix,
                    "-Wno-unused-parameter",
                    "-c",
                    str(source_path),
                    "-o",
                    str(object_path),
                ]
                outcome, item = _run_stage(
                    command_runner,
                    f"definition-binding[{index}]",
                    args,
                    workspace=workspace,
                    scratch=scratch,
                    timeout=profile.timeout_seconds,
                    expected_artifact=object_path,
                )
                evidence.append(item)
                evidence.append(
                    StageEvidence(
                        stage=f"definition-symbols[{index}]",
                        status="observed",
                        diagnostic=",".join(names),
                        diagnostic_sha256=_sha256_text(",".join(names)),
                    )
                )
                if outcome.returncode != 0:
                    return C4Receipt(
                        disposition="scored",
                        contract_version=contract.contract_version,
                        verifier_result=VerifierResult(
                            verifier=VERIFIER_ID,
                            status="failed",
                            kernel=-1,
                            phase="definition-binding",
                            failure_code="C4_DEFINITION_BINDING_FAILURE",
                        ),
                        attribution_evidence=tuple(evidence),
                        compiler_profile=_compiler_profile_doc(profile, identity),
                    )
                binding_objects.append(object_path)

            harness_source = scratch / "exhaustive_link_harness.cpp"
            harness_object = scratch / "exhaustive_link_harness.o"
            harness_source.write_text(contract.exhaustive_link_harness_source, encoding="utf-8")
            harness_args = [
                *compile_prefix,
                "-c",
                str(harness_source),
                "-o",
                str(harness_object),
            ]
            outcome, item = _run_stage(
                command_runner,
                "exhaustive-harness",
                harness_args,
                workspace=workspace,
                scratch=scratch,
                timeout=profile.timeout_seconds,
                expected_artifact=harness_object,
            )
            evidence.append(item)
            if outcome.returncode != 0:
                return _invalid_receipt(
                    "not_evaluated",
                    "C4_BLOCKED_BY_DECLARATION_SURFACE",
                    contract_version=contract.contract_version,
                    evidence=evidence,
                    compiler_profile=_compiler_profile_doc(profile, identity),
                )

            linked_probe = scratch / "c4_link_probe"
            link_args = [
                profile.executable,
                *profile.link_flags,
                *(str(path) for path in binding_objects),
                str(harness_object),
                "-o",
                str(linked_probe),
            ]
            outcome, item = _run_stage(
                command_runner,
                "exhaustive-link",
                link_args,
                workspace=workspace,
                scratch=scratch,
                timeout=profile.timeout_seconds,
                expected_artifact=linked_probe,
            )
            evidence.append(item)
            if outcome.returncode != 0:
                return C4Receipt(
                    disposition="scored",
                    contract_version=contract.contract_version,
                    verifier_result=VerifierResult(
                        verifier=VERIFIER_ID,
                        status="failed",
                        kernel=-1,
                        phase="link",
                        failure_code="C4_LINK_COMPLETENESS_FAILURE",
                    ),
                    attribution_evidence=tuple(evidence),
                    compiler_profile=_compiler_profile_doc(profile, identity),
                )
    except ExecutionInfrastructureError as exc:
        evidence.append(
            _evidence(
                "infrastructure",
                "invalid",
                failure_code=getattr(exc, "failure_code", "C4_INFRASTRUCTURE_EXECUTION_FAILURE"),
            )
        )
        return _invalid_receipt(
            "infrastructure_invalid",
            getattr(exc, "failure_code", "C4_INFRASTRUCTURE_EXECUTION_FAILURE"),
            contract_version=contract.contract_version,
            evidence=evidence,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )
    except OSError as exc:
        evidence.append(_evidence("scratch-workspace", "invalid", failure_code=str(exc)))
        return _invalid_receipt(
            "infrastructure_invalid",
            "C4_SCRATCH_WORKSPACE_FAILURE",
            contract_version=contract.contract_version,
            evidence=evidence,
            compiler_profile=_compiler_profile_doc(profile, identity),
        )

    return C4Receipt(
        disposition="scored",
        contract_version=contract.contract_version,
        verifier_result=VerifierResult(
            verifier=VERIFIER_ID,
            status="passed",
            kernel=1,
        ),
        attribution_evidence=tuple(evidence),
        compiler_profile=_compiler_profile_doc(profile, identity),
    )
