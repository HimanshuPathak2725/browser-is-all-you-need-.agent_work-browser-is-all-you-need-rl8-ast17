from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

import glm47_posttraining.aider_polyglot.harness as harness_module
from glm47_posttraining.aider_polyglot.harness import run_shadow_weighted45_tests


def test_header_only_candidate_gets_a_synthetic_syntax_translation_unit(
    tmp_path: Path, monkeypatch,
) -> None:
    exercise = tmp_path / "header-only"
    (exercise / ".grader").mkdir(parents=True)
    header = "#pragma once\ninline int answer(){return 42;}\n"
    (exercise / "answer.hpp").write_text(header, encoding="utf-8")
    hidden = (
        '#include "answer.hpp"\n'
        "int main(){\n"
        " if(answer()!=42) return 1;\n"
        " if(answer()<0) return 2;\n"
        " if(answer()>100) return 3;\n"
        " if(answer()%2!=0) return 4;\n"
        " if(answer()!=answer()) return 5;\n"
        " return 0;\n}\n"
    )
    (exercise / ".grader" / "test.cpp").write_text(hidden, encoding="utf-8")
    scripts: list[str] = []

    def fake_stage(
        _scratch: Path, script: str, *, image: str, timeout_s: int
    ) -> subprocess.CompletedProcess[str]:
        del image, timeout_s
        scripts.append(script)
        output = "GLM47_AIDER_WEIGHTED45_fixed:0\n" if "GLM47_AIDER_SUITE=" in script else ""
        return subprocess.CompletedProcess(["fake"], 0, stdout=output, stderr="")

    monkeypatch.setattr(harness_module.secrets, "token_hex", lambda _size: "fixed")
    monkeypatch.setattr(harness_module, "_run_stage", fake_stage)
    result = run_shadow_weighted45_tests(
        exercise,
        {"answer.hpp": header},
        expected_test_sha256=hashlib.sha256(hidden.encode()).hexdigest(),
    )

    assert result.status == "passed"
    syntax = next(script for script in scripts if "-fsyntax-only" in script)
    assert ".grader/candidate_headers.cpp" in syntax
    assert all(result.weighted45_checks.values())


def test_cpp_only_candidate_included_by_grader_is_not_linked_twice(
    tmp_path: Path, monkeypatch,
) -> None:
    exercise = tmp_path / "cpp-only"
    (exercise / ".grader").mkdir(parents=True)
    implementation = "inline int answer(){return 42;}\n"
    (exercise / "answer.cpp").write_text(implementation, encoding="utf-8")
    hidden = (
        '#include "answer.cpp"\n'
        "int main(){\n"
        " if(answer()!=42) return 1;\n"
        " if(answer()<0) return 2;\n"
        " if(answer()>100) return 3;\n"
        " if(answer()%2!=0) return 4;\n"
        " if(answer()!=answer()) return 5;\n"
        " return 0;\n}\n"
    )
    (exercise / ".grader" / "test.cpp").write_text(hidden, encoding="utf-8")
    scripts: list[str] = []

    def fake_stage(
        _scratch: Path, script: str, *, image: str, timeout_s: int
    ) -> subprocess.CompletedProcess[str]:
        del image, timeout_s
        scripts.append(script)
        output = "GLM47_AIDER_WEIGHTED45_fixed:0\n" if "GLM47_AIDER_SUITE=" in script else ""
        return subprocess.CompletedProcess(["fake"], 0, stdout=output, stderr="")

    monkeypatch.setattr(harness_module.secrets, "token_hex", lambda _size: "fixed")
    monkeypatch.setattr(harness_module, "_run_stage", fake_stage)
    result = run_shadow_weighted45_tests(
        exercise,
        {"answer.cpp": implementation},
        expected_test_sha256=hashlib.sha256(hidden.encode()).hexdigest(),
    )

    assert result.status == "passed"
    syntax = next(script for script in scripts if "-fsyntax-only" in script)
    assert "answer.cpp" in syntax
    link = next(script for script in scripts if ".grader/test.o -o" in script)
    assert "answer.cpp" not in link
    sanitizer_link = next(script for script in scripts if ".grader/test_asan.o" in script)
    assert "answer.cpp" not in sanitizer_link
    assert all(result.weighted45_checks.values())
