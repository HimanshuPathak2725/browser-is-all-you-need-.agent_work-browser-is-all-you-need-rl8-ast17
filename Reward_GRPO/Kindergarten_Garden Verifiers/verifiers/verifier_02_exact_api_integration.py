from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "KGF-C02"
EXACT_API = r'''#include "kindergarten_garden.h"
#include <array>
#include <string_view>
#include <type_traits>
using P = kindergarten_garden::Plants;
using Signature = std::array<P, 4> (*)(std::string_view, std::string_view);
static_assert(std::is_enum_v<P>);
static_assert(std::is_same_v<std::underlying_type_t<P>, char>);
static_assert(static_cast<char>(P::grass) == 'G');
static_assert(static_cast<char>(P::clover) == 'C');
static_assert(static_cast<char>(P::radishes) == 'R');
static_assert(static_cast<char>(P::violets) == 'V');
static_assert(std::is_same_v<decltype(&kindergarten_garden::plants), Signature>);
int main() { return 0; }
'''
REPEATED_INCLUDE = '#include "kindergarten_garden.h"\n#include "kindergarten_garden.h"\nint main() { return 0; }\n'
HELPER = r'''#include "kindergarten_garden.h"
#include <array>
kindergarten_garden::Plants observe_elsewhere() {
    const auto result = kindergarten_garden::plants(
        "VRCGVVRVCGGCCGVRGCVCGCGV\nVRCCCGCRRGVCGCRVVCVGCGCV", "Alice");
    return result.at(0);
}
'''
MAIN = r'''#include "kindergarten_garden.h"
#include <iostream>
kindergarten_garden::Plants observe_elsewhere();
int main() {
    (void)observe_elsewhere();
    std::cout << "integration-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "KGF-C02-A", "exact_enum_and_function_type", "exact_api.cpp", EXACT_API),
        compile_only(ctx, "KGF-C02-B", "idempotent_header_include", "repeated_include.cpp", REPEATED_INCLUDE),
        compile_multi_tu_and_run(
            ctx,
            "KGF-C02-C",
            "multi_tu_odr_surface",
            {"helper.cpp": HELPER, "main.cpp": MAIN},
            "integration-ok\n",
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
