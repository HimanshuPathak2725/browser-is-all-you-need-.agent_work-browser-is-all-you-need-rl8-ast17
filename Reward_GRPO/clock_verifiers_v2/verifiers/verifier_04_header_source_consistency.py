from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "CL2-C04"
FACTORY_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    auto value = date_independent::clock::at(10, 3);
    value.plus(61).minus(61);
    const std::string rendered = static_cast<std::string>(value);
    if (rendered.empty()) return 1;
    std::cout << "factory-link-ok\n";
}
'''
SURFACE_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    auto first = date_independent::clock::at(-1, 0);
    const auto second = date_independent::clock::at(23, 0);
    first.plus(1441).minus(1441);
    const bool equal = first == second;
    const bool unequal = first != second;
    const std::string rendered = static_cast<std::string>(first);
    if (rendered.empty()) return 1;
    (void)equal;
    (void)unequal;
    std::cout << "surface-link-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_implementation_only(ctx, "CL2-C04-A", "implementation_declarations"),
        compile_and_run(ctx, "CL2-C04-B", "external_factory_arithmetic", "external_factory.cpp", FACTORY_PROBE, "factory-link-ok\n"),
        compile_and_run(ctx, "CL2-C04-C", "complete_public_surface", "complete_surface.cpp", SURFACE_PROBE, "surface-link-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
