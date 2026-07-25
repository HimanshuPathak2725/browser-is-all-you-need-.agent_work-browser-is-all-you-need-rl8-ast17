"""Sandboxed build-and-test harness for Aider Polyglot C++ exercises."""

from __future__ import annotations

import hashlib
import os
import platform
import re
import secrets
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping

from glm47_posttraining.cpp_perf.sandbox import (
    SandboxInfrastructureError,
    docker_base_args,
    sandbox_backend,
)

from .ast_evaluator import validate_libclang_runtime
from .schema import AiderTestResult, WEIGHTED45_HARNESS_CHECK_IDS


DEFAULT_AIDER_DOCKER_IMAGE = "glm47-aider-polyglot-cpp:latest"
DEFAULT_CONFIGURE_TIMEOUT_S = 30
DEFAULT_BUILD_TIMEOUT_S = 120
DEFAULT_TEST_TIMEOUT_S = 30
MAX_CANDIDATE_FILE_BYTES = 256 * 1024
PASS_RE = re.compile(
    r"All tests passed \(\s*\d+ assertions? in\s*(\d+) test cases?\)", re.IGNORECASE
)
FAIL_RE = re.compile(
    r"test cases:\s*(\d+)\s*\|\s*(\d+) passed\s*\|\s*(\d+) failed",
    re.IGNORECASE,
)
ORDINAL_RETURN_RE = re.compile(r"return\s+(\d+)\s*;")
COUNTED_TOTAL_RE = re.compile(
    r"^\s*#\s*define\s+GLM47_AIDER_COUNTED_TESTS\s+(\d+)\s*$",
    re.MULTILINE,
)
MIN_ORDINAL_CHECKS = 4
WEIGHTED45_SUITE_COUNT = 5
WEIGHTED45_MACRO_NAMES = ("CHECK", "REQUIRE")
WEIGHTED45_CONCURRENCY_RE = re.compile(
    r"\b(?:std::(?:thread|jthread|mutex|shared_mutex|atomic|condition_variable)|pthread_)"
)
INFRASTRUCTURE_MARKERS = (
    "cannot connect to the docker daemon",
    "error response from daemon",
    "failed to create shim task",
    "no such image",
    "leaksanitizer does not work under ptrace",
    "leaksanitizer has encountered a fatal error",
    "threadsanitizer: unexpected memory mapping",
    "threadsanitizer: failed to mmap",
    "shadow memory range interleaves",
)
FORBIDDEN_CANDIDATE_PATTERNS = (
    re.compile(r"#\s*(?:define|undef)\s+(?:main|return|if|for|while|switch)\b"),
    re.compile(r"\b(?:std::)?(?:_Exit|_exit|exit|quick_exit|abort|terminate)\s*\("),
    re.compile(r"\b(?:system|popen|fork|vfork|exec[a-z]*|kill|raise)\s*\("),
    re.compile(r"\b(?:__asm__|__asm|asm)\b"),
    re.compile(r"(?:/proc/self|\.grader|CMakeLists\.txt|_test\.cpp)"),
)


class CandidatePolicyError(ValueError):
    """Generated source attempts to bypass or inspect the hidden verifier."""


def ensure_ast17_tooling(*, raise_on_error: bool = True, require_clang18: bool = False) -> bool:
    """Verify libclang C++17 AST tooling before training or evaluation starts."""

    return validate_libclang_runtime(
        raise_on_error=raise_on_error,
        require_clang18=require_clang18,
    )


def _shadow_ordinal_total(grader_source: str) -> int | None:
    """Return N when the grader short-circuits with clean sequential ordinals 1..N.

    Most shadow graders are a single ``main()`` of ``if (!check) return k;`` lines
    with a distinct 1-based ``k`` per check, so the renamed grader's return value
    (surfaced as the candidate process exit code) is the index of the first failing
    check. That lets us score partial progress without running checks against known-
    bad state, which would risk crashes that destroy the tally. Graders that do not
    follow this convention (abort-based ``assert``, constant ``return 1``) yield
    ``None`` and fall back to binary pass/fail.
    """
    values = [int(match) for match in ORDINAL_RETURN_RE.findall(grader_source)]
    values = [value for value in values if value != 0]
    if len(values) >= MIN_ORDINAL_CHECKS and values == list(range(1, len(values) + 1)):
        return len(values)
    return None


def _shadow_counted_total(grader_source: str) -> int | None:
    """Read the all-check grader contract, if present.

    A counted grader defines ``GLM47_AIDER_COUNTED_TESTS N``, executes all N
    independent checks, and returns the number of failed checks (zero means full
    pass). The hidden grader hash prevents a candidate from changing this contract.
    """
    match = COUNTED_TOTAL_RE.search(grader_source)
    if match is None:
        return None
    total = int(match.group(1))
    return total if total > 0 else None


