from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "CL2-C02"
HEADER_FIRST = r'''#include "clock.h"
#include <string>
int main() {
    const auto value = date_independent::clock::at(0);
    const std::string rendered = static_cast<std::string>(value);
    return rendered.empty();
}
'''
FORMAT_CALLER = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    const std::string rendered = static_cast<std::string>(date_independent::clock::at(8, 3));
    if (rendered.empty()) return 1;
    std::cout << "dependency-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CL2-C02-A", "header_included_first", "header_first.cpp", HEADER_FIRST),
        compile_implementation_only(ctx, "CL2-C02-B", "declared_dependencies"),
        compile_and_run(ctx, "CL2-C02-C", "format_dependency_link", "format_dependency.cpp", FORMAT_CALLER, "dependency-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
