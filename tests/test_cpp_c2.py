from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from glm47_posttraining.verifiers.cpp_c2 import (
    C2Candidate,
    C2Contract,
    C2ImplementationTranslationVerifier,
    C2Receipt,
    CommandOutcome,
    CompilerProfile,
    SubprocessCommandRunner,
    _compiler_environment,
)

CONTRACT_VERSION = "crypto-square-c2-independent-v1"
HEADER = """\
#pragma once
#include <string>

namespace crypto_square {
class cipher {
public:
    explicit cipher(const std::string& text);
    std::string normalized_cipher_text() const;

private:
    std::string text_;
};
}
"""
PROBE = """\
#include "crypto_square.h"
#include <string>
#include <type_traits>

using cipher_type = crypto_square::cipher;
using method_type = std::string (cipher_type::*)() const;
static_assert(std::is_constructible_v<cipher_type, const std::string&>);
static_assert(std::is_same_v<
    decltype(static_cast<method_type>(&cipher_type::normalized_cipher_text)),
    method_type>);
"""
VALID_IMPLEMENTATION = """\
#include "crypto_square.h"

namespace crypto_square {
cipher::cipher(const std::string& text) : text_(text) {}

std::string cipher::normalized_cipher_text() const {
    return text_;
}
}
"""


@pytest.fixture(scope="session")
def compiler_profile() -> CompilerProfile:
    executable = shutil.which("g++")
    if executable is None:
        pytest.skip("g++ is required for real C2 translation tests")
    executable = str(Path(executable).resolve())
    completed = subprocess.run(
        [executable, "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    identity = next(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return CompilerProfile(
        profile_id="gcc-c++17-strict-test-v1",
        executable=executable,
        expected_identity=identity,
        arguments=(
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-fdiagnostics-color=never",
        ),
        timeout_seconds=10,
    )


@pytest.fixture
def contract(compiler_profile: CompilerProfile) -> C2Contract:
    return C2Contract(
        contract_version=CONTRACT_VERSION,
        compiler=compiler_profile,
        required_files=("crypto_square.h", "crypto_square.cpp"),
        implementation_files=("crypto_square.cpp",),
        public_declaration_probe=PROBE,
    )


@pytest.fixture
def verifier(tmp_path: Path) -> C2ImplementationTranslationVerifier:
    return C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        scratch_root=tmp_path,
    )


def candidate(
    implementation: str = VALID_IMPLEMENTATION,
    *,
    header: str = HEADER,
    extra_files: Mapping[str, str] | None = None,
) -> C2Candidate:
    files = {
        "crypto_square.h": header,
        "crypto_square.cpp": implementation,
        **dict(extra_files or {}),
    }
    return C2Candidate(contract_version=CONTRACT_VERSION, files=files)


def assert_c2_pass(receipt: C2Receipt) -> None:
    assert receipt.disposition == "scored"
    assert receipt.status == "passed"
    assert receipt.kernel == 1
    assert receipt.category_score == 1
    assert receipt.verifier == "implementation-translation"
    assert receipt.compile_phase["linked"] is False
    assert receipt.compile_phase["executed"] is False


def assert_c2_failure(receipt: C2Receipt) -> None:
    assert receipt.disposition == "scored"
    assert receipt.status == "failed"
    assert receipt.kernel == -1
    assert receipt.category_score == -1
    assert receipt.failure_code == "C2_TRANSLATION_FAILURE"
    assert receipt.attribution["declaration_surface"]["status"] == "ruled_out"
    assert receipt.attribution["definition_binding"]["status"] == "ruled_out"
    assert receipt.attribution["declaration_surface"]["reward_bearing"] is False
    assert receipt.attribution["definition_binding"]["reward_bearing"] is False


def assert_unscored(receipt: C2Receipt, disposition: str) -> None:
    assert receipt.disposition == disposition
    assert receipt.kernel is None
    assert receipt.category_score is None