def aider_sandbox_image_dockerfile() -> str:
    return """FROM gcc:13
RUN apt-get update \\
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends cmake make \\
    && rm -rf /var/lib/apt/lists/*
"""


def build_aider_sandbox_image(
    *, image: str = DEFAULT_AIDER_DOCKER_IMAGE
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "build", "-t", image, "-"],
        input=aider_sandbox_image_dockerfile(),
        check=False,
        capture_output=True,
        text=True,
    )


def run_aider_tests(
    exercise_dir: str | Path,
    files: Mapping[str, str],
    *,
    image: str = DEFAULT_AIDER_DOCKER_IMAGE,
    configure_timeout_s: int = DEFAULT_CONFIGURE_TIMEOUT_S,
    build_timeout_s: int = DEFAULT_BUILD_TIMEOUT_S,
) -> AiderTestResult:
    """Apply candidate files and run the benchmark's build-triggered Catch suite."""

    source = Path(exercise_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"exercise directory not found: {source}")

    with TemporaryDirectory(prefix=f"aider_{source.name}_") as scratch_value:
        scratch = Path(scratch_value)
        shutil.copytree(source, scratch, dirs_exist_ok=True)
        for name, contents in files.items():
            if len(contents.encode("utf-8")) > MAX_CANDIDATE_FILE_BYTES:
                raise ValueError(f"candidate file exceeds byte limit: {name}")
            target = scratch / name
            if target.parent != scratch:
                raise ValueError(f"candidate path escapes exercise root: {name}")
            target.write_text(contents, encoding="utf-8")

        configure = _run_stage(
            scratch,
            f"timeout {configure_timeout_s}s cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON",
            image=image,
            timeout_s=configure_timeout_s + 10,
        )
        configure_logs = _combined_logs(configure)
        if _is_infrastructure_error(configure_logs):
            raise SandboxInfrastructureError(configure_logs)
        if configure.returncode != 0:
            return AiderTestResult(status="compile_failed", logs={"configure": configure_logs})

        build = _run_stage(
            scratch,
            f"timeout {build_timeout_s}s cmake --build build --parallel 2",
            image=image,
            timeout_s=build_timeout_s + 10,
        )
        build_logs = _combined_logs(build)
        logs = {"configure": configure_logs, "build_and_test": build_logs}
        if _is_infrastructure_error(build_logs):
            raise SandboxInfrastructureError(build_logs)

        passed = PASS_RE.search(build_logs)
        if passed:
            total = int(passed.group(1))
            return AiderTestResult(
                status="passed", tests_passed=total, tests_total=total, logs=logs
            )

        failed = FAIL_RE.search(build_logs)
        if failed:
            total, passed_count, _failed_count = (int(value) for value in failed.groups())
            return AiderTestResult(
                status="tests_failed",
                tests_passed=passed_count,
                tests_total=total,
                logs=logs,
            )

        if build.returncode == 124 or "timed out" in build_logs.lower():
            return AiderTestResult(status="candidate_timeout", logs=logs)
        return AiderTestResult(status="compile_failed", logs=logs)


