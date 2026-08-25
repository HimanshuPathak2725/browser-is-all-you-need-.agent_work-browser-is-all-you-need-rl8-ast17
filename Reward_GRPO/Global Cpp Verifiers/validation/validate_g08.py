from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALIDATION_ROOT = Path(__file__).resolve().parent
GLOBAL_ROOT = VALIDATION_ROOT.parent
REPO_ROOT = Path(__file__).resolve().parents[3]
G08_VERIFIER = GLOBAL_ROOT / "verifiers/verifier_08_header_dependency_odr.py"
CIRCULAR_FIXTURE = REPO_ROOT / "Reward_GRPO/multi_env_fixtures/circular-buffer"
CIRCULAR_CASES = REPO_ROOT / "Reward_GRPO/Circular_Buffer Verifiers/validation/cases"
PHONE_CURRICULUM = REPO_ROOT / "Reward_GRPO/phone_number_grpo.py"
SOURCE_FILES = {
    "circular-buffer": ("circular_buffer.h", "circular_buffer.cpp"),
    "phone-number": ("phone_number.h", "phone_number.cpp"),
}
HEADERS = {
    "circular-buffer": "circular_buffer.h",
    "phone-number": "phone_number.h",
}
PROBE_KINDS = (
    "header-self-contained",
    "repeated-include",
    "protected-dependency",
    "multi-tu-odr",
)
STRICT_FLAGS = (
    "-std=c++17",
    "-Wall",
    "-Wextra",
    "-Wpedantic",
    "-Werror",
)
PROTECTED_SENTINEL = "validation/protected_sentinel.hpp"
PHONE_RECEIPT = re.compile(r"GLM47_PHONE_KERNELS_V1:([01]{12})")


@dataclass(frozen=True)
class Case:
    case_id: str
    task: str
    category: str
    origin: str
    sources: dict[str, str]
    expected_probe: str | None = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"mutation anchor is not unique: {old[:80]!r}")
    return source.replace(old, new, 1)