def test_valid_implementation_scores_positive(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    receipt = verifier.evaluate_candidate(candidate(), contract)

    assert_c2_pass(receipt)
    assert receipt.to_dict()["kernels"] == [1]
    assert receipt.to_dict()["verifier_results"][0]["verifier"] == ("implementation-translation")
    assert receipt.attribution["declaration_surface"]["status"] == ("not_required_for_compile_pass")
    assert receipt.attribution["definition_binding"]["status"] == ("not_required_for_compile_pass")


def test_receipt_rejects_reward_bearing_attribution_gate(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    receipt = verifier.evaluate_candidate(candidate(), contract)
    attribution = dict(receipt.attribution)
    attribution["declaration_surface"] = {
        **attribution["declaration_surface"],
        "reward_bearing": True,
    }

    with pytest.raises(ValueError, match="non-reward-bearing"):
        replace(receipt, attribution=attribution)


@pytest.mark.parametrize(
    ("case", "body"),
    [
        ("syntax", "int value = ;\n    return text_;"),
        ("unknown-name", "return missing_value;"),
        ("unknown-type", "MissingType value;\n    return text_;"),
        ("invalid-expression", "return text_ * 2;"),
        ("invalid-conversion", "int value = text_;\n    return std::to_string(value);"),
        (
            "overload-resolution",
            "auto pick = [](int) { return 1; };\n    (void)pick(text_);\n    return text_;",
        ),
        (
            "template-instantiation",
            "struct no_add {};\n"
            "    auto twice = [](auto value) { return value + value; };\n"
            "    (void)twice(no_add{});\n"
            "    return text_;",
        ),
        (
            "cxx20-under-cxx17",
            "auto identity = []<typename T>(T value) { return value; };\n"
            "    return identity(text_);",
        ),
        ("warning-as-error", "int unused = 1;\n    return text_;"),
        ("const-misuse", "text_.clear();\n    return text_;"),
    ],
)
def test_genuine_body_owned_failures_score_negative(
    case: str,
    body: str,
    verifier: C2ImplementationTranslationVerifier,
    contract: C2Contract,
) -> None:
    implementation = f"""\
#include "crypto_square.h"

namespace crypto_square {{
cipher::cipher(const std::string& text) : text_(text) {{}}
std::string cipher::normalized_cipher_text() const {{
    {body}
}}
}}
"""

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_c2_failure(receipt), case


def test_missing_implementation_only_dependency_scores_negative(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace(
        '#include "crypto_square.h"',
        '#include "crypto_square.h"\n#include "missing_implementation_only.hpp"',
    )

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_c2_failure(receipt)
    files = receipt.attribution["definition_binding"]["files"]
    assert files[0]["removed_missing_quoted_includes"] == ["missing_implementation_only.hpp"]


def test_constructor_initializer_body_error_is_c2_not_c4(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace(
        ": text_(text)",
        ": text_(missing_implementation_name)",
    )

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_c2_failure(receipt)


def test_top_level_initializer_attribution_fails_closed(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace(
        "namespace crypto_square {",
        "namespace crypto_square {\nint local_state = missing_implementation_name;",
    )

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_unscored(receipt, "not_evaluated")
    assert receipt.attribution["definition_binding"]["status"] == "not_ruled_out"


def test_missing_angle_dependency_attribution_fails_closed(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace(
        '#include "crypto_square.h"',
        '#include "crypto_square.h"\n#include <w8_c2_definitely_missing_dependency.hpp>',
    )

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_unscored(receipt, "not_evaluated")
    assert receipt.attribution["definition_binding"]["status"] == "not_ruled_out"


def test_wrong_public_api_that_still_translates_scores_positive(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    wrong_header = HEADER.replace("normalized_cipher_text", "wrong_normalized_cipher_text")
    wrong_implementation = VALID_IMPLEMENTATION.replace(
        "normalized_cipher_text", "wrong_normalized_cipher_text"
    )

    receipt = verifier.evaluate_candidate(
        candidate(wrong_implementation, header=wrong_header), contract
    )

    assert_c2_pass(receipt)


def test_c1_defect_that_prevents_attribution_is_not_evaluated(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    wrong_header = HEADER.replace("namespace crypto_square", "namespace wrong_square")
    implementation = """\
#include "crypto_square.h"
namespace crypto_square {
std::string cipher::normalized_cipher_text() const { return missing_name; }
}
"""

    receipt = verifier.evaluate_candidate(candidate(implementation, header=wrong_header), contract)

    assert_unscored(receipt, "not_evaluated")
    assert receipt.attribution["declaration_surface"]["status"] == "not_ruled_out"


@pytest.mark.parametrize(
    "implementation",
    [
        """\
#include "crypto_square.h"
namespace crypto_square {
std::string cipher::normalized_cipher_text() { return {}; }
}
""",
        """\
#include "crypto_square.h"
namespace wrong_square {
std::string cipher::normalized_cipher_text() const { return {}; }
}
""",
    ],
    ids=["declaration-definition-mismatch", "wrong-definition-namespace"],
)
def test_c4_binding_failures_are_not_scored_as_c2(
    implementation: str,
    verifier: C2ImplementationTranslationVerifier,
    contract: C2Contract,
) -> None:
    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_unscored(receipt, "not_evaluated")
    assert receipt.attribution["declaration_surface"]["status"] == "ruled_out"
    assert receipt.attribution["definition_binding"]["status"] == "not_ruled_out"
    assert receipt.failure_code == "C4_OWNERSHIP_NOT_RULED_OUT"


@pytest.mark.parametrize(
    "implementation",
    [
        '#include "crypto_square.h"\n',
        """\
#include "crypto_square.h"
namespace crypto_square {
std::string cipher::normalized_cipher_text() const { return {}; }
}
""",
    ],
    ids=["undefined-constructor-and-method", "undefined-constructor"],
)
def test_undefined_symbols_or_later_link_failure_still_score_positive(
    implementation: str,
    verifier: C2ImplementationTranslationVerifier,
    contract: C2Contract,
) -> None:
    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_c2_pass(receipt)


def test_algorithmically_wrong_but_translatable_scores_positive(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace("return text_;", 'return "wrong";')

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_c2_pass(receipt)


class AlwaysInfrastructureRunner:
    def __init__(self, failure: str) -> None:
        self.failure = failure

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        del command, cwd, env, timeout_seconds
        return CommandOutcome(
            returncode=None,
            infrastructure_failure=self.failure,  # type: ignore[arg-type]
            infrastructure_detail=f"injected {self.failure}",
        )


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        ("unavailable", "COMPILER_UNAVAILABLE"),
        ("sandbox", "SANDBOX_FAILURE"),
        ("timeout", "COMPILER_TIMEOUT"),
    ],
)
def test_infrastructure_failures_never_score(
    failure: str,
    code: str,
    tmp_path: Path,
    contract: C2Contract,
) -> None:
    verifier = C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        runner=AlwaysInfrastructureRunner(failure),
        scratch_root=tmp_path,
    )

    receipt = verifier.evaluate_candidate(candidate(), contract)

    assert_unscored(receipt, "infrastructure_invalid")
    assert receipt.failure_code == code


class CompileTimeoutRunner:
    def __init__(self) -> None:
        self.delegate = SubprocessCommandRunner()
        self.calls = 0

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        self.calls += 1
        if self.calls > 1:
            return CommandOutcome(
                returncode=None,
                infrastructure_failure="timeout",
                infrastructure_detail="injected compile timeout",
            )
        return self.delegate.run(command, cwd=cwd, env=env, timeout_seconds=timeout_seconds)


def test_compile_phase_timeout_is_unscored(tmp_path: Path, contract: C2Contract) -> None:
    verifier = C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        runner=CompileTimeoutRunner(),
        scratch_root=tmp_path,
    )

    receipt = verifier.evaluate_candidate(candidate(), contract)

    assert_unscored(receipt, "infrastructure_invalid")
    assert receipt.failure_code == "COMPILER_TIMEOUT"


class SuccessfulWithoutObjectRunner:
    def __init__(self) -> None:
        self.delegate = SubprocessCommandRunner()
        self.calls = 0

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        self.calls += 1
        if self.calls == 1:
            return self.delegate.run(command, cwd=cwd, env=env, timeout_seconds=timeout_seconds)
        return CommandOutcome(returncode=0)


def test_compiler_success_without_object_is_infrastructure_invalid(
    tmp_path: Path, contract: C2Contract
) -> None:
    verifier = C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        runner=SuccessfulWithoutObjectRunner(),
        scratch_root=tmp_path,
    )

    receipt = verifier.evaluate_candidate(candidate(), contract)

    assert_unscored(receipt, "infrastructure_invalid")
    assert receipt.failure_code == "COMPILER_OUTPUT_MISSING"


class MissingReturnCodeRunner:
    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        del command, cwd, env, timeout_seconds
        return CommandOutcome(returncode=None)


def test_malformed_runner_outcome_is_infrastructure_invalid(
    tmp_path: Path, contract: C2Contract
) -> None:
    verifier = C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        runner=MissingReturnCodeRunner(),
        scratch_root=tmp_path,
    )

    receipt = verifier.evaluate_candidate(candidate(), contract)

    assert_unscored(receipt, "infrastructure_invalid")
    assert receipt.failure_code == "COMMAND_OUTCOME_INVALID"


@pytest.mark.parametrize(
    "malformed",
    [
        None,
        "not-an-object",
        {},
        {"contract_version": CONTRACT_VERSION, "files": []},
        {
            "contract_version": CONTRACT_VERSION,
            "files": {"../escape.cpp": ""},
        },
        {
            "contract_version": CONTRACT_VERSION,
            "files": {"nested//alias.cpp": ""},
        },
    ],
)
def test_malformed_candidate_response_is_unscored(
    malformed: object,
    verifier: C2ImplementationTranslationVerifier,
    contract: C2Contract,
) -> None:
    receipt = verifier.evaluate_candidate(malformed, contract)

    assert_unscored(receipt, "candidate_format_invalid")


def test_candidate_omission_and_workspace_corruption_remain_distinct(
    tmp_path: Path,
    verifier: C2ImplementationTranslationVerifier,
    contract: C2Contract,
) -> None:
    omitted = verifier.evaluate_candidate(
        {
            "contract_version": CONTRACT_VERSION,
            "files": {"crypto_square.cpp": VALID_IMPLEMENTATION},
        },
        contract,
    )
    workspace = tmp_path / "corrupt-workspace"
    workspace.mkdir()
    (workspace / "crypto_square.cpp").write_text(VALID_IMPLEMENTATION)
    corrupted = verifier.evaluate_workspace(
        workspace,
        contract,
        candidate_contract_version=CONTRACT_VERSION,
    )

    assert_unscored(omitted, "candidate_format_invalid")
    assert omitted.failure_code == "CANDIDATE_REQUIRED_FILE_OMITTED"
    assert_unscored(corrupted, "workspace_invalid")
    assert corrupted.failure_code == "WORKSPACE_INVALID"


def test_contract_version_mismatch_is_unscored(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    response = C2Candidate(contract_version="wrong-version", files=candidate().files)

    receipt = verifier.evaluate_candidate(response, contract)

    assert_unscored(receipt, "contract_invalid")
    assert receipt.failure_code == "CONTRACT_VERSION_MISMATCH"


def test_invalid_contract_is_unscored(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    invalid_contract = replace(contract, contract_version="unsupported-contract")

    receipt = verifier.evaluate_candidate(candidate(), invalid_contract)

    assert_unscored(receipt, "contract_invalid")
    assert receipt.failure_code == "CONTRACT_INVALID"


def test_noncanonical_contract_path_is_unscored(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    invalid_contract = replace(
        contract,
        required_files=("crypto_square.h", "nested//crypto_square.cpp"),
        implementation_files=("nested//crypto_square.cpp",),
    )

    receipt = verifier.evaluate_candidate(candidate(), invalid_contract)

    assert_unscored(receipt, "contract_invalid")
    assert receipt.failure_code == "CONTRACT_INVALID"


def test_extension_does_not_bypass_cpp_translation(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    text_contract = replace(
        contract,
        required_files=("crypto_square.h", "crypto_square.txt"),
        implementation_files=("crypto_square.txt",),
    )
    text_candidate = C2Candidate(
        contract_version=CONTRACT_VERSION,
        files={
            "crypto_square.h": HEADER,
            "crypto_square.txt": VALID_IMPLEMENTATION,
        },
    )

    receipt = verifier.evaluate_candidate(text_candidate, text_contract)

    assert_c2_pass(receipt)


def test_ambiguous_definition_transformation_fails_closed(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = """\
#include "crypto_square.h"
namespace crypto_square {
cipher::cipher(const std::string& text) try : text_(text) {
    int value = missing_name;
} catch (...) {}
std::string cipher::normalized_cipher_text() const { return text_; }
}
"""

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_unscored(receipt, "not_evaluated")
    assert receipt.attribution["definition_binding"]["status"] == "ambiguous"


class DiagnosticDecoratingRunner:
    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        self.delegate = SubprocessCommandRunner()

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        outcome = self.delegate.run(command, cwd=cwd, env=env, timeout_seconds=timeout_seconds)
        if outcome.returncode and outcome.infrastructure_failure is None:
            return replace(outcome, stderr=outcome.stderr + self.suffix)
        return outcome


class DeclarationArtifactOmittingRunner:
    def __init__(self) -> None:
        self.delegate = SubprocessCommandRunner()

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout_seconds: float,
    ) -> CommandOutcome:
        outcome = self.delegate.run(
            command,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
        )
        if (
            outcome.returncode == 0
            and any(str(part).endswith("declaration-gate.cpp") for part in command)
            and "-o" in command
        ):
            Path(command[command.index("-o") + 1]).unlink(missing_ok=True)
        return outcome


def test_missing_declaration_gate_artifact_is_infrastructure_invalid(
    tmp_path: Path, contract: C2Contract
) -> None:
    verifier = C2ImplementationTranslationVerifier(
        expected_contract_version=CONTRACT_VERSION,
        runner=DeclarationArtifactOmittingRunner(),
        scratch_root=tmp_path,
    )
    implementation = VALID_IMPLEMENTATION.replace("return text_;", "return missing_name;")

    receipt = verifier.evaluate_candidate(candidate(implementation), contract)

    assert_unscored(receipt, "infrastructure_invalid")


def test_diagnostic_wording_does_not_change_kernel(tmp_path: Path, contract: C2Contract) -> None:
    implementation = VALID_IMPLEMENTATION.replace("return text_;", "return missing_name;")
    receipts = []
    for suffix in ("\nwording A", "\ncompletely different wording B"):
        verifier = C2ImplementationTranslationVerifier(
            expected_contract_version=CONTRACT_VERSION,
            runner=DiagnosticDecoratingRunner(suffix),
            scratch_root=tmp_path,
        )
        receipts.append(verifier.evaluate_candidate(candidate(implementation), contract))

    assert [receipt.kernel for receipt in receipts] == [-1, -1]
    assert [receipt.category_score for receipt in receipts] == [-1, -1]
    assert receipts[0].diagnostic != receipts[1].diagnostic


def test_repeated_equivalent_evaluations_are_deterministic(
    verifier: C2ImplementationTranslationVerifier, contract: C2Contract
) -> None:
    implementation = VALID_IMPLEMENTATION.replace("return text_;", "return missing_name;")

    first = verifier.evaluate_candidate(candidate(implementation), contract).to_dict()
    second = verifier.evaluate_candidate(candidate(implementation), contract).to_dict()

    assert first == second


def test_receipt_rejects_zero_or_mismatched_category_score() -> None:
    base = {
        "schema_version": "c2-receipt-v1",
        "category": "C2",
        "disposition": "scored",
        "verifier": "implementation-translation",
        "status": "failed",
        "attribution": {},
        "compiler_profile": {},
        "compile_phase": {},
        "failure_code": "C2_TRANSLATION_FAILURE",
        "diagnostic": "",
        "contract_version": CONTRACT_VERSION,
    }
    with pytest.raises(ValueError):
        C2Receipt(kernel=0, category_score=0, **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        C2Receipt(kernel=-1, category_score=1, **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        C2Receipt(kernel=True, category_score=True, **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        C2Receipt(kernel=-1, category_score=-1, **{**base, "category": "C3"})
    with pytest.raises(ValueError):
        C2Receipt(
            kernel=-1,
            category_score=-1,
            **{**base, "verifier": "not-the-c2-verifier"},
        )


def test_receipt_rejects_reward_on_non_scored_disposition() -> None:
    with pytest.raises(ValueError):
        C2Receipt(
            schema_version="c2-receipt-v1",
            category="C2",
            disposition="infrastructure_invalid",
            verifier="implementation-translation",
            status="invalid",
            kernel=-1,
            category_score=-1,
            attribution={},
            compiler_profile={},
            compile_phase={},
            failure_code="COMPILER_UNAVAILABLE",
            diagnostic="",
            contract_version=CONTRACT_VERSION,
        )


def test_receipt_rejects_unknown_disposition() -> None:
    with pytest.raises(ValueError):
        C2Receipt(
            schema_version="c2-receipt-v1",
            category="C2",
            disposition="unknown",  # type: ignore[arg-type]
            verifier="implementation-translation",
            status="invalid",
            kernel=None,
            category_score=None,
            attribution={},
            compiler_profile={},
            compile_phase={},
            failure_code="UNKNOWN",
            diagnostic="",
            contract_version=CONTRACT_VERSION,
        )


def test_compiler_environment_does_not_inherit_host_state(monkeypatch) -> None:
    monkeypatch.setenv("CPLUS_INCLUDE_PATH", "/candidate-controlled")
    monkeypatch.setenv("W8_SECRET_SENTINEL", "must-not-leak")

    environment = _compiler_environment()

    assert "CPLUS_INCLUDE_PATH" not in environment
    assert "W8_SECRET_SENTINEL" not in environment