def run_shadow_tests(
    exercise_dir: str | Path,
    files: Mapping[str, str],
    *,
    image: str = DEFAULT_AIDER_DOCKER_IMAGE,
    build_timeout_s: int = DEFAULT_BUILD_TIMEOUT_S,
    test_timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
    expected_test_sha256: str | None = None,
) -> AiderTestResult:
    """Compile candidate sources against an answer-blind C++17 executable oracle."""

    source = Path(exercise_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"shadow task directory not found: {source}")
    grader_path = source / ".grader" / "test.cpp"
    if not grader_path.is_file():
        raise FileNotFoundError(f"shadow executable oracle not found: {source}")
    grader_bytes = grader_path.read_bytes()
    if expected_test_sha256:
        observed = hashlib.sha256(grader_bytes).hexdigest()
        if observed != expected_test_sha256:
            raise ValueError(f"shadow executable oracle hash mismatch: {source}")
    grader_source = grader_bytes.decode("utf-8", errors="replace")
    counted_total = _shadow_counted_total(grader_source)
    ordinal_total = None if counted_total is not None else _shadow_ordinal_total(grader_source)

    with TemporaryDirectory(prefix=f"aider_shadow_{source.name}_") as scratch_value:
        scratch = Path(scratch_value)
        shutil.copytree(source, scratch, dirs_exist_ok=True)
        for name, contents in files.items():
            if len(contents.encode("utf-8")) > MAX_CANDIDATE_FILE_BYTES:
                raise ValueError(f"candidate file exceeds byte limit: {name}")
            _validate_candidate_source(name, contents)
            target = scratch / name
            if target.parent != scratch:
                raise ValueError(f"candidate path escapes shadow task root: {name}")
            target.write_text(contents, encoding="utf-8")

        sources = sorted(path.name for path in scratch.iterdir() if path.suffix in {".cpp", ".cc"})
        quoted_sources = " ".join(shlex_quote(name) for name in sources)
        success_marker = f"GLM47_AIDER_PASS_{secrets.token_hex(16)}"
        driver = scratch / ".grader" / "driver.cpp"
        driver.write_text(
            "#include <cstdio>\n"
            "int glm47_hidden_main();\n"
            "int main() {\n"
            "  const int result = glm47_hidden_main();\n"
            f'  if (result == 0) {{ std::fputs("{success_marker}\\n", stdout); '
            "std::fflush(stdout); }\n"
            "  return result;\n"
            "}\n",
            encoding="utf-8",
        )
        compiler_flags = "-std=c++17 -Wall -Wextra -Werror -pedantic -pthread -I."
        compile_result = _run_stage(
            scratch,
            " ".join(
                [
                    f"timeout {build_timeout_s}s c++",
                    compiler_flags,
                    "-Dmain=glm47_hidden_main -c .grader/test.cpp -o .grader/test.o",
                    f"&& rm .grader/test.cpp && timeout {build_timeout_s}s c++",
                    compiler_flags,
                    quoted_sources,
                    ".grader/driver.cpp .grader/test.o -o .grader/candidate_test",
                ]
            ),
            image=image,
            timeout_s=build_timeout_s + 10,
        )
        compile_logs = _combined_logs(compile_result)
        if _is_infrastructure_error(compile_logs):
            raise SandboxInfrastructureError(compile_logs)
        if compile_result.returncode == 124 or "timed out" in compile_logs.lower():
            return AiderTestResult(
                status="candidate_timeout",
                candidate_returncode=compile_result.returncode,
                logs={"compile": compile_logs},
            )
        if compile_result.returncode != 0:
            return AiderTestResult(
                status="compile_failed",
                candidate_returncode=compile_result.returncode,
                logs={"compile": compile_logs},
            )
        # The candidate process sees neither hidden test source nor its linkable object.
        (scratch / ".grader" / "test.o").unlink(missing_ok=True)
        driver.unlink(missing_ok=True)

        test_result = _run_stage(
            scratch,
            f"timeout {test_timeout_s}s .grader/candidate_test",
            image=image,
            timeout_s=test_timeout_s + 10,
        )
        test_logs = _combined_logs(test_result)
        logs = {"compile": compile_logs, "test": test_logs}
        if _is_infrastructure_error(test_logs):
            raise SandboxInfrastructureError(test_logs)
        total = counted_total or ordinal_total or 1
        if test_result.returncode == 124 or "timed out" in test_logs.lower():
            return AiderTestResult(
                status="candidate_timeout",
                tests_total=total,
                candidate_returncode=test_result.returncode,
                logs=logs,
            )
        if test_result.returncode == 0 and success_marker in test_logs:
            return AiderTestResult(
                status="passed",
                tests_passed=total,
                tests_total=total,
                candidate_returncode=0,
                logs=logs,
            )
        # Counted graders run every independent check and return the number failed.
        # Legacy ordinal graders return the 1-based index of the first failed check.
        # Anything outside the declared range (a crash signal or malformed grader)
        # scores zero.
        passed_checks = 0
        if counted_total is not None and 1 <= test_result.returncode <= counted_total:
            passed_checks = counted_total - test_result.returncode
        elif ordinal_total is not None and 1 <= test_result.returncode <= ordinal_total:
            passed_checks = test_result.returncode - 1
        return AiderTestResult(
            status="tests_failed",
            tests_passed=passed_checks,
            tests_total=total,
            candidate_returncode=test_result.returncode,
            logs=logs,
        )


