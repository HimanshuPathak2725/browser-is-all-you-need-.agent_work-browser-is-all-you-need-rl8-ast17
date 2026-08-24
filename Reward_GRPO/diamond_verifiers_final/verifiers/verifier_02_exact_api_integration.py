from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "DMF-C02"
EXACT_API = r'''#include "diamond.h"
#include <string>
#include <type_traits>
#include <vector>
using Rows = std::vector<std::string> (*)(char);
static_assert(std::is_same_v<decltype(&diamond::rows), Rows>);
int main() {
    const Rows rows = &diamond::rows;
    (void)rows;
    return 0;
}
'''
REPEATED_INCLUDE = '#include "diamond.h"\n#include "diamond.h"\nint main() { return 0; }\n'
HELPER = r'''#include "diamond.h"
#include <string>
#include <vector>
std::vector<std::string> rows_elsewhere(char letter) { return diamond::rows(letter); }
'''
MAIN = r'''#include "diamond.h"
#include <iostream>
#include <string>
#include <vector>
std::vector<std::string> rows_elsewhere(char);
int main() {
    if (diamond::rows('A').empty()) return 1;
    if (rows_elsewhere('C').empty()) return 2;
    std::cout << "integration-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "DMF-C02-A", "exact_function_type", "exact_api.cpp", EXACT_API),
        compile_only(ctx, "DMF-C02-B", "idempotent_header_include", "repeated_include.cpp", REPEATED_INCLUDE),
        compile_multi_tu_and_run(
            ctx,
            "DMF-C02-C",
            "multi_tu_odr_surface",
            {"helper.cpp": HELPER, "main.cpp": MAIN},
            "integration-ok\n",
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
