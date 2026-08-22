from __future__ import annotations

import dataclasses
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from glm47_posttraining.verifiers.cpp_c4 import (
    C4Contract,
    C4Receipt,
    CommandOutcome,
    CompilerProfile,
    ExecutionInfrastructureError,
    InputDisposition,
    SandboxExecutionError,
    StageEvidence,
    SubprocessRunner,
    VerifierResult,
    evaluate_cpp_c4,
    fingerprint_compiler,
)

HEADER = """\
#pragma once
#include <string>

namespace crypto_square {
class cipher {
public:
    explicit cipher(const std::string& text);
    std::string normalized_cipher_text() const;
    std::string plaintext_segments() const;
    std::string ciphertext() const;
};
}
"""

IMPLEMENTATION = """\
#include "crypto_square.h"
namespace crypto_square {
cipher::cipher(const std::string& text) { (void)text; }
std::string cipher::normalized_cipher_text() const { return "normalized"; }
std::string cipher::plaintext_segments() const { return "plain"; }
std::string cipher::ciphertext() const { return "cipher"; }
}
"""

DECLARATION_PROBE = """\
#include "crypto_square.h"
#include <string>
#include <type_traits>
using crypto_square::cipher;
static_assert(std::is_constructible_v<cipher, const std::string&>);
static_assert(std::is_same_v<decltype(&cipher::normalized_cipher_text),
                             std::string (cipher::*)() const>);
static_assert(std::is_same_v<decltype(&cipher::plaintext_segments),
                             std::string (cipher::*)() const>);
static_assert(std::is_same_v<decltype(&cipher::ciphertext),
                             std::string (cipher::*)() const>);
"""

LINK_HARNESS = """\
#include "crypto_square.h"
#include <string>
int main() {
    crypto_square::cipher value(std::string("abc"));
    auto (crypto_square::cipher::*a)() const = &crypto_square::cipher::normalized_cipher_text;
    auto (crypto_square::cipher::*b)() const = &crypto_square::cipher::plaintext_segments;
    auto (crypto_square::cipher::*c)() const = &crypto_square::cipher::ciphertext;
    return (a == nullptr) + (b == nullptr) + (c == nullptr) + sizeof(value);
}
"""


@pytest.fixture(scope="session")
def compiler_profile() -> CompilerProfile:
    compiler = shutil.which("g++")
    if compiler is None:
        pytest.skip("focused semantic C4 tests require g++")
    executable = str(Path(compiler).resolve())
    return CompilerProfile(
        executable=executable,
        identity_sha256=fingerprint_compiler(executable),
    )


def make_contract(
    compiler_profile: CompilerProfile,
    **changes: object,
) -> C4Contract:
    contract = C4Contract(
        contract_version="crypto-square-c4-v1",
        header="crypto_square.h",
        implementation_units=("crypto_square.cpp",),
        definition_owners=("crypto_square::cipher",),
        declaration_probe_source=DECLARATION_PROBE,
        exhaustive_link_harness_source=LINK_HARNESS,
        compiler=compiler_profile,
    )
    return dataclasses.replace(contract, **changes)


def candidate(
    tmp_path: Path, *, header: str = HEADER, implementation: str = IMPLEMENTATION
) -> Path:
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "crypto_square.h").write_text(header, encoding="utf-8")
    (root / "crypto_square.cpp").write_text(implementation, encoding="utf-8")
    return root


def evaluate(root: object, contract: C4Contract, *, runner=None, version=None):
    return evaluate_cpp_c4(
        root,
        contract,
        expected_contract_version=version or contract.contract_version,
        runner=runner,
    )


def assert_scored(receipt, kernel: int, phase: str | None = None) -> None:
    assert receipt.disposition == "scored"
    assert receipt.kernel == kernel
    assert receipt.category_score == kernel
    assert receipt.verifier_result.kernel in {-1, 1}
    assert receipt.verifier_result.phase == phase
    assert len(receipt.to_dict()["verifier_results"]) == 1
    assert all(not item.reward_bearing for item in receipt.attribution_evidence)


def assert_unscored(receipt, disposition: str) -> None:
    assert receipt.disposition == disposition
    assert receipt.kernel is None
    assert receipt.category_score is None
    assert receipt.verifier_result.kernel is None


def test_valid_contract_scores_positive(tmp_path: Path, compiler_profile: CompilerProfile) -> None:
    receipt = evaluate(candidate(tmp_path), make_contract(compiler_profile))

    assert_scored(receipt, 1)
    assert receipt.verifier_result.status == "passed"
    assert receipt.to_dict()["kernels"] == [1]