def run_shadow_weighted45_tests(
    exercise_dir: str | Path,
    files: Mapping[str, str],
    *,
    image: str = DEFAULT_AIDER_DOCKER_IMAGE,
    build_timeout_s: int = DEFAULT_BUILD_TIMEOUT_S,
    test_timeout_s: int = DEFAULT_TEST_TIMEOUT_S,
    expected_test_sha256: str | None = None,
) -> AiderTestResult:
    """Return observed K/R/H/A outcomes for the weighted 45-check policy.

    The verified hidden grader is instrumented in the private scratch directory
    and invoked in five isolated processes.  Each invocation enforces one stable
    partition of the grader's actual checks, so H1--H5 are observed independently
    instead of inferred from the first failing assertion.
    """

    source = Path(exercise_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"shadow task directory not found: {source}")
    grader_path = source / ".grader" / "test.cpp"
    if not grader_path.is_file():
        raise FileNotFoundError(f"shadow executable oracle not found: {source}")
    grader_bytes = grader_path.read_bytes()
    if expected_test_sha256:
        observed = hashlib.sha256(grader_bytes).hexdigest()
        if observed != expected_test_sha256:
            raise ValueError(f"shadow executable oracle hash mismatch: {source}")
    grader_source = grader_bytes.decode("utf-8", errors="strict")
    instrumented_source, grader_check_count = _instrument_weighted45_grader(grader_source)

    result: AiderTestResult
    with TemporaryDirectory(prefix=f"aider_weighted45_{source.name}_") as scratch_value:
        scratch = Path(scratch_value)
        shutil.copytree(source, scratch, dirs_exist_ok=True)
        for name, contents in files.items():
            if len(contents.encode("utf-8")) > MAX_CANDIDATE_FILE_BYTES:
                raise ValueError(f"candidate file exceeds byte limit: {name}")
            _validate_candidate_source(name, contents)
            target = scratch / name
            if target.parent != scratch:
                raise ValueError(f"candidate path escapes shadow task root: {name}")
            target.write_text(contents, encoding="utf-8")

        private_grader = scratch / ".grader" / "test.cpp"
        private_grader.write_text(instrumented_source, encoding="utf-8")
        sources = sorted(path.name for path in scratch.iterdir() if path.suffix in {".cpp", ".cc"})
        quoted_sources = " ".join(shlex_quote(name) for name in sources)
        success_marker = f"GLM47_AIDER_WEIGHTED45_{secrets.token_hex(16)}"
        driver = scratch / ".grader" / "driver.cpp"
        driver.write_text(
            "#include <cstdio>\n"
            "int glm47_hidden_main();\n"
            "int main() {\n"
            "  int result = 1;\n"
            "  try { result = glm47_hidden_main(); } catch (...) { result = 1; }\n"
            f'  std::printf("{success_marker}:%d\\n", result);\n'
            "  std::fflush(stdout);\n"
            "  return result;\n"
            "}\n",
            encoding="utf-8",
        )
        compiler_flags = "-std=c++17 -Wall -Wextra -Werror -pedantic -pthread -I."
        hidden_compiler_flags = "-std=c++17 -Wall -Wextra -pedantic -pthread -I."
        logs: dict[str, str] = {}
        checks = {check_id: False for check_id in WEIGHTED45_HARNESS_CHECK_IDS}
        evidence = {
            check_id: "stage not reached" for check_id in WEIGHTED45_HARNESS_CHECK_IDS
        }

        syntax = _run_stage(
            scratch,
            f"timeout {build_timeout_s}s c++ {compiler_flags} -fsyntax-only {quoted_sources}",
            image=image,
            timeout_s=build_timeout_s + 10,
        )
        syntax_logs = _combined_logs(syntax)
        logs["candidate_syntax"] = syntax_logs
        if _is_infrastructure_error(syntax_logs):
            raise SandboxInfrastructureError(syntax_logs)
        checks["K3"] = syntax.returncode == 0
        evidence["K3"] = f"candidate -fsyntax-only returncode={syntax.returncode}"

        hidden_compile = _run_stage(
            scratch,
            f"timeout {build_timeout_s}s c++ {hidden_compiler_flags} "
            "-Dmain=glm47_hidden_main -c .grader/test.cpp -o .grader/test.o",
            image=image,
            timeout_s=build_timeout_s + 10,
        )
        hidden_logs = _combined_logs(hidden_compile)
        logs["hidden_typecheck"] = hidden_logs
        if _is_infrastructure_error(hidden_logs):
            raise SandboxInfrastructureError(hidden_logs)
        checks["K2"] = hidden_compile.returncode == 0
        evidence["K2"] = f"hidden API/type-check returncode={hidden_compile.returncode}"
        checks["K4"] = checks["K2"] and checks["K3"]
        evidence["K4"] = "strict warning flags accepted all translation units"

        if not checks["K4"]:
            result = AiderTestResult(
                status="compile_failed",
                tests_total=WEIGHTED45_SUITE_COUNT,
                candidate_returncode=(
                    syntax.returncode if syntax.returncode != 0 else hidden_compile.returncode
                ),
                logs=logs,
                weighted45_checks=checks,
                weighted45_evidence=evidence,
            )
        else:
            link = _run_stage(
                scratch,
                f"timeout {build_timeout_s}s c++ {compiler_flags} {quoted_sources} "
                ".grader/driver.cpp .grader/test.o -o .grader/candidate_test",
                image=image,
                timeout_s=build_timeout_s + 10,
            )
            link_logs = _combined_logs(link)
            logs["link"] = link_logs
            if _is_infrastructure_error(link_logs):
                raise SandboxInfrastructureError(link_logs)
            checks["K1"] = link.returncode == 0
            evidence["K1"] = f"hidden-grader link returncode={link.returncode}"
            target_probe = _run_stage(
                scratch,
                "test -x .grader/candidate_test",
                image=image,
                timeout_s=10,
            )
            checks["K5"] = target_probe.returncode == 0
            evidence["K5"] = f"executable target probe returncode={target_probe.returncode}"

            sanitizer_ready = False
            sanitizer_compile_logs = "normal link failed"
            tsan_ready = False
            tsan_compile_logs = "not applicable"
            task_contract_source = "\n".join(
                path.read_text(encoding="utf-8")
                for path in source.iterdir()
                if path.is_file() and path.suffix in {".cpp", ".cc", ".h", ".hpp"}
            )
            concurrency_applicable = bool(
                WEIGHTED45_CONCURRENCY_RE.search(grader_source + "\n" + task_contract_source)
            )
            if checks["K1"] and checks["K5"]:
                sanitizer = _run_stage(
                    scratch,
                    f"timeout {build_timeout_s}s c++ {hidden_compiler_flags} "
                    "-fsanitize=address,undefined -fno-omit-frame-pointer "
                    "-Dmain=glm47_hidden_main -c .grader/test.cpp -o .grader/test_asan.o "
                    f"&& timeout {build_timeout_s}s c++ {compiler_flags} "
                    "-fsanitize=address,undefined -fno-omit-frame-pointer "
                    f"{quoted_sources} .grader/driver.cpp .grader/test_asan.o "
                    "-o .grader/candidate_test_asan",
                    image=image,
                    timeout_s=2 * build_timeout_s + 10,
                )
                sanitizer_compile_logs = _combined_logs(sanitizer)
                logs["sanitizer_compile"] = sanitizer_compile_logs
                if _is_infrastructure_error(sanitizer_compile_logs):
                    raise SandboxInfrastructureError(sanitizer_compile_logs)
                sanitizer_ready = sanitizer.returncode == 0
                if concurrency_applicable:
                    tsan = _run_stage(
                        scratch,
                        f"timeout {build_timeout_s}s c++ {hidden_compiler_flags} -fsanitize=thread "
                        "-Dmain=glm47_hidden_main -c .grader/test.cpp -o .grader/test_tsan.o "
                        f"&& timeout {build_timeout_s}s c++ {compiler_flags} -fsanitize=thread "
                        f"{quoted_sources} .grader/driver.cpp .grader/test_tsan.o "
                        "-o .grader/candidate_test_tsan",
                        image=image,
                        timeout_s=2 * build_timeout_s + 10,
                    )
                    tsan_compile_logs = _combined_logs(tsan)
                    logs["thread_sanitizer_compile"] = tsan_compile_logs
                    if _is_infrastructure_error(tsan_compile_logs):
                        raise SandboxInfrastructureError(tsan_compile_logs)
                    tsan_ready = tsan.returncode == 0

            # Candidate execution cannot read the hidden source or its objects.
            private_grader.unlink(missing_ok=True)
            for object_name in ("test.o", "test_asan.o", "test_tsan.o"):
                (scratch / ".grader" / object_name).unlink(missing_ok=True)
            driver.unlink(missing_ok=True)

            if not (checks["K1"] and checks["K5"]):
                result = AiderTestResult(
                    status="compile_failed",
                    tests_total=WEIGHTED45_SUITE_COUNT,
                    candidate_returncode=link.returncode,
                    logs=logs,
                    weighted45_checks=checks,
                    weighted45_evidence=evidence,
                )
            else:
                before_runtime = _workspace_file_snapshot(scratch)
                full_run = _run_stage(
                    scratch,
                    f"timeout {test_timeout_s}s env GLM47_AIDER_SUITE=-1 "
                    ".grader/candidate_test",
                    image=image,
                    timeout_s=test_timeout_s + 10,
                )
                full_logs = _combined_logs(full_run)
                logs["standard_run"] = full_logs
                if _is_infrastructure_error(full_logs):
                    raise SandboxInfrastructureError(full_logs)
                full_handshake = f"{success_marker}:{full_run.returncode}" in full_logs
                checks["R1"] = full_run.returncode not in {124, 126, 127}
                checks["R2"] = full_run.returncode in {0, 1}
                checks["R3"] = full_run.returncode in {0, 1}
                checks["R5"] = full_handshake
                evidence["R1"] = f"standard process returncode={full_run.returncode}"
                evidence["R2"] = f"non-crash returncode={full_run.returncode}"
                evidence["R3"] = f"weighted grader status returncode={full_run.returncode}"
                evidence["R5"] = f"secret verifier handshake={full_handshake}"

                suite_passes: list[bool] = []
                for suite_index in range(WEIGHTED45_SUITE_COUNT):
                    suite_run = _run_stage(
                        scratch,
                        f"timeout {test_timeout_s}s env GLM47_AIDER_SUITE={suite_index} "
                        ".grader/candidate_test",
                        image=image,
                        timeout_s=test_timeout_s + 10,
                    )
                    suite_logs = _combined_logs(suite_run)
                    logs[f"hidden_suite_{suite_index + 1}"] = suite_logs
                    if _is_infrastructure_error(suite_logs):
                        raise SandboxInfrastructureError(suite_logs)
                    handshake = f"{success_marker}:{suite_run.returncode}" in suite_logs
                    passed = suite_run.returncode == 0 and handshake
                    check_id = f"H{suite_index + 1}"
                    checks[check_id] = passed
                    evidence[check_id] = (
                        f"partition={suite_index + 1}/5 grader_checks={grader_check_count} "
                        f"returncode={suite_run.returncode} handshake={handshake}"
                    )
                    suite_passes.append(passed)

                checks["A1"] = full_run.returncode == 0 and full_handshake
                evidence["A1"] = (
                    f"standard functional grader returncode={full_run.returncode} "
                    f"handshake={full_handshake}"
                )

                sanitizer_pass = False
                if sanitizer_ready:
                    sanitizer_run = _run_stage(
                        scratch,
                        f"timeout {test_timeout_s}s env GLM47_AIDER_SUITE=-1 "
                        "ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 "
                        "UBSAN_OPTIONS=halt_on_error=1 .grader/candidate_test_asan",
                        image=image,
                        timeout_s=test_timeout_s + 10,
                    )
                    sanitizer_logs = _combined_logs(sanitizer_run)
                    logs["sanitizer_run"] = sanitizer_logs
                    if _is_infrastructure_error(sanitizer_logs):
                        raise SandboxInfrastructureError(sanitizer_logs)
                    sanitizer_handshake = (
                        f"{success_marker}:{sanitizer_run.returncode}" in sanitizer_logs
                    )
                    sanitizer_pass = sanitizer_run.returncode == 0 and sanitizer_handshake
                    evidence["A2"] = (
                        f"ASan/UBSan returncode={sanitizer_run.returncode} "
                        f"handshake={sanitizer_handshake}"
                    )
                else:
                    evidence["A2"] = (
                        "ASan/UBSan build failed: " + sanitizer_compile_logs[-500:]
                    )
                checks["A2"] = sanitizer_pass
                checks["A3"] = full_run.returncode != 124 and full_handshake
                evidence["A3"] = (
                    f"sandbox time/resource-bounded run returncode={full_run.returncode}"
                )

                if not concurrency_applicable:
                    checks["A4"] = True
                    evidence["A4"] = "not applicable: no threading primitive in candidate"
                elif tsan_ready:
                    tsan_run = _run_stage(
                        scratch,
                        f"timeout {test_timeout_s}s env GLM47_AIDER_SUITE=-1 "
                        "TSAN_OPTIONS=halt_on_error=1 .grader/candidate_test_tsan",
                        image=image,
                        timeout_s=test_timeout_s + 10,
                    )
                    tsan_logs = _combined_logs(tsan_run)
                    logs["thread_sanitizer_run"] = tsan_logs
                    if _is_infrastructure_error(tsan_logs):
                        raise SandboxInfrastructureError(tsan_logs)
                    tsan_handshake = f"{success_marker}:{tsan_run.returncode}" in tsan_logs
                    checks["A4"] = tsan_run.returncode == 0 and tsan_handshake
                    evidence["A4"] = (
                        f"TSan returncode={tsan_run.returncode} handshake={tsan_handshake}"
                    )
                else:
                    checks["A4"] = False
                    evidence["A4"] = "TSan build failed: " + tsan_compile_logs[-500:]
                checks["A5"] = all(suite_passes)
                evidence["A5"] = f"all independent hidden partitions={suite_passes}"
                after_runtime = _workspace_file_snapshot(scratch)
                checks["R4"] = before_runtime == after_runtime
                evidence["R4"] = (
                    "no runtime workspace artifacts"
                    if checks["R4"]
                    else f"workspace changed: before={before_runtime} after={after_runtime}"
                )

                passed_count = sum(suite_passes)
                timed_out = full_run.returncode == 124
                status = (
                    "candidate_timeout"
                    if timed_out
                    else "passed"
                    if all(checks[check_id] for check_id in ("A1", "A2", "A3", "A4", "A5"))
                    else "tests_failed"
                )
                result = AiderTestResult(
                    status=status,
                    tests_passed=passed_count,
                    tests_total=WEIGHTED45_SUITE_COUNT,
                    candidate_returncode=full_run.returncode,
                    logs=logs,
                    weighted45_checks=checks,
                    weighted45_evidence=evidence,
                )
    return result


