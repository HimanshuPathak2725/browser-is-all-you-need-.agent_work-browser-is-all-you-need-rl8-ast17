from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "CLF-C03"
REPEATED_INCLUDE = '#include "clock.h"\n#include "clock.h"\nint main() { return 0; }\n'
HELPER = r'''#include "clock.h"
#include <string>
std::string render_elsewhere(int hour, int minute) {
    return static_cast<std::string>(date_independent::clock::at(hour, minute));
}
bool unequal_elsewhere(const date_independent::clock& lhs, const date_independent::clock& rhs) {
    return lhs != rhs;
}
'''
MAIN = r'''#include "clock.h"
#include <iostream>
#include <string>
std::string render_elsewhere(int, int);
bool unequal_elsewhere(const date_independent::clock&, const date_independent::clock&);
int main() {
    const auto first = date_independent::clock::at(8);
    const auto second = date_independent::clock::at(8, 1);
    if (render_elsewhere(8, 3) != "08:03" || !unequal_elsewhere(first, second)) return 1;
    std::cout << "multi-tu-ok\n";
}
'''
STATE_ISOLATION = r'''#include "clock.h"
#include <iostream>
#include <string>
using Clock = date_independent::clock;
int main() {
    auto first = Clock::at(1, 0);
    auto second = Clock::at(2, 0);
    first.plus(60);
    if (!(first == second) || static_cast<std::string>(second) != "02:00") return 1;
    const auto observed = Clock::at(8, 3);
    const std::string before = static_cast<std::string>(observed);
    const std::string after = static_cast<std::string>(observed);
    if (before != "08:03" || after != before) return 2;
    std::cout << "isolation-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CLF-C03-A", "idempotent_header_include", "repeated_include.cpp", REPEATED_INCLUDE),
        compile_multi_tu_and_run(ctx, "CLF-C03-B", "multi_tu_odr_surface", {"helper.cpp": HELPER, "main.cpp": MAIN}, "multi-tu-ok\n"),
        compile_and_run(ctx, "CLF-C03-C", "factory_state_isolation", "state_isolation.cpp", STATE_ISOLATION, "isolation-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
