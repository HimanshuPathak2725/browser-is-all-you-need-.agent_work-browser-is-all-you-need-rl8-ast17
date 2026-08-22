from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "CL2-C05"
REPEATED_INCLUDE = '#include "clock.h"\n#include "clock.h"\nint main() { return 0; }\n'
HELPER = r'''#include "clock.h"
#include <string>
std::string helper_render(int hour, int minute) {
    return static_cast<std::string>(date_independent::clock::at(hour, minute));
}
bool helper_unequal(const date_independent::clock& lhs, const date_independent::clock& rhs) {
    return lhs != rhs;
}
'''
MAIN = r'''#include "clock.h"
#include <iostream>
#include <string>
std::string helper_render(int, int);
bool helper_unequal(const date_independent::clock&, const date_independent::clock&);
int main() {
    const auto first = date_independent::clock::at(1, 0);
    const auto second = date_independent::clock::at(2, 0);
    const bool unequal = helper_unequal(first, second);
    const std::string rendered = helper_render(8, 3);
    if (rendered.empty()) return 1;
    (void)unequal;
    std::cout << "odr-link-ok\n";
}
'''
OPERATOR_HELPER = r'''#include "clock.h"
bool compare_elsewhere(const date_independent::clock& lhs, const date_independent::clock& rhs) {
    return lhs != rhs;
}
'''
OPERATOR_MAIN = r'''#include "clock.h"
#include <iostream>
bool compare_elsewhere(const date_independent::clock&, const date_independent::clock&);
int main() {
    std::cout << (compare_elsewhere(date_independent::clock::at(0), date_independent::clock::at(0)) ? "bad" : "ok") << '\n';
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CL2-C05-A", "repeated_header_include", "repeated_include.cpp", REPEATED_INCLUDE),
        compile_multi_tu_and_run(ctx, "CL2-C05-B", "two_caller_link", {"odr_helper.cpp": HELPER, "odr_main.cpp": MAIN}, "odr-link-ok\n"),
        compile_multi_tu_and_run(ctx, "CL2-C05-C", "cross_tu_inequality", {"operator_helper.cpp": OPERATOR_HELPER, "operator_main.cpp": OPERATOR_MAIN}, "ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