def _instrument_weighted45_grader(source: str) -> tuple[str, int]:
    """Convert the three verified grader idioms into five selectable partitions."""

    macro_names = [
        name
        for name in WEIGHTED45_MACRO_NAMES
        if re.search(rf"^\s*#\s*define\s+{name}\b", source, re.MULTILINE)
    ]
    assertion_count = len(re.findall(r"\bassert\s*\(", source))
    transformed = source
    if macro_names:
        counts = {
            name: len(re.findall(rf"\b{name}\s*\(", source))
            - len(re.findall(rf"^\s*#\s*define\s+{name}\b", source, re.MULTILINE))
            for name in macro_names
        }
        total = sum(counts.values())
        for name in macro_names:
            transformed = re.sub(
                rf"^\s*#\s*define\s+{name}\b[^\n]*$",
                f"#define {name}(...) GLM47_WEIGHTED45_ASSERT(__VA_ARGS__)",
                transformed,
                flags=re.MULTILINE,
            )
    elif assertion_count:
        total = assertion_count
        transformed = re.sub(r"\bassert\s*\(", "GLM47_WEIGHTED45_ASSERT(", transformed)
    else:
        transformed, total = _instrument_direct_return_checks(transformed)
    if total < WEIGHTED45_SUITE_COUNT:
        raise ValueError(
            f"weighted45 hidden grader exposes only {total} independent checks; five required"
        )

    transformed = _ensure_explicit_main_return(transformed)
    support = f"""
#include <cstdlib>
namespace glm47_weighted45_detail {{
constexpr int check_count = {total};
inline int selected_suite() {{
    const char* value = std::getenv("GLM47_AIDER_SUITE");
    if (value == nullptr) return -1;
    return std::atoi(value);
}}
inline int suite_for(int check_index) {{
    const int suite = (check_index * {WEIGHTED45_SUITE_COUNT}) / check_count;
    return suite < {WEIGHTED45_SUITE_COUNT} ? suite : {WEIGHTED45_SUITE_COUNT - 1};
}}
inline bool enforce(int check_index) {{
    const int selected = selected_suite();
    return selected < 0 || suite_for(check_index) == selected;
}}
inline bool failed(bool condition, int check_index) {{
    return condition && enforce(check_index);
}}
}}  // namespace glm47_weighted45_detail
#define GLM47_WEIGHTED45_ASSERT(...) do {{ \
    const bool glm47_weighted45_passed = static_cast<bool>((__VA_ARGS__)); \
    if (glm47_weighted45_detail::failed(!glm47_weighted45_passed, __COUNTER__)) throw 4745; \
}} while (false)
"""
    return support + "\n" + transformed, total


