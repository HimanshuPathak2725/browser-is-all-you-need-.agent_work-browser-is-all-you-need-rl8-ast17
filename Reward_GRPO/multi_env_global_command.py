"""Trusted build/test commands for the generic C++ verifier manifests.

The candidate tree is mounted read-only. This helper derives the official
solution and test file lists from the authenticated Exercism task metadata and
places every build product in a private temporary directory.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


MODES = {"strict-build", "api-link", "official-functional", "safety", "portability"}


def _task_files(root: Path) -> tuple[list[str], list[str]]:
    config = json.loads((root / ".meta" / "config.json").read_text(encoding="utf-8"))
    files = config.get("files")
    if not isinstance(files, dict):
        raise ValueError("official task metadata has no files map")
    solution = files.get("solution")
    tests = files.get("test")
    if not isinstance(solution, list) or not solution or not isinstance(tests, list) or not tests:
        raise ValueError("official task metadata has invalid solution/test lists")
    values = [*solution, *tests, "test/tests-main.cpp"]
    if not all(
        isinstance(value, str) and value and ".." not in Path(value).parts
        for value in values
    ):
        raise ValueError("official task metadata contains an unsafe path")
    for value in values:
        path = root / value
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"authenticated task file is unavailable: {value}")
    return [str(value) for value in solution], [str(value) for value in tests]


def _run(command: list[str], root: Path, *, env: dict[str, str] | None = None) -> None:
    print(json.dumps({"command": command}, sort_keys=True))
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        env={**os.environ, "LC_ALL": "C", "LANG": "C", **(env or {})},
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def execute(mode: str, task: str, root: Path) -> None:
    if mode not in MODES:
        raise ValueError(f"unsupported global verifier mode: {mode}")
    if root.name != task:
        raise ValueError(f"candidate task identity mismatch: expected {task}, got {root.name}")
    solution, tests = _task_files(root)
    sources = [*solution, *tests, "test/tests-main.cpp"]
    link_flags = ["-pthread", *(["-lboost_date_time"] if task == "meetup" else [])]

    with TemporaryDirectory(prefix=f"global-{task}-{mode}-") as temporary:
        build = Path(temporary)
        if mode == "strict-build":
            for index, source in enumerate(solution):
                if Path(source).suffix not in {".cc", ".cpp", ".cxx"}:
                    continue
                _run(
                    [
                        "g++",
                        "-std=c++17",
                        "-Wall",
                        "-Wextra",
                        "-Wpedantic",
                        "-Werror",
                        "-I.",
                        "-c",
                        source,
                        "-o",
                        str(build / f"solution-{index}.o"),
                    ],
                    root,
                )
            return

        compiler = "clang++" if mode == "portability" else "g++"
        executable = build / "official-tests"
        command = [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-DEXERCISM_RUN_ALL_TESTS",
            "-I.",
            *sources,
            "-o",
            str(executable),
            *link_flags,
        ]
        if mode == "safety":
            command[1:1] = [
                "-fsanitize=address,undefined",
                "-fno-omit-frame-pointer",
                "-O1",
            ]
        _run(command, root)
        if mode == "api-link":
            return
        runtime_env = None
        if mode == "safety":
            runtime_env = {
                "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1",
                "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
            }
        _run([str(executable)], root, env=runtime_env)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--candidate-dir", type=Path, default=Path.cwd())
    return parser


if __name__ == "__main__":
    try:
        arguments = _parser().parse_args()
        execute(arguments.mode, arguments.task, arguments.candidate_dir.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)
