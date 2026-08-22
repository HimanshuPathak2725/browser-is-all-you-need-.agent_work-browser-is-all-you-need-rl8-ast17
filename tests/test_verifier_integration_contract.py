from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from glm47_posttraining.verifiers import cpp_c1, cpp_c2, cpp_c3, cpp_c4, p1, p2


def _c1(kernel: int | None) -> cpp_c1.C1Receipt:
    scored = kernel is not None
    result = cpp_c1.VerifierResult(
        verifier=cpp_c1.VERIFIER_ID,
        status=("passed" if kernel == 1 else "failed") if scored else "invalid",
        kernel=kernel,
        phase="complete" if kernel == 1 else "public_api_probe",
        failure_code=None if kernel == 1 else "C1_TEST_FAILURE",
        probe_id=None,
        evidence=cpp_c1.DiagnosticEvidence("0" * 64, "", 0, "completed"),
    )
    return cpp_c1.C1Receipt(
        schema_version=cpp_c1.SCHEMA_VERSION,
        category=cpp_c1.CATEGORY,
        disposition="scored" if scored else "infrastructure_invalid",
        verifier_results=(result,),
        category_score=kernel,
        contract_version="contract-v1",
        compiler_profile="compiler-v1",
    )


def _c2(kernel: int | None) -> cpp_c2.C2Receipt:
    scored = kernel is not None
    return cpp_c2.C2Receipt(
        schema_version=cpp_c2.C2_SCHEMA_VERSION,
        category=cpp_c2.C2_CATEGORY,
        disposition="scored" if scored else "infrastructure_invalid",
        verifier=cpp_c2.C2_VERIFIER_ID,
        status=("passed" if kernel == 1 else "failed") if scored else "invalid",
        kernel=kernel,
        category_score=kernel,
        attribution={
            "declaration_surface": {"status": "ruled_out", "reward_bearing": False},
            "definition_binding": {"status": "ruled_out", "reward_bearing": False},
        },
        compiler_profile={},
        compile_phase={"phase": "compile_to_object"},
        failure_code=(
            None
            if kernel == 1
            else "C2_TRANSLATION_FAILURE"
            if kernel == -1
            else "COMPILER_UNAVAILABLE"
        ),
        diagnostic="",
        contract_version="contract-v1",
    )


def _c3(kernel: int | None) -> cpp_c3.C3Receipt:
    scored = kernel is not None
    result = cpp_c3.C3VerifierResult(
        verifier=cpp_c3.C3_VERIFIER_ID,
        status=("passed" if kernel == 1 else "failed") if scored else "invalid",
        kernel=kernel,
        failure_code=(
            None if kernel == 1 else "C3_BEHAVIOR_MISMATCH" if kernel == -1 else "C3_ORACLE_INVALID"
        ),
        phase="behavior_oracle",
        evidence={},
    )
    return cpp_c3.C3Receipt(
        schema_version=cpp_c3.C3_SCHEMA_VERSION,
        category="C3",
        disposition=(
            cpp_c3.C3Disposition.SCORED if scored else cpp_c3.C3Disposition.INFRASTRUCTURE_INVALID
        ),
        verifier_results=(result,),
        category_score=kernel,
        contract_version="contract-v1",
        contract_digest=None,
        oracle_id="oracle",
        oracle_version="v1",
    )


def _c4(kernel: int | None) -> cpp_c4.C4Receipt:
    scored = kernel is not None
    return cpp_c4.C4Receipt(
        disposition="scored" if scored else "infrastructure_invalid",
        contract_version="contract-v1",
        verifier_result=cpp_c4.VerifierResult(
            verifier=cpp_c4.VERIFIER_ID,
            status=("passed" if kernel == 1 else "failed") if scored else "not_evaluated",
            kernel=kernel,
            failure_code=(
                None
                if kernel == 1
                else "C4_LINK_COMPLETENESS_FAILURE"
                if kernel == -1
                else "C4_INFRASTRUCTURE_EXECUTION_FAILURE"
            ),
        ),
        attribution_evidence=(cpp_c4.StageEvidence("binding", "passed"),),
    )


def _p1(kernel: int | None) -> p1.P1Receipt:
    scored = kernel is not None
    result = p1.VerifierResult(
        p1.VERIFIER_ID,
        ("passed" if kernel == 1 else "failed") if scored else "not_evaluated",
        kernel,
        None if kernel == 1 else "P1_CONTEXT_EXHAUSTED" if kernel == -1 else "P1_INVALID",
    )
    return p1.P1Receipt(
        schema_version=p1.RECEIPT_SCHEMA_VERSION,
        category=p1.CATEGORY,
        contract_version="contract-v1",
        disposition="scored" if scored else "infrastructure_invalid",
        verifier_results=(result,),
        kernels=(kernel,) if scored else None,
        category_score=float(kernel) if scored else None,
        evidence={},
    )


def _p2(kernel: int | None) -> p2.P2Receipt:
    scored = kernel is not None
    result = p2.VerifierResult(
        p2.VERIFIER_ID,
        ("passed" if kernel == 1 else "failed") if scored else "not_evaluated",
        kernel,
        None if kernel == 1 else "P2_NO_SEMANTIC_PROGRESS" if kernel == -1 else "P2_INVALID",
    )
    return p2.P2Receipt(
        schema_version=p2.RECEIPT_SCHEMA_VERSION,
        category=p2.CATEGORY,
        contract_version="contract-v1",
        disposition="scored" if scored else "infrastructure_invalid",
        verifier_results=(result,),
        kernels=(kernel,) if scored else None,
        category_score=float(kernel) if scored else None,
        evidence={},
    )