def _instrument_direct_return_checks(source: str) -> tuple[str, int]:
    """Instrument ``if (failure) return N`` graders, including compound failures."""

    replacements: list[tuple[int, int, str]] = []
    check_index = 0
    cursor = 0
    while True:
        match = re.search(r"\bif\s*\(", source[cursor:])
        if match is None:
            break
        start = cursor + match.start()
        open_paren = cursor + match.end() - 1
        close_paren = _matching_cpp_paren(source, open_paren)
        if close_paren is None:
            cursor = open_paren + 1
            continue
        tail = source[close_paren + 1 :]
        return_match = re.match(r"\s*return\s+(?P<value>\d+|code)\s*;", tail)
        if return_match is None or return_match.group("value") == "0":
            cursor = close_paren + 1
            continue
        end = close_paren + 1 + return_match.end()
        condition = source[open_paren + 1 : close_paren]
        atoms = _split_top_level_or(condition)
        lines = []
        for atom in atoms:
            lines.append(
                "if (glm47_weighted45_detail::failed(static_cast<bool>("
                f"{atom.strip()}), {check_index})) throw 4745;"
            )
            check_index += 1
        replacements.append((start, end, "\n".join(lines)))
        cursor = end
    for start, end, replacement in reversed(replacements):
        source = source[:start] + replacement + source[end:]
    return source, check_index


