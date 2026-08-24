from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute
from strange_cpp import failed, invalid, passed, source_unchanged

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "DNF-C01"
HEADER_PROBE = r"""#include "dnd_character.h"
#if __cplusplus != 201703L
#error D&D Character verifier requires exact C++17 mode
#endif
int main() { return 0; }
"""
LINK_PROBE = r"""#include "dnd_character.h"
#include <iostream>
int main() {
    const dnd_character::Character value;
    if (dnd_character::modifier(3) != -4) return 1;
    if (value.hitpoints != 10 + dnd_character::modifier(value.constitution)) return 2;
    std::cout << "build-ok\n";
}
"""


def protected_dependency_check(ctx: Context) -> KernelReceipt:
    forbidden = (
        ".meta/example",
        ".meta\\example",
        "../.meta",
        'example.cpp"',
        "test/catch.hpp",
        "tests-main.cpp",
        "dnd_character_test.cpp",
        "dnd_character_hidden_test.cpp",
    )
    matches: dict[str, list[str]] = {}
    for relative in ctx.contract.source_files:
        text = (ctx.exercise_dir / relative).read_text(encoding="utf-8", errors="replace")
        found = [token for token in forbidden if token in text]
        if found:
            matches[relative] = found
    facts = {"forbidden_reference_matches": matches}
    if not source_unchanged(ctx):
        return invalid(
            "DNF-C01-D", "candidate source changed during dependency inspection", facts=facts
        )
    if matches:
        return failed(
            "DNF-C01-D", "candidate source references hidden or protected task assets", facts=facts
        )
    return passed(
        "DNF-C01-D",
        "candidate source is independent of hidden and protected task assets",
        facts=facts,
    )


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(
            ctx, "DNF-C01-A", "self_contained_cxx17_header", "header_first.cpp", HEADER_PROBE
        ),
        compile_implementation_only(ctx, "DNF-C01-B", "strict_warning_clean_implementation"),
        compile_and_run(
            ctx, "DNF-C01-C", "external_compile_link", "external_link.cpp", LINK_PROBE, "build-ok\n"
        ),
        protected_dependency_check(ctx),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
