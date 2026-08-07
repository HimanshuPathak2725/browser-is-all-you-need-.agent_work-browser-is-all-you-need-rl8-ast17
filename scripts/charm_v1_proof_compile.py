"""Isolated header and alternate-compiler proof helpers for CHARM V1."""

from __future__ import annotations

import shlex
from pathlib import Path

from glm47_posttraining.aider_polyglot.harness import _run_stage


def compile_proofs(
    *,
    workspace: Path,
    root: Path,
    editable: list[str],
    reference: dict[str, str],
    hidden_name: str,
    primary_image: str,
    gcc_image: str,
    clang_image: str,
    reference_syntax_passed: bool,
) -> dict[str, object]:
    for name, contents in reference.items():
        (workspace / name).write_text(contents, encoding="utf-8")
    headers = sorted(
        path.name for path in workspace.iterdir()
        if path.is_file() and path.suffix in {".h", ".hpp"}
    )
    if headers:
        probe = workspace / ".grader/header_isolation.cpp"
        probe.write_text(
            "".join(f'#include "{name}"\n' for name in headers),
            encoding="utf-8",
        )
        isolated = _run_stage(
            workspace,
            "timeout 30s c++ -std=c++17 -Wall -Wextra -Werror -pedantic "
            "-pthread -I. -fsyntax-only .grader/header_isolation.cpp",
            image=primary_image,
            timeout_s=40,
        )
        header_ok = isolated.returncode == 0
    else:
        header_ok = reference_syntax_passed

    hidden_text = (root / hidden_name).read_text(encoding="utf-8")
    (workspace / hidden_name).write_text(hidden_text, encoding="utf-8")
    cpp_files = [name for name in editable if Path(name).suffix in {".cpp", ".cc"}]
    included_cpp = {name for name in cpp_files if f'#include "{name}"' in hidden_text}
    sources = [*sorted(name for name in cpp_files if name not in included_cpp), hidden_name]
    quoted = " ".join(shlex.quote(name) for name in sources)
    alternate_image = gcc_image if primary_image == clang_image else clang_image
    portability = _run_stage(
        workspace,
        "timeout 45s c++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic "
        f"-pthread -I. {quoted} -o .grader/portability_test && "
        "timeout 15s .grader/portability_test",
        image=alternate_image,
        timeout_s=70,
    )
    return {
        "header_isolation_passed": header_ok,
        "grader_portability_passed": portability.returncode == 0,
        "alternate_compiler_image": alternate_image,
    }