def _matching_cpp_paren(source: str, opening: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    index = opening
    while index < len(source):
        character = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _split_top_level_or(condition: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(condition) - 1:
        character = condition[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character in "([{":
            depth += 1
        elif character in ")]}" and depth:
            depth -= 1
        elif character == "|" and condition[index + 1] == "|" and depth == 0:
            parts.append(condition[start:index])
            start = index + 2
            index += 1
        index += 1
    parts.append(condition[start:])
    return [part for part in parts if part.strip()]


def _ensure_explicit_main_return(source: str) -> str:
    match = re.search(r"\bint\s+main\s*\([^)]*\)\s*\{", source)
    if match is None:
        raise ValueError("weighted45 hidden grader has no int main entry point")
    opening = match.end() - 1
    closing = _matching_cpp_delimiter(source, opening, "{", "}")
    if closing is None:
        raise ValueError("weighted45 hidden grader main body is unbalanced")
    return source[:closing] + "\nreturn 0;\n" + source[closing:]


def _matching_cpp_delimiter(
    source: str, opening: int, opening_character: str, closing_character: str
) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    index = opening
    while index < len(source):
        character = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == opening_character:
            depth += 1
        elif character == closing_character:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _workspace_file_snapshot(root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def _validate_candidate_source(name: str, contents: str) -> None:
    for pattern in FORBIDDEN_CANDIDATE_PATTERNS:
        if pattern.search(contents):
            raise CandidatePolicyError(
                f"candidate file uses a forbidden verifier-bypass primitive: {name}"
            )


def _run_stage(
    scratch: Path, script: str, *, image: str, timeout_s: int
) -> subprocess.CompletedProcess[str]:
    if sandbox_backend() == "local":
        command = _local_sandbox_command(scratch, script)
    else:
        command = docker_base_args(scratch, image=image, memory="4g") + ["bash", "-lc", script]
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=False, timeout=timeout_s
        )
        return subprocess.CompletedProcess(
            completed.args,
            completed.returncode,
            stdout=_text(completed.stdout),
            stderr=_text(completed.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _text(exc.stdout)
        stderr = _text(exc.stderr)
        raise SandboxInfrastructureError(
            "outer sandbox watchdog expired before the sandbox command returned; "
            f"stdout={stdout!r} stderr={stderr!r}"
        ) from exc


def _local_sandbox_command(scratch: Path, script: str) -> list[str]:
    """Use bubblewrap on Linux and fail closed if it is unavailable.

    Modal cannot run Docker-in-Docker. Bubblewrap gives generated programs a
    private mount, PID, IPC, UTS, and (by default) network namespace and
    deliberately does not mount the repository, run volume, or inherited
    environment secrets. GLM47_CPP_SANDBOX_UNSHARE_NET=0 skips only the
    network unshare: gVisor-style runtimes (Modal) reject the RTM_NEWADDR
    loopback setup bwrap performs after unsharing the network namespace.
    """

    if platform.system() != "Linux":
        # Development-only path for macOS unit tests. Paid Linux runs never use it.
        local_script = re.sub(r"\btimeout\s+\d+s\s+", "", script)
        return [
            "bash",
            "-lc",
            f"cd {shlex_quote(str(scratch.resolve()))} && ulimit -c 0 && {local_script}",
        ]

    bwrap = shutil.which("bwrap")
    if not bwrap:
        raise SandboxInfrastructureError(
            "bubblewrap is required for GLM47_CPP_SANDBOX_BACKEND=local on Linux"
        )
    if os.environ.get("GLM47_CPP_SANDBOX_UNSHARE_NET", "1") != "0":
        unshare_flags = ["--unshare-all"]
    else:
        unshare_flags = [
            "--unshare-user-try",
            "--unshare-ipc",
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-cgroup-try",
        ]
    command = [
        bwrap,
        "--die-with-parent",
        "--new-session",
        *unshare_flags,
        "--clearenv",
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "HOME",
        "/tmp",
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
    ]
    for host_path in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
        if Path(host_path).exists():
            command.extend(["--ro-bind", host_path, host_path])
    command.extend(
        [
            "--bind",
            str(scratch.resolve()),
            "/work",
            "--chdir",
            "/work",
            "/bin/bash",
            "-lc",
            "ulimit -c 0 -f 262144 -n 64 -u 128; umask 077; " + script,
        ]
    )
    return command


def assert_local_sandbox_ready() -> None:
    """Fail before allocating a training run if secure local isolation is absent."""

    if sandbox_backend() == "local" and platform.system() == "Linux" and not shutil.which("bwrap"):
        raise SandboxInfrastructureError("bubblewrap is required for secure Aider reward execution")


def run_sandbox_preflight() -> None:
    """Prove normal, ASan/UBSan/LSan, and TSan execution before training."""

    ensure_ast17_tooling()
    assert_local_sandbox_ready()
    with TemporaryDirectory(prefix="aider_sandbox_preflight_") as scratch_value:
        scratch = Path(scratch_value)
        (scratch / "probe.cpp").write_text(
            "#include <thread>\n"
            "int main() { int value = 0; std::thread worker([&] { value = 1; }); "
            "worker.join(); return value == 1 ? 0 : 1; }\n",
            encoding="utf-8",
        )
        result = _run_stage(
            scratch,
            "c++ -std=c++17 -Wall -Wextra -Werror -pedantic -pthread probe.cpp -o probe "
            "&& ./probe "
            "&& c++ -std=c++17 -Wall -Wextra -Werror -pedantic -pthread "
            "-fsanitize=address,undefined -fno-omit-frame-pointer probe.cpp -o probe_asan "
            "&& ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 "
            "UBSAN_OPTIONS=halt_on_error=1 ./probe_asan "
            "&& c++ -std=c++17 -Wall -Wextra -Werror -pedantic -pthread "
            "-fsanitize=thread probe.cpp -o probe_tsan "
            "&& TSAN_OPTIONS=halt_on_error=1 ./probe_tsan",
            image=DEFAULT_AIDER_DOCKER_IMAGE,
            timeout_s=90,
        )
        if result.returncode != 0:
            raise SandboxInfrastructureError(_combined_logs(result) or "sandbox preflight failed")


def shlex_quote(value: str) -> str:
    # Kept local so the candidate command construction has one tiny, auditable surface.
    import shlex

    return shlex.quote(value)


def _combined_logs(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or "") + (result.stderr or "")


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _is_infrastructure_error(logs: str) -> bool:
    lowered = logs.lower()
    return any(marker in lowered for marker in INFRASTRUCTURE_MARKERS)