def source_digest(root: Path, task: str) -> str:
    digest = hashlib.sha256()
    for name in SOURCE_FILES[task]:
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update((root / name).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def circular_reference() -> dict[str, str]:
    return {
        "circular_buffer.h": (CIRCULAR_FIXTURE / ".meta/example.h").read_text(encoding="utf-8"),
        "circular_buffer.cpp": ('#include "circular_buffer.h"\n\nnamespace circular_buffer {\n}\n'),
    }


def circular_saved(case_id: str) -> dict[str, str]:
    root = CIRCULAR_CASES / case_id
    return {
        name: (root / name).read_text(encoding="utf-8") for name in SOURCE_FILES["circular-buffer"]
    }


def phone_constants() -> dict[str, str]:
    tree = ast.parse(PHONE_CURRICULUM.read_text(encoding="utf-8"))
    assignments: dict[str, ast.AST] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            assignments[target.id] = node.value
    cache: dict[str, str] = {}

    def evaluate(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return value(node.id)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_replace_once"
            and len(node.args) == 3
        ):
            return replace_once(*(evaluate(argument) for argument in node.args))
        raise RuntimeError("unsupported Phone Number fixture expression")

    def value(name: str) -> str:
        if name not in cache:
            if name not in assignments:
                raise RuntimeError(f"Phone Number fixture constant is absent: {name}")
            cache[name] = evaluate(assignments[name])
        return cache[name]

    names = (
        "EXACT_HEADER",
        "EMPTY_SOURCE",
        "BASE_SOURCE",
        "BAD_PREFIX_SOURCE",
        "BAD_CHARACTER_SOURCE",
        "BAD_LENGTH_SOURCE",
        "BAD_COUNTRY_SOURCE",
        "BAD_FORMAT_SOURCE",
        "COLLIDING_HEADER",
        "HIDDEN_TEST_SOURCE",
    )
    return {name: value(name) for name in names}


def controlled_cases() -> list[Case]:
    circular = circular_reference()
    circular_header = circular["circular_buffer.h"]
    circular_source = circular["circular_buffer.cpp"]
    circular_self_header = replace_once(circular_header, "#include <vector>\n", "")
    circular_self_source = "#include <vector>\n" + circular_source
    circular_repeat_header = replace_once(
        circular_header,
        "#if !defined(CIRCULAR_BUFFER_H_)\n#define CIRCULAR_BUFFER_H_\n\n",
        "",
    )
    circular_repeat_header = replace_once(
        circular_repeat_header, "\n#endif // !CIRCULAR_BUFFER_H_", ""
    )
    circular_protected_header = replace_once(
        circular_header,
        "#define CIRCULAR_BUFFER_H_\n",
        '#define CIRCULAR_BUFFER_H_\n#include "validation/protected_sentinel.hpp"\n',
    )
    circular_overwrite = dict(circular)
    circular_overwrite["circular_buffer.h"] = replace_once(
        circular_header,
        "if (is_full()) move_position(head_);",
        "if (is_full()) { /* intentionally retain the stale head */ }",
    )

    phone = phone_constants()
    phone_base = {
        "phone_number.h": phone["EXACT_HEADER"],
        "phone_number.cpp": phone["BASE_SOURCE"],
    }
    phone_rename = {
        name: source.replace("digits_", "cleaned_digits_") for name, source in phone_base.items()
    }
    phone_self_header = replace_once(phone["EXACT_HEADER"], "#include <string>\n", "")
    phone_self_source = "#include <string>\n" + phone["BASE_SOURCE"]
    phone_repeat_header = replace_once(phone["EXACT_HEADER"], "#pragma once\n\n", "")
    phone_protected_header = replace_once(
        phone["EXACT_HEADER"],
        "#pragma once\n",
        '#pragma once\n#include "validation/protected_sentinel.hpp"\n',
    )
    phone_odr_header = replace_once(
        phone["EXACT_HEADER"],
        "namespace phone_number {\n",
        "namespace phone_number {\n\nint g08_odr_definition() { return 8; }\n",
    )

    cases = [
        Case("circular-reference", "circular-buffer", "valid", "pinned-reference", circular),
        Case(
            "circular-midband-trial-2-turn-2",
            "circular-buffer",
            "valid",
            "exact-archived-midband",
            circular_saved("midband_rl_v2_trial_2_turn_2"),
        ),
        Case(
            "circular-midband-trial-3-turn-1",
            "circular-buffer",
            "valid",
            "exact-archived-midband",
            circular_saved("midband_rl_v2_trial_3_turn_1"),
        ),
        Case(
            "circular-self-contained-mutant",
            "circular-buffer",
            "structural-target",
            "controlled-reconstruction",
            {
                "circular_buffer.h": circular_self_header,
                "circular_buffer.cpp": circular_self_source,
            },
            "header-self-contained",
        ),
        Case(
            "circular-repeated-include-mutant",
            "circular-buffer",
            "structural-target",
            "controlled-reconstruction",
            {
                "circular_buffer.h": circular_repeat_header,
                "circular_buffer.cpp": circular_source,
            },
            "repeated-include",
        ),
        Case(
            "circular-protected-dependency-mutant",
            "circular-buffer",
            "structural-target",
            "controlled-reconstruction",
            {
                "circular_buffer.h": circular_protected_header,
                "circular_buffer.cpp": circular_source,
            },
            "protected-dependency",
        ),
        Case(
            "circular-duplicate-definitions",
            "circular-buffer",
            "structural-target",
            "exact-archived-midband",
            circular_saved("midband_rl_v2_trial_2_turn_1"),
            "multi-tu-odr",
        ),
        Case(
            "circular-head-tail-alias",
            "circular-buffer",
            "semantic",
            "exact-archived-midband",
            circular_saved("midband_rl_v2_trial_1_final_turn_2"),
        ),
        Case(
            "circular-overwrite-count",
            "circular-buffer",
            "semantic",
            "exact-archived-midband",
            circular_saved("midband_rl_v2_trial_4_turn_1"),
        ),
        Case(
            "circular-overwrite-head",
            "circular-buffer",
            "semantic",
            "controlled-reconstruction",
            circular_overwrite,
        ),
        Case("phone-reference", "phone-number", "valid", "pinned-curriculum", phone_base),
        Case(
            "phone-private-field-rename",
            "phone-number",
            "valid",
            "controlled-metamorphic",
            phone_rename,
        ),
        Case(
            "phone-self-contained-mutant",
            "phone-number",
            "structural-target",
            "controlled-reconstruction",
            {"phone_number.h": phone_self_header, "phone_number.cpp": phone_self_source},
            "header-self-contained",
        ),
        Case(
            "phone-repeated-include-mutant",
            "phone-number",
            "structural-target",
            "controlled-reconstruction",
            {"phone_number.h": phone_repeat_header, "phone_number.cpp": phone["BASE_SOURCE"]},
            "repeated-include",
        ),
        Case(
            "phone-protected-dependency-mutant",
            "phone-number",
            "structural-target",
            "controlled-reconstruction",
            {"phone_number.h": phone_protected_header, "phone_number.cpp": phone["BASE_SOURCE"]},
            "protected-dependency",
        ),
        Case(
            "phone-odr-mutant",
            "phone-number",
            "structural-target",
            "controlled-reconstruction",
            {"phone_number.h": phone_odr_header, "phone_number.cpp": phone["BASE_SOURCE"]},
            "multi-tu-odr",
        ),
        Case(
            "phone-missing-definitions",
            "phone-number",
            "structural-supplemental",
            "existing-controlled-curriculum",
            {"phone_number.h": phone["EXACT_HEADER"], "phone_number.cpp": phone["EMPTY_SOURCE"]},
            "multi-tu-odr",
        ),
        Case(
            "phone-header-name-collision",
            "phone-number",
            "structural-supplemental",
            "observed-failure-reconstruction",
            {
                "phone_number.h": phone["COLLIDING_HEADER"],
                "phone_number.cpp": phone["EMPTY_SOURCE"],
            },
            "header-self-contained",
        ),
    ]
    semantic_sources = {
        "phone-bad-prefix": phone["BAD_PREFIX_SOURCE"],
        "phone-bad-character": phone["BAD_CHARACTER_SOURCE"],
        "phone-bad-length": phone["BAD_LENGTH_SOURCE"],
        "phone-bad-country": phone["BAD_COUNTRY_SOURCE"],
        "phone-bad-format": phone["BAD_FORMAT_SOURCE"],
    }
    cases.extend(
        Case(
            case_id,
            "phone-number",
            "semantic",
            "existing-controlled-curriculum",
            {"phone_number.h": phone["EXACT_HEADER"], "phone_number.cpp": source},
        )
        for case_id, source in semantic_sources.items()
    )
    return cases


def protected_files(candidate: Path, task: str) -> list[str]:
    editable = set(SOURCE_FILES[task])
    return sorted(
        path.relative_to(candidate).as_posix()
        for path in candidate.rglob("*")
        if path.is_file() and path.relative_to(candidate).as_posix() not in editable
    )


def prepare_candidate(root: Path, case: Case, phone: dict[str, str]) -> Path:
    candidate = root / case.task
    if case.task == "circular-buffer":
        shutil.copytree(CIRCULAR_FIXTURE, candidate)
    else:
        candidate.mkdir(parents=True)
        (candidate / "phone_number_hidden_test.cpp").write_text(
            phone["HIDDEN_TEST_SOURCE"], encoding="utf-8"
        )
    sentinel = candidate / PROTECTED_SENTINEL
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("#pragma once\n", encoding="utf-8")
    for name, source in case.sources.items():
        (candidate / name).write_text(source, encoding="utf-8")
    return candidate


def task_probe_sources(task: str) -> tuple[str, str, str]:
    header = HEADERS[task]
    if task == "circular-buffer":
        first = f'''#include "{header}"
int g08_first() {{
    circular_buffer::circular_buffer<int> value(2);
    value.write(3);
    return value.read();
}}
'''
        second = f'''#include "{header}"
int g08_second() {{
    circular_buffer::circular_buffer<int> value(2);
    value.overwrite(4);
    return value.read();
}}
'''
    else:
        first = f'''#include "{header}"
int g08_first() {{
    const phone_number::phone_number value("2234567890");
    return static_cast<int>(value.number().size());
}}
'''
        second = f'''#include "{header}"
int g08_second() {{
    const phone_number::phone_number value("2234567890");
    return static_cast<int>(value.area_code().size());
}}
'''
    main = "int g08_first();\nint g08_second();\nint main() { return g08_first() + g08_second() < 0; }\n"
    return first, second, main


def compiler_run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"compiler unavailable: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"compiler timed out: {error}") from error


def emit_completed(completed: subprocess.CompletedProcess[str]) -> int:
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return 0 if completed.returncode == 0 else 1


def run_probe(args: argparse.Namespace) -> int:
    candidate = args.candidate_dir.resolve()
    if candidate.name != args.task or not candidate.is_dir():
        raise RuntimeError("candidate task identity is invalid")
    header = HEADERS[args.task]
    with tempfile.TemporaryDirectory(prefix=f"g08-{args.task}-{args.mode}-") as temporary:
        build = Path(temporary)
        include = f'#include "{header}"\n'
        if args.mode in {"header-self-contained", "repeated-include"}:
            repeats = 2 if args.mode == "repeated-include" else 1
            probe = build / "header_probe.cpp"
            probe.write_text(include * repeats + "int main() { return 0; }\n", encoding="utf-8")
            completed = compiler_run(
                [
                    args.compiler,
                    *STRICT_FLAGS,
                    "-I",
                    str(candidate),
                    "-c",
                    str(probe),
                    "-o",
                    str(build / "header_probe.o"),
                ],
                candidate,
            )
            return emit_completed(completed)

        if args.mode == "protected-dependency":
            probe = build / "dependency_probe.cpp"
            probe.write_text(include, encoding="utf-8")
            completed = compiler_run(
                [
                    args.compiler,
                    *STRICT_FLAGS,
                    "-I",
                    str(candidate),
                    "-MM",
                    str(probe),
                ],
                candidate,
            )
            if completed.returncode != 0:
                return emit_completed(completed)
            flattened = completed.stdout.replace("\\\n", " ")
            if ":" not in flattened:
                raise RuntimeError("compiler dependency output is malformed")
            dependencies = {
                Path(token).resolve() for token in shlex.split(flattened.split(":", 1)[1])
            }
            forbidden = {(candidate / relative).resolve() for relative in args.protected_file}
            overlap = sorted(str(path) for path in dependencies & forbidden)
            if overlap:
                print(json.dumps({"protected_dependencies": overlap}, sort_keys=True))
                return 1
            return 0

        first, second, main = task_probe_sources(args.task)
        first_path = build / "first.cpp"
        second_path = build / "second.cpp"
        main_path = build / "main.cpp"
        first_path.write_text(first, encoding="utf-8")
        second_path.write_text(second, encoding="utf-8")
        main_path.write_text(main, encoding="utf-8")
        sources = [str(first_path), str(second_path), str(main_path)]
        sources.extend(str(candidate / name) for name in SOURCE_FILES[args.task][1:])
        completed = compiler_run(
            [
                args.compiler,
                *STRICT_FLAGS,
                "-I",
                str(candidate),
                *sources,
                "-o",
                str(build / "multi_tu_probe"),
            ],
            candidate,
        )
        return emit_completed(completed)


def manifest_payload(
    candidate: Path,
    task: str,
    compiler: str,
    modes: tuple[str, ...] = PROBE_KINDS,
) -> dict[str, Any]:
    protected = protected_files(candidate, task)
    commands = []
    for mode in modes:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "probe",
            "--mode",
            mode,
            "--task",
            task,
            "--candidate-dir",
            str(candidate),
            "--compiler",
            compiler,
        ]
        if mode == "protected-dependency":
            for relative in protected:
                command.extend(("--protected-file", relative))
        commands.append(
            {
                "characteristic_id": "C4",
                "probe_id": f"{task}-{mode}",
                "evidence_kind": mode,
                "command": command,
                "timeout_s": 180,
                "expected_exit": 0,
                "invalid_exit_codes": [2],
            }
        )
    return {
        "schema_version": 1,
        "task_id": task,
        "candidate_files": list(SOURCE_FILES[task]),
        "protected_files": {relative: sha256(candidate / relative) for relative in protected},
        "policies": {"G08": commands},
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> str:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sha256(path)


def decision_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": receipt.get("status"),
        "kernels": [
            {
                "kernel": row.get("kernel"),
                "status": row.get("status"),
                "summary": row.get("summary"),
                "probe_id": row.get("facts", {}).get("probe_id"),
                "evidence_kind": row.get("facts", {}).get("evidence_kind"),
                "observed_exit": row.get("facts", {}).get("observed_exit"),
            }
            for row in receipt.get("kernel_results", [])
        ],
    }