ReceiptFactory = Callable[[int | None], Any]
FACTORIES: tuple[ReceiptFactory, ...] = (_c1, _c2, _c3, _c4, _p1, _p2)


def test_all_categories_serialize_the_minimum_receipt_boundary() -> None:
    required = {
        "schema_version",
        "category",
        "disposition",
        "verifier_results",
        "kernels",
        "category_score",
        "contract_version",
    }
    for factory in FACTORIES:
        document = factory(1).to_dict()
        assert required <= document.keys()
        assert len(document["verifier_results"]) == 1
        assert "overall_score" not in document


def test_every_category_uses_binary_kernels_and_exact_mean_score() -> None:
    for factory in FACTORIES:
        for kernel in (-1, 1):
            document = factory(kernel).to_dict()
            assert document["kernels"] == [kernel]
            assert document["category_score"] == sum(document["kernels"]) / len(document["kernels"])


def test_every_category_invalid_state_has_no_reward() -> None:
    for factory in FACTORIES:
        document = factory(None).to_dict()
        assert document["disposition"] != "scored"
        assert document["kernels"] is None
        assert document["category_score"] is None
        assert document["verifier_results"][0]["kernel"] is None


def test_technical_stages_do_not_create_extra_verifier_results() -> None:
    c2_receipt = _c2(-1)
    c4_receipt = _c4(-1)

    assert len(c2_receipt.verifier_results) == 1
    assert all(not gate["reward_bearing"] for gate in c2_receipt.attribution.values())
    assert len(c4_receipt.to_dict()["verifier_results"]) == 1
    assert all(not stage.reward_bearing for stage in c4_receipt.attribution_evidence)


def test_independent_categories_allow_meaningful_mixed_outcomes() -> None:
    assert (_c1(-1).category_score, _c2(1).category_score) == (-1, 1)
    assert (_c2(-1).category_score, _c4(1).category_score) == (-1, 1)
    assert (_c2(1).category_score, _c4(-1).category_score) == (1, -1)
    assert (
        _c1(1).category_score,
        _c2(1).category_score,
        _c4(1).category_score,
        _c3(-1).category_score,
    ) == (1, 1, 1, -1)
    assert (_p1(-1).category_score, _p2(None).category_score) == (-1.0, None)
    assert _p2(-1).category_score == -1.0


def test_constructor_initializer_error_is_c2_while_c4_binding_passes(tmp_path: Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        pytest.skip("joint C2/C4 regression requires g++")
    executable = str(Path(compiler).resolve())
    identity = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    header = """\
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
    implementation = """\
#include "crypto_square.h"
namespace crypto_square {
cipher::cipher(const std::string& text) : text_(missing_implementation_name) {}
std::string cipher::normalized_cipher_text() const { return text_; }
}
"""
    declaration_probe = """\
#include "crypto_square.h"
#include <string>
#include <type_traits>
using cipher_type = crypto_square::cipher;
using method_type = std::string (cipher_type::*)() const;
static_assert(std::is_constructible_v<cipher_type, const std::string&>);
static_assert(std::is_same_v<decltype(&cipher_type::normalized_cipher_text), method_type>);
"""
    c2_contract = cpp_c2.C2Contract(
        contract_version="joint-contract-v1",
        compiler=cpp_c2.CompilerProfile(
            profile_id="joint-gcc-v1",
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
        ),
        required_files=("crypto_square.h", "crypto_square.cpp"),
        implementation_files=("crypto_square.cpp",),
        public_declaration_probe=declaration_probe,
    )
    candidate = cpp_c2.C2Candidate(
        contract_version="joint-contract-v1",
        files={"crypto_square.h": header, "crypto_square.cpp": implementation},
    )
    c2_receipt = cpp_c2.C2ImplementationTranslationVerifier(
        expected_contract_version="joint-contract-v1",
        scratch_root=tmp_path,
    ).evaluate_candidate(candidate, c2_contract)

    workspace = tmp_path / "joint-workspace"
    workspace.mkdir()
    (workspace / "crypto_square.h").write_text(header, encoding="utf-8")
    (workspace / "crypto_square.cpp").write_text(implementation, encoding="utf-8")
    c4_contract = cpp_c4.C4Contract(
        contract_version="joint-contract-v1",
        header="crypto_square.h",
        implementation_units=("crypto_square.cpp",),
        definition_owners=("crypto_square::cipher",),
        declaration_probe_source=declaration_probe,
        exhaustive_link_harness_source="""\
#include "crypto_square.h"
#include <string>
int main() {
    crypto_square::cipher value(std::string("abc"));
    auto method = &crypto_square::cipher::normalized_cipher_text;
    return method == nullptr || sizeof(value) == 0;
}
""",
        compiler=cpp_c4.CompilerProfile(
            executable=executable,
            identity_sha256=cpp_c4.fingerprint_compiler(executable),
        ),
    )
    c4_receipt = cpp_c4.evaluate_cpp_c4(
        workspace,
        c4_contract,
        expected_contract_version="joint-contract-v1",
    )

    assert c2_receipt.disposition == "scored"
    assert c2_receipt.kernel == -1
    assert c4_receipt.disposition == "scored"
    assert c4_receipt.kernel == 1