def test_receipt_and_stage_invariants_reject_reward_inconsistency() -> None:
    with pytest.raises(ValueError, match="never be reward-bearing"):
        StageEvidence(stage="binding", status="passed", reward_bearing=True)
    with pytest.raises(ValueError, match="unexpected C4 verifier"):
        VerifierResult(verifier="wrong", status="passed", kernel=1)
    with pytest.raises(ValueError, match="non-scored"):
        C4Receipt(
            disposition="not_evaluated",
            contract_version="v1",
            verifier_result=VerifierResult(
                verifier="implementation-contract-linkage",
                status="passed",
                kernel=1,
            ),
        )


@pytest.mark.parametrize(
    ("replacement", "expected_fragment"),
    [
        (
            "cipher::cipher(std::string text) { (void)text; }",
            "cipher::cipher(std::stringtext)",
        ),
        (
            "int cipher::normalized_cipher_text() const { return 1; }",
            "cipher::normalized_cipher_text",
        ),
        (
            "std::string cipher::normalized_cipher_text() { return {}; }",
            "cipher::normalized_cipher_text",
        ),
    ],
)
def test_declaration_definition_mismatches_are_c4(
    tmp_path: Path,
    compiler_profile: CompilerProfile,
    replacement: str,
    expected_fragment: str,
) -> None:
    original = (
        "cipher::cipher(const std::string& text) { (void)text; }"
        if replacement.startswith("cipher::cipher")
        else 'std::string cipher::normalized_cipher_text() const { return "normalized"; }'
    )
    implementation = IMPLEMENTATION.replace(original, replacement)

    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_scored(receipt, -1, "definition-binding")
    symbols = "\n".join(item.diagnostic or "" for item in receipt.attribution_evidence)
    assert expected_fragment in symbols.replace(" ", "")


@pytest.mark.parametrize(
    "implementation",
    [
        IMPLEMENTATION.replace("namespace crypto_square", "namespace wrong_namespace", 1),
        IMPLEMENTATION.replace("cipher::cipher", "wrong_class::wrong_class", 1),
    ],
)
def test_wrong_definition_namespace_or_class_is_c4_link_failure(
    tmp_path: Path, compiler_profile: CompilerProfile, implementation: str
) -> None:
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_scored(receipt, -1, "link")


@pytest.mark.parametrize(
    "definition",
    [
        "cipher::cipher(const std::string& text) { (void)text; }",
        'std::string cipher::normalized_cipher_text() const { return "normalized"; }',
        'std::string cipher::plaintext_segments() const { return "plain"; }',
        'std::string cipher::ciphertext() const { return "cipher"; }',
    ],
)
def test_each_undefined_required_symbol_is_c4(
    tmp_path: Path, compiler_profile: CompilerProfile, definition: str
) -> None:
    receipt = evaluate(
        candidate(tmp_path, implementation=IMPLEMENTATION.replace(definition, "")),
        make_contract(compiler_profile),
    )

    assert_scored(receipt, -1, "link")
    assert receipt.verifier_result.failure_code == "C4_LINK_COMPLETENESS_FAILURE"