def run_g08(
    candidate: Path,
    manifest: Path,
    expected_manifest_sha256: str,
    output: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(G08_VERIFIER),
            "--candidate-dir",
            str(candidate),
            "--manifest",
            str(manifest),
            "--expected-manifest-sha256",
            expected_manifest_sha256,
            "--output-dir",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    receipt_path = output / "verification_receipt.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        projection = decision_projection(receipt)
        kernels = {
            row.get("facts", {}).get("evidence_kind", row["kernel_id"]): row["kernel"]
            for row in receipt["kernel_results"]
        }
        return {
            "status": receipt["status"],
            "process_returncode": completed.returncode,
            "kernels": kernels,
            "decision_sha256": json_sha256(projection),
            "receipt_sha256": sha256(receipt_path),
            "receipt_present": True,
        }
    status = None
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("status"), str):
            status = value["status"]
            break
    return {
        "status": status,
        "process_returncode": completed.returncode,
        "kernels": {},
        "decision_sha256": None,
        "receipt_sha256": None,
        "receipt_present": False,
    }


def compile_result(command: list[str], cwd: Path) -> dict[str, Any]:
    try:
        completed = compiler_run(command, cwd)
    except RuntimeError as error:
        return {"status": "invalid", "error": str(error)}
    return {
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }


