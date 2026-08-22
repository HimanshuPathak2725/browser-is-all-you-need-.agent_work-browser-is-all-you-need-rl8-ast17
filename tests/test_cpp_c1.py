from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from glm47_posttraining.verifiers.cpp_c1 import (
    C1Verifier,
    CommandOutcome,
    CompileContractProbe,
    CompilerProfile,
    InputDisposition,
    PublicApiContract,
    RunState,
    SubprocessCommandRunner,
    SymbolContractProbe,
    _compiler_env,
    fingerprint_tool,
)

GOOD_HEADER = """\
#pragma once
#include <string>
namespace specimen {
class cipher {
public:
    explicit cipher(const std::string& text);
    std::string encode(const std::string& key) const;
};
}
"""


def _toolchain_available() -> bool:
    return shutil.which("g++") is not None and shutil.which("nm") is not None


requires_cpp_toolchain = pytest.mark.skipif(
    not _toolchain_available(), reason="C1 integration tests require g++ and GNU-compatible nm"
)


def _contract(**changes: object) -> PublicApiContract:
    compiler_path = Path(shutil.which("g++") or "/definitely/missing/g++").resolve()
    symbol_path = Path(shutil.which("nm") or "/definitely/missing/nm").resolve()
    compiler_identity = fingerprint_tool(str(compiler_path)) if compiler_path.exists() else "0" * 64
    symbol_identity = fingerprint_tool(str(symbol_path)) if symbol_path.exists() else "0" * 64
    compiler = CompilerProfile(
        profile_id="gcc-cpp17-test",
        compiler=str(compiler_path),
        identity_sha256=compiler_identity,
        symbol_inspector=str(symbol_path),
        symbol_identity_sha256=symbol_identity,
    )
    probes = (
        CompileContractProbe(
            "namespace-visible",
            "namespace c1_namespace_probe { using namespace ::specimen; }\n",
            "C1_NAMESPACE_MISSING",
        ),
        CompileContractProbe(
            "class-visible",
            "#include <type_traits>\nstatic_assert(std::is_class_v<::specimen::cipher>);\n",
            "C1_CLASS_MISSING",
        ),
        CompileContractProbe(
            "constructor-public",
            "#include <type_traits>\n"
            "static_assert(std::is_constructible_v<::specimen::cipher, const std::string&>);\n",
            "C1_CONSTRUCTOR_MISSING_OR_INACCESSIBLE",
        ),
        CompileContractProbe(
            "constructor-explicit",
            "void c1_accept_cipher(::specimen::cipher);\n"
            "void c1_reject_implicit(const std::string& value) { c1_accept_cipher(value); }\n",
            "C1_CONSTRUCTOR_EXPLICITNESS_MISMATCH",
            expect_success=False,
        ),
        CompileContractProbe(
            "encode-signature",
            "using c1_encode_signature = std::string (::specimen::cipher::*)"
            "(const std::string&) const;\n"
            "constexpr c1_encode_signature c1_encode = "
            "static_cast<c1_encode_signature>(&::specimen::cipher::encode);\n",
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
    )
    symbol_probe = SymbolContractProbe(
        probe_id="constructor-exact-symbol",
        consumer_source=(
            "::specimen::cipher* c1_make_cipher(const std::string& value) {\n"
            "    return new ::specimen::cipher(value);\n"
            "}\n"
        ),
        provider_source=(
            "#include <string>\n"
            "namespace specimen {\n"
            "class cipher { public: explicit cipher(const std::string&); };\n"
            "cipher::cipher(const std::string&) {}\n"
            "}\n"
        ),
        baseline_source=(
            "#include <string>\n"
            "namespace specimen {\n"
            "class cipher { public: explicit cipher(const std::string&); };\n"
            "}\n"
        ),
        failure_code="C1_CONSTRUCTOR_SIGNATURE_MISMATCH",
    )
    contract = PublicApiContract(
        contract_version="specimen-c1-v1",
        public_header="cipher.hpp",
        compiler=compiler,
        compile_probes=probes,
        symbol_probes=(symbol_probe,),
    )
    return replace(contract, **changes)


def _workspace(
    tmp_path: Path, header: str = GOOD_HEADER, implementation: str | None = None
) -> Path:
    workspace = tmp_path / "candidate"
    workspace.mkdir(parents=True)
    (workspace / "cipher.hpp").write_text(header, encoding="utf-8")
    if implementation is not None:
        (workspace / "cipher.cpp").write_text(implementation, encoding="utf-8")
    return workspace


def _assert_failed(receipt, failure_code: str) -> None:
    assert receipt.disposition == "scored"
    assert receipt.kernel == -1
    assert receipt.category_score == -1
    assert receipt.verifier_results[0].failure_code == failure_code


@requires_cpp_toolchain
def test_valid_public_contract_scores_positive(tmp_path):
    receipt = C1Verifier().evaluate(_workspace(tmp_path), _contract())

    assert receipt.disposition == "scored"
    assert receipt.kernel == 1
    assert receipt.category_score == 1
    assert len(receipt.verifier_results) == 1
    assert receipt.verifier_results[0].verifier == "public-api-contract"


@requires_cpp_toolchain
def test_required_header_missing_is_semantic_c1_failure(tmp_path):
    workspace = tmp_path / "candidate"
    workspace.mkdir()

    _assert_failed(
        C1Verifier().evaluate(workspace, _contract()),
        "C1_REQUIRED_HEADER_MISSING",
    )


@requires_cpp_toolchain
def test_non_self_contained_header_is_c1_failure(tmp_path):
    header = GOOD_HEADER.replace("#include <string>\n", "")

    _assert_failed(
        C1Verifier().evaluate(_workspace(tmp_path, header), _contract()),
        "C1_HEADER_NOT_SELF_CONTAINED",
    )


@pytest.mark.parametrize(
    ("header", "failure_code"),
    [
        (
            GOOD_HEADER.replace("namespace specimen {", "namespace other {"),
            "C1_NAMESPACE_MISSING",
        ),
        (
            GOOD_HEADER.replace("class cipher", "class other").replace(
                "explicit cipher(", "explicit other("
            ),
            "C1_CLASS_MISSING",
        ),
        (
            GOOD_HEADER.replace("    explicit cipher(const std::string& text);\n", ""),
            "C1_CONSTRUCTOR_MISSING_OR_INACCESSIBLE",
        ),
        (
            GOOD_HEADER.replace("public:\n    explicit cipher", "private:\n    explicit cipher"),
            "C1_CONSTRUCTOR_MISSING_OR_INACCESSIBLE",
        ),
        (
            GOOD_HEADER.replace("    explicit cipher", "    cipher"),
            "C1_CONSTRUCTOR_EXPLICITNESS_MISMATCH",
        ),
        (
            GOOD_HEADER.replace("    std::string encode(const std::string& key) const;\n", ""),
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
        (
            GOOD_HEADER.replace("const std::string& key", "int key"),
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
        (
            GOOD_HEADER.replace("std::string encode", "int encode"),
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
        (
            GOOD_HEADER.replace(" key) const;", " key);"),
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
        (
            GOOD_HEADER.replace(
                "    std::string encode(const std::string& key) const;",
                "private:\n    std::string encode(const std::string& key) const;",
            ),
            "C1_METHOD_SIGNATURE_MISMATCH",
        ),
    ],
)
@requires_cpp_toolchain
def test_public_contract_failure_classes(header, failure_code, tmp_path):
    _assert_failed(
        C1Verifier().evaluate(_workspace(tmp_path, header), _contract()),
        failure_code,
    )


@requires_cpp_toolchain
def test_exact_constructor_signature_uses_semantic_symbol_binding(tmp_path):
    # Construction remains viable with a by-value overload, so the earlier
    # is_constructible check passes. The raw ABI symbol proves exact identity.
    header = GOOD_HEADER.replace(
        "explicit cipher(const std::string& text)", "explicit cipher(std::string text)"
    )

    _assert_failed(
        C1Verifier().evaluate(_workspace(tmp_path, header), _contract()),
        "C1_CONSTRUCTOR_SIGNATURE_MISMATCH",
    )


@requires_cpp_toolchain
def test_constructor_type_alias_is_semantically_equivalent(tmp_path):
    header = GOOD_HEADER.replace(
        "class cipher {\npublic:\n    explicit cipher(const std::string& text);",
        "class cipher {\npublic:\n    using text_type = std::string;\n"
        "    explicit cipher(const text_type& text);",
    )

    assert C1Verifier().evaluate(_workspace(tmp_path, header), _contract()).kernel == 1


@pytest.mark.parametrize(
    "implementation",
    [
        "this is a C2 syntax error;",
        "// C4: declarations are intentionally left undefined\n",
        "namespace wrong { void mismatched_definition(); }\n",
        "// C3: a compiling implementation could return the wrong answer\n",
    ],
)
@requires_cpp_toolchain
def test_candidate_implementation_is_outside_c1(tmp_path, implementation):
    receipt = C1Verifier().evaluate(_workspace(tmp_path, GOOD_HEADER, implementation), _contract())

    assert receipt.kernel == 1


@requires_cpp_toolchain
def test_candidate_omission_is_cause_based(tmp_path):
    workspace = tmp_path / "candidate"
    workspace.mkdir()

    semantic = C1Verifier().evaluate(workspace, _contract())
    malformed = C1Verifier().evaluate(
        workspace,
        _contract(),
        input_disposition=InputDisposition.CANDIDATE_FORMAT_INVALID,
        input_failure_code="P1_INCOMPLETE_GENERATION",
    )

    assert semantic.kernel == -1
    assert malformed.disposition == "candidate_format_invalid"
    assert malformed.kernel is None
    assert malformed.category_score is None


@requires_cpp_toolchain
def test_contract_version_mismatch_is_unscored(tmp_path):
    receipt = C1Verifier().evaluate(
        _workspace(tmp_path), _contract(), expected_contract_version="other-v2"
    )

    assert receipt.disposition == "contract_invalid"
    assert receipt.kernel is None
    assert receipt.category_score is None


@pytest.mark.parametrize(
    "input_disposition",
    [
        InputDisposition.CANDIDATE_FORMAT_INVALID,
        InputDisposition.WORKSPACE_INVALID,
        InputDisposition.INFRASTRUCTURE_INVALID,
        InputDisposition.CONTRACT_INVALID,
        InputDisposition.NOT_EVALUATED,
    ],
)
def test_upstream_invalid_dispositions_never_score(tmp_path, input_disposition):
    receipt = C1Verifier().evaluate(tmp_path, _contract(), input_disposition=input_disposition)

    assert receipt.disposition == input_disposition.value
    assert receipt.kernel is None
    assert receipt.category_score is None


def test_missing_workspace_is_unscored():
    receipt = C1Verifier().evaluate("/definitely/missing/c1-workspace", _contract())

    assert receipt.disposition == "workspace_invalid"
    assert receipt.kernel is None


def test_public_header_symlink_escape_is_workspace_invalid(tmp_path):
    outside = tmp_path / "outside.hpp"
    outside.write_text(GOOD_HEADER, encoding="utf-8")
    workspace = tmp_path / "candidate"
    workspace.mkdir()
    (workspace / "cipher.hpp").symlink_to(outside)

    receipt = C1Verifier().evaluate(workspace, _contract())

    assert receipt.disposition == "workspace_invalid"
    assert receipt.kernel is None
    assert receipt.category_score is None


def test_invalid_contract_is_unscored(tmp_path):
    contract = replace(_contract(), public_header="../escape.hpp")

    receipt = C1Verifier().evaluate(tmp_path, contract)

    assert receipt.disposition == "contract_invalid"
    assert receipt.kernel is None


def test_contract_without_task_api_probes_is_invalid(tmp_path):
    contract = replace(_contract(), compile_probes=(), symbol_probes=())

    receipt = C1Verifier().evaluate(tmp_path, contract)

    assert receipt.disposition == "contract_invalid"
    assert receipt.kernel is None


class FixedRunner:
    def __init__(self, outcome: CommandOutcome):
        self.outcome = outcome

    def run(self, *_args, **_kwargs):
        return self.outcome


@pytest.mark.parametrize(
    "outcome",
    [
        CommandOutcome(RunState.LAUNCH_FAILED, stderr="sandbox denied"),
        CommandOutcome(RunState.TIMED_OUT, stderr="resource timeout"),
    ],
)
def test_infrastructure_failures_never_score(tmp_path, outcome):
    receipt = C1Verifier(FixedRunner(outcome)).evaluate(_workspace(tmp_path), _contract())

    assert receipt.disposition == "infrastructure_invalid"
    assert receipt.kernel is None
    assert receipt.category_score is None


@requires_cpp_toolchain
def test_compiler_unavailable_never_scores(tmp_path):
    contract = replace(
        _contract(),
        compiler=replace(_contract().compiler, compiler="/definitely/missing/c1-compiler"),
    )

    receipt = C1Verifier().evaluate(_workspace(tmp_path), contract)

    assert receipt.disposition == "infrastructure_invalid"
    assert receipt.kernel is None


@requires_cpp_toolchain
def test_symbol_inspector_unavailable_never_scores(tmp_path):
    contract = replace(
        _contract(),
        compiler=replace(_contract().compiler, symbol_inspector="/definitely/missing/c1-nm"),
    )

    receipt = C1Verifier().evaluate(_workspace(tmp_path), contract)

    assert receipt.disposition == "infrastructure_invalid"
    assert receipt.kernel is None


class DiagnosticReplacingRunner:
    def __init__(self, replacement: str):
        self.delegate = SubprocessCommandRunner()
        self.replacement = replacement

    def run(self, *args, **kwargs):
        outcome = self.delegate.run(*args, **kwargs)
        if outcome.state is RunState.COMPLETED and outcome.returncode:
            return replace(outcome, stdout="", stderr=self.replacement)
        return outcome


class ArtifactOmittingRunner:
    def __init__(self):
        self.delegate = SubprocessCommandRunner()

    def run(self, args, **kwargs):
        outcome = self.delegate.run(args, **kwargs)
        if outcome.state is RunState.COMPLETED and outcome.returncode == 0 and "-o" in args:
            Path(args[args.index("-o") + 1]).unlink(missing_ok=True)
        return outcome


@requires_cpp_toolchain
def test_success_without_object_artifact_is_infrastructure_invalid(tmp_path):
    receipt = C1Verifier(ArtifactOmittingRunner()).evaluate(_workspace(tmp_path), _contract())

    assert receipt.disposition == "infrastructure_invalid"
    assert receipt.kernel is None


@requires_cpp_toolchain
def test_diagnostic_wording_does_not_change_kernel(tmp_path):
    header = GOOD_HEADER.replace("std::string encode", "int encode")
    workspace = _workspace(tmp_path, header)

    first = C1Verifier(DiagnosticReplacingRunner("compiler wording A")).evaluate(
        workspace, _contract()
    )
    second = C1Verifier(DiagnosticReplacingRunner("totally different wording B")).evaluate(
        workspace, _contract()
    )

    assert first.kernel == second.kernel == -1
    assert first.category_score == second.category_score == -1
    assert (
        first.verifier_results[0].failure_code
        == second.verifier_results[0].failure_code
        == "C1_METHOD_SIGNATURE_MISMATCH"
    )
    assert (
        first.verifier_results[0].evidence.digest_sha256
        != second.verifier_results[0].evidence.digest_sha256
    )


@requires_cpp_toolchain
def test_equivalent_evaluations_are_deterministic(tmp_path):
    workspace = _workspace(tmp_path, GOOD_HEADER.replace("std::string encode", "int encode"))

    first = C1Verifier().evaluate(workspace, _contract())
    second = C1Verifier().evaluate(workspace, _contract())

    assert first.to_json() == second.to_json()


@requires_cpp_toolchain
def test_duplicate_passing_probe_does_not_change_reward(tmp_path):
    base = _contract()
    duplicate = replace(base.compile_probes[-1], probe_id="encode-signature-duplicate")
    extended = replace(base, compile_probes=base.compile_probes + (duplicate,))
    workspace = _workspace(tmp_path)

    assert C1Verifier().evaluate(workspace, base).category_score == 1
    assert C1Verifier().evaluate(workspace, extended).category_score == 1


@requires_cpp_toolchain
def test_category_score_is_always_equal_to_the_single_kernel(tmp_path):
    passing = C1Verifier().evaluate(_workspace(tmp_path / "pass"), _contract())
    failing = C1Verifier().evaluate(
        _workspace(tmp_path / "fail", GOOD_HEADER.replace("std::string encode", "int encode")),
        _contract(),
    )

    assert {passing.kernel, failing.kernel} == {-1, 1}
    assert passing.category_score == passing.kernel
    assert failing.category_score == failing.kernel
    assert 0 not in {passing.kernel, failing.kernel}


@requires_cpp_toolchain
def test_receipt_is_stable_and_json_serializable(tmp_path):
    receipt = C1Verifier().evaluate(_workspace(tmp_path), _contract())
    doc = receipt.to_dict()

    assert doc["schema_version"] == "w8-c1-receipt-v1"
    assert doc["category"] == "C1"
    assert doc["contract_version"] == "specimen-c1-v1"
    assert doc["kernels"] == [1]
    assert '"category":"C1"' in receipt.to_json()


def test_relative_compiler_or_symbol_tool_is_contract_invalid(tmp_path):
    base = _contract()
    relative_compiler = replace(base, compiler=replace(base.compiler, compiler="g++"))
    relative_symbol = replace(base, compiler=replace(base.compiler, symbol_inspector="nm"))

    assert C1Verifier().evaluate(tmp_path, relative_compiler).disposition == "contract_invalid"
    assert C1Verifier().evaluate(tmp_path, relative_symbol).disposition == "contract_invalid"


def test_pinned_tool_identity_mismatch_is_infrastructure_invalid(tmp_path):
    base = _contract()
    mismatched = replace(
        base,
        compiler=replace(base.compiler, identity_sha256="0" * 64),
    )

    receipt = C1Verifier().evaluate(_workspace(tmp_path), mismatched)
    assert receipt.disposition == "infrastructure_invalid"
    assert receipt.kernel is None


def test_receipt_rejects_duplicate_or_inconsistent_results(tmp_path):
    receipt = C1Verifier().evaluate(
        tmp_path,
        _contract(),
        input_disposition=InputDisposition.NOT_EVALUATED,
    )
    with pytest.raises(ValueError, match="exactly one"):
        replace(receipt, verifier_results=receipt.verifier_results * 2)
    with pytest.raises(ValueError, match="cannot contain reward"):
        replace(receipt, category_score=1)


def test_compiler_environment_does_not_inherit_host_state(monkeypatch):
    monkeypatch.setenv("CPATH", "/candidate-controlled")
    monkeypatch.setenv("W8_SECRET_SENTINEL", "must-not-leak")

    environment = _compiler_env()

    assert "CPATH" not in environment
    assert "W8_SECRET_SENTINEL" not in environment