def test_defaulted_deleted_symbol_that_cannot_link_is_c4(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    header = HEADER.replace(
        "std::string ciphertext() const;", "std::string ciphertext() const = delete;"
    )
    implementation = IMPLEMENTATION.replace(
        'std::string cipher::ciphertext() const { return "cipher"; }', ""
    )
    receipt = evaluate(
        candidate(tmp_path, header=header, implementation=implementation),
        make_contract(compiler_profile),
    )

    # The trusted public-contract probe cannot legally reference a deleted API.
    assert_unscored(receipt, "not_evaluated")


@pytest.mark.parametrize(
    "broken_body",
    [
        "this is ???;",
        "unknown_implementation_name();",
        'int value = std::string("bad"); (void)value;',
        "return missing_overload(1, 2, 3);",
        "const std::string value; value.clear();",
        "return algorithmically_wrong;",
    ],
)
def test_body_local_c2_or_c3_defects_do_not_fail_c4(
    tmp_path: Path, compiler_profile: CompilerProfile, broken_body: str
) -> None:
    implementation = IMPLEMENTATION.replace('return "normalized";', broken_body, 1)
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_scored(receipt, 1)


def test_implementation_only_missing_include_does_not_fail_c4(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    implementation = '#include "candidate_only_missing.h"\n' + IMPLEMENTATION
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_scored(receipt, 1)


def test_constructor_initializer_body_is_neutralized(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    header = HEADER.replace("};", "private:\n    int value_;\n};")
    implementation = IMPLEMENTATION.replace(
        "cipher::cipher(const std::string& text) { (void)text; }",
        "cipher::cipher(const std::string& text) : value_(unknown_name) { (void)text; }",
    )
    receipt = evaluate(
        candidate(tmp_path, header=header, implementation=implementation),
        make_contract(compiler_profile),
    )

    assert_scored(receipt, 1)


def test_wrong_public_api_blocks_c4_without_negative_kernel(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    header = HEADER.replace("ciphertext", "cipher_text")
    implementation = IMPLEMENTATION.replace("ciphertext", "cipher_text")
    receipt = evaluate(
        candidate(tmp_path, header=header, implementation=implementation),
        make_contract(compiler_profile),
    )

    assert_unscored(receipt, "not_evaluated")
    assert receipt.verifier_result.failure_code == "C4_BLOCKED_BY_DECLARATION_SURFACE"


def test_non_self_contained_header_blocks_c4(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    receipt = evaluate(
        candidate(tmp_path, header=HEADER.replace("#include <string>\n", "")),
        make_contract(compiler_profile),
    )

    assert_unscored(receipt, "not_evaluated")


def test_top_level_parse_ambiguity_fails_closed(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    implementation = "int = ;\n" + IMPLEMENTATION
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_unscored(receipt, "not_evaluated")
    assert receipt.verifier_result.failure_code == "C4_ATTRIBUTION_AMBIGUOUS"


def test_definition_generating_preprocessor_construct_fails_closed(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    implementation = "#define DEFINE_CONSTRUCTOR cipher::cipher\n" + IMPLEMENTATION
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_unscored(receipt, "not_evaluated")
    assert receipt.verifier_result.failure_code == "C4_ATTRIBUTION_AMBIGUOUS"


def test_missing_header_is_c1_blocked_not_c4_failure(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    root = candidate(tmp_path)
    (root / "crypto_square.h").unlink()

    assert_unscored(evaluate(root, make_contract(compiler_profile)), "not_evaluated")


def test_missing_implementation_is_candidate_format_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    root = candidate(tmp_path)
    (root / "crypto_square.cpp").unlink()

    assert_unscored(evaluate(root, make_contract(compiler_profile)), "candidate_format_invalid")


def test_upstream_workspace_cause_short_circuits_filename_inference(
    compiler_profile: CompilerProfile,
) -> None:
    receipt = evaluate_cpp_c4(
        None,
        make_contract(compiler_profile),
        expected_contract_version="crypto-square-c4-v1",
        input_disposition=InputDisposition.WORKSPACE_INVALID,
        input_failure_code="WORKSPACE_CORRUPTED_UPSTREAM",
    )

    assert_unscored(receipt, "workspace_invalid")
    assert receipt.verifier_result.failure_code == "WORKSPACE_CORRUPTED_UPSTREAM"


def test_malformed_candidate_response_is_unscored(compiler_profile: CompilerProfile) -> None:
    assert_unscored(evaluate(None, make_contract(compiler_profile)), "candidate_format_invalid")


def test_corrupt_or_symlink_workspace_is_unscored(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    root = candidate(tmp_path)
    workspace_link = tmp_path / "workspace-link"
    workspace_link.symlink_to(root, target_is_directory=True)

    assert_unscored(evaluate(workspace_link, make_contract(compiler_profile)), "workspace_invalid")


def test_contract_version_mismatch_is_unscored(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    receipt = evaluate(
        candidate(tmp_path), make_contract(compiler_profile), version="different-contract"
    )

    assert_unscored(receipt, "contract_invalid")


def test_unpinned_compiler_contract_is_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    profile = dataclasses.replace(compiler_profile, identity_sha256="not-a-digest")

    assert_unscored(
        evaluate(candidate(tmp_path), make_contract(profile)),
        "contract_invalid",
    )


def test_pinned_compiler_identity_mismatch_is_infrastructure_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    profile = dataclasses.replace(compiler_profile, identity_sha256="0" * 64)
    receipt = evaluate(candidate(tmp_path), make_contract(profile))

    assert_unscored(receipt, "infrastructure_invalid")


def test_malformed_contract_object_is_unscored(tmp_path: Path) -> None:
    receipt = evaluate_cpp_c4(
        candidate(tmp_path),
        None,  # type: ignore[arg-type]
        expected_contract_version="crypto-square-c4-v1",
    )

    assert_unscored(receipt, "contract_invalid")


def test_intermediate_symlink_escape_is_workspace_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "crypto_square.h").write_text(HEADER, encoding="utf-8")
    (outside / "crypto_square.cpp").write_text(IMPLEMENTATION, encoding="utf-8")
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "escaped").symlink_to(outside, target_is_directory=True)
    contract = make_contract(
        compiler_profile,
        header="escaped/crypto_square.h",
        implementation_units=("escaped/crypto_square.cpp",),
    )

    assert_unscored(evaluate(root, contract), "not_evaluated")


def test_compiler_unavailable_is_infrastructure_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    profile = dataclasses.replace(compiler_profile, executable="/definitely/missing/g++")
    receipt = evaluate(candidate(tmp_path), make_contract(profile))

    assert_unscored(receipt, "infrastructure_invalid")


class FailingRunner:
    def __init__(self, exc: ExecutionInfrastructureError) -> None:
        self.exc = exc

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float,
    ) -> CommandOutcome:
        raise self.exc


@pytest.mark.parametrize(
    "exc",
    [
        SandboxExecutionError("sandbox denied execution"),
        ExecutionInfrastructureError("resource timeout"),
    ],
)
def test_sandbox_and_resource_failures_are_unscored(
    tmp_path: Path, compiler_profile: CompilerProfile, exc: ExecutionInfrastructureError
) -> None:
    receipt = evaluate(
        candidate(tmp_path), make_contract(compiler_profile), runner=FailingRunner(exc)
    )

    assert_unscored(receipt, "infrastructure_invalid")


class DiagnosticRewriteRunner:
    def __init__(self, replacement: str) -> None:
        self.delegate = SubprocessRunner()
        self.replacement = replacement

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float,
    ) -> CommandOutcome:
        outcome = self.delegate.run(args, cwd=cwd, env=env, timeout=timeout)
        if outcome.returncode:
            return CommandOutcome(outcome.returncode, "", self.replacement)
        return outcome


class ArtifactOmittingRunner:
    def __init__(self) -> None:
        self.delegate = SubprocessRunner()

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float,
    ) -> CommandOutcome:
        outcome = self.delegate.run(args, cwd=cwd, env=env, timeout=timeout)
        if outcome.returncode == 0 and "-o" in args:
            Path(args[args.index("-o") + 1]).unlink(missing_ok=True)
        return outcome


def test_success_without_expected_artifact_is_infrastructure_invalid(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    receipt = evaluate(
        candidate(tmp_path),
        make_contract(compiler_profile),
        runner=ArtifactOmittingRunner(),
    )

    assert_unscored(receipt, "infrastructure_invalid")


def test_diagnostic_wording_does_not_change_kernel(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    implementation = IMPLEMENTATION.replace(
        "std::string cipher::normalized_cipher_text() const",
        "int cipher::normalized_cipher_text() const",
    )
    root = candidate(tmp_path, implementation=implementation)
    contract = make_contract(compiler_profile)

    first = evaluate(root, contract, runner=DiagnosticRewriteRunner("localized diagnostic A"))
    second = evaluate(root, contract, runner=DiagnosticRewriteRunner("different formatting B"))

    assert_scored(first, -1, "definition-binding")
    assert_scored(second, -1, "definition-binding")


def test_equivalent_evaluations_have_deterministic_receipts(
    tmp_path: Path, compiler_profile: CompilerProfile
) -> None:
    root = candidate(tmp_path)
    contract = make_contract(compiler_profile)

    assert evaluate(root, contract).to_dict() == evaluate(root, contract).to_dict()


@pytest.mark.parametrize(
    ("implementation", "expected_kernel"),
    [
        (IMPLEMENTATION, 1),
        (IMPLEMENTATION.replace('return "cipher";', 'return "wrong";'), 1),
        (IMPLEMENTATION.replace("cipher::cipher", "cipher::missing", 1), -1),
    ],
)
def test_only_binary_kernels_and_score_equals_kernel(
    tmp_path: Path,
    compiler_profile: CompilerProfile,
    implementation: str,
    expected_kernel: int,
) -> None:
    receipt = evaluate(
        candidate(tmp_path, implementation=implementation), make_contract(compiler_profile)
    )

    assert_scored(receipt, expected_kernel, "definition-binding" if expected_kernel == -1 else None)
    assert receipt.category_score == receipt.kernel