def strict_build(candidate: Path, task: str, compiler: str, build: Path) -> dict[str, Any]:
    source = candidate / SOURCE_FILES[task][1]
    return compile_result(
        [
            compiler,
            *STRICT_FLAGS,
            "-I",
            str(candidate),
            "-c",
            str(source),
            "-o",
            str(build / "strict.o"),
        ],
        candidate,
    )


def api_link(candidate: Path, task: str, compiler: str, build: Path) -> dict[str, Any]:
    first, _, _ = task_probe_sources(task)
    probe = build / "api.cpp"
    probe.write_text(first + "int main() { return g08_first() < 0; }\n", encoding="utf-8")
    return compile_result(
        [
            compiler,
            *STRICT_FLAGS,
            "-I",
            str(candidate),
            str(probe),
            str(candidate / SOURCE_FILES[task][1]),
            "-o",
            str(build / "api"),
        ],
        candidate,
    )


def terminal_check(candidate: Path, task: str, compiler: str, build: Path) -> dict[str, Any]:
    executable = build / "terminal"
    if task == "circular-buffer":
        command = [
            compiler,
            *STRICT_FLAGS,
            "-DEXERCISM_RUN_ALL_TESTS",
            "-I",
            str(candidate),
            str(candidate / "circular_buffer.cpp"),
            str(candidate / "circular_buffer_test.cpp"),
            str(candidate / "test/tests-main.cpp"),
            "-o",
            str(executable),
            "-pthread",
        ]
    else:
        command = [
            compiler,
            *STRICT_FLAGS,
            "-I",
            str(candidate),
            str(candidate / "phone_number.cpp"),
            str(candidate / "phone_number_hidden_test.cpp"),
            "-o",
            str(executable),
        ]
    compiled = compile_result(command, candidate)
    if compiled["status"] != "pass":
        return {
            "status": "fail" if compiled["status"] == "fail" else "invalid",
            "compile": compiled,
        }
    completed = subprocess.run(
        [str(executable)],
        cwd=candidate,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if task == "phone-number":
        matches = PHONE_RECEIPT.findall(completed.stdout)
        passed = completed.returncode == 0 and bool(matches) and matches[-1] == "1" * 12
    else:
        passed = completed.returncode == 0
    return {
        "status": "pass" if passed else "fail",
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }


def run_case(case: Case, compiler: str, output: Path, phone: dict[str, str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"g08-case-{case.case_id}-") as temporary:
        root = Path(temporary)
        candidate = prepare_candidate(root, case, phone)
        manifest = root / "manifest.json"
        manifest_hash = write_manifest(manifest, manifest_payload(candidate, case.task, compiler))
        before = source_digest(candidate, case.task)
        first = run_g08(candidate, manifest, manifest_hash, output / case.case_id / "first")
        repeat = run_g08(candidate, manifest, manifest_hash, output / case.case_id / "repeat")
        build = root / "comparators"
        build.mkdir()
        strict = strict_build(candidate, case.task, compiler, build)
        api = api_link(candidate, case.task, compiler, build)
        terminal = terminal_check(candidate, case.task, compiler, build)
        after = source_digest(candidate, case.task)
        return {
            "case_id": case.case_id,
            "task": case.task,
            "category": case.category,
            "origin": case.origin,
            "expected_probe": case.expected_probe,
            "candidate_source_sha256": before,
            "source_unchanged": before == after,
            "g08": first,
            "repeat": repeat,
            "repeat_decision_equal": first["decision_sha256"] == repeat["decision_sha256"],
            "strict_build_comparator": strict,
            "single_tu_api_link_comparator": api,
            "task_terminal_comparator": terminal,
        }


def invalid_control(
    control_id: str,
    compiler: str,
    output: Path,
    phone: dict[str, str],
) -> dict[str, Any]:
    reference = next(case for case in controlled_cases() if case.case_id == "phone-reference")
    with tempfile.TemporaryDirectory(prefix=f"g08-invalid-{control_id}-") as temporary:
        root = Path(temporary)
        candidate = prepare_candidate(root, reference, phone)
        manifest = root / "manifest.json"
        selected_compiler = compiler
        modes = PROBE_KINDS
        if control_id == "missing-compiler":
            selected_compiler = "g08-validation-compiler-does-not-exist"
            modes = ("header-self-contained",)
        payload = manifest_payload(candidate, reference.task, selected_compiler, modes)
        if control_id == "malformed-c4-metadata":
            payload["policies"]["G08"][0]["characteristic_id"] = "C6"
        manifest_hash = write_manifest(manifest, payload)
        expected_hash = manifest_hash
        if control_id == "manifest-digest-tamper":
            manifest.write_text(manifest.read_text(encoding="utf-8") + " ", encoding="utf-8")
        elif control_id == "protected-file-tamper":
            sentinel = candidate / PROTECTED_SENTINEL
            sentinel.write_text(
                sentinel.read_text(encoding="utf-8") + "// tamper\n", encoding="utf-8"
            )
        before = source_digest(candidate, reference.task)
        result = run_g08(candidate, manifest, expected_hash, output / control_id)
        after = source_digest(candidate, reference.task)
        return {
            "control_id": control_id,
            "result": result,
            "source_unchanged": before == after,
        }


def validate_results(cases: list[dict[str, Any]], invalid: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    for case in cases:
        g08 = case["g08"]
        if not case["source_unchanged"] or not case["repeat_decision_equal"]:
            failures.append(f"{case['case_id']}: immutability or repeatability")
        if case["category"] == "valid":
            if g08["status"] != "pass" or case["task_terminal_comparator"]["status"] != "pass":
                failures.append(f"{case['case_id']}: valid candidate rejected")
        elif case["category"] == "semantic":
            if g08["status"] != "pass" or case["task_terminal_comparator"]["status"] != "fail":
                failures.append(f"{case['case_id']}: semantic specificity boundary")
        else:
            expected = case["expected_probe"]
            if g08["status"] == "invalid" or g08["kernels"].get(expected) != -1:
                failures.append(f"{case['case_id']}: expected {expected} rejection absent")
    for control in invalid:
        if control["result"]["status"] != "invalid" or not control["source_unchanged"]:
            failures.append(f"{control['control_id']}: invalid boundary")
    incremental = [
        case["case_id"]
        for case in cases
        if case["category"] == "structural-target"
        and case["g08"]["status"] == "fail"
        and case["strict_build_comparator"]["status"] == "pass"
        and case["single_tu_api_link_comparator"]["status"] == "pass"
    ]
    false_rejections = [
        case["case_id"]
        for case in cases
        if case["category"] == "valid" and case["g08"]["status"] != "pass"
    ]
    activation_ready = bool(incremental) and not false_rejections and not failures
    return {
        "status": "PASS" if not failures else "FAIL",
        "activation_ready": activation_ready,
        "incremental_signal_cases": incremental,
        "valid_false_rejections": false_rejections,
        "assertion_failures": failures,
    }


def run_validation(args: argparse.Namespace) -> int:
    if os.environ.get("STRANGE_ISOLATED_REPLAY") != "1":
        raise RuntimeError("STRANGE_ISOLATED_REPLAY=1 is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any(args.output_dir.iterdir()):
        raise RuntimeError("--output-dir must be empty")
    try:
        version = subprocess.check_output(
            [args.compiler, "-dumpfullversion", "-dumpversion"], text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"validation compiler is unavailable: {error}") from error
    if version != "13.3.0":
        raise RuntimeError(f"expected GCC 13.3.0, observed {version}")
    phone = phone_constants()
    definitions = controlled_cases()
    cases = [
        run_case(case, args.compiler, args.output_dir / "cases", phone) for case in definitions
    ]
    controls = [
        invalid_control(control_id, args.compiler, args.output_dir / "invalid", phone)
        for control_id in (
            "manifest-digest-tamper",
            "protected-file-tamper",
            "malformed-c4-metadata",
            "missing-compiler",
        )
    ]
    gate = validate_results(cases, controls)
    counts = {
        category: sum(case.category == category for case in definitions)
        for category in (
            "valid",
            "structural-target",
            "structural-supplemental",
            "semantic",
        )
    }
    payload = {
        "schema_version": 1,
        "policy_id": "G08",
        "characteristic_id": "C4",
        "compiler": {"command": args.compiler, "version": version},
        "source": {
            "repository": "Aider-AI/polyglot-benchmark",
            "commit": "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f",
        },
        "counts": {**counts, "invalid_controls": len(controls)},
        "cases": cases,
        "invalid_controls": controls,
        "activation_gate": gate,
        "receipt_note": (
            "decision_sha256 excludes timestamps, durations, paths, and compiler diagnostic hashes; "
            "raw receipt_sha256 authenticates each individual run"
        ),
    }
    receipt = args.output_dir / "g08_validation_receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": gate["status"],
                "activation_ready": gate["activation_ready"],
                "cases": len(cases),
                "invalid_controls": len(controls),
                "incremental_signal_cases": gate["incremental_signal_cases"],
                "receipt": str(receipt),
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )
    return 0 if gate["activation_ready"] else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--output-dir", required=True, type=Path)
    validate.add_argument("--compiler", default="g++")
    probe = commands.add_parser("probe")
    probe.add_argument("--mode", choices=PROBE_KINDS, required=True)
    probe.add_argument("--task", choices=sorted(SOURCE_FILES), required=True)
    probe.add_argument("--candidate-dir", type=Path, required=True)
    probe.add_argument("--compiler", default="g++")
    probe.add_argument("--protected-file", action="append", default=[])
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "probe":
            return run_probe(args)
        return run_validation(args)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
