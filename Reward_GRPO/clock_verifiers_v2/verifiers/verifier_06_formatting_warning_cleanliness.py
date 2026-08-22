from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT
from _helpers import compile_implementation_only


POLICY_ID = "CL2-C06"
BOUNDARY_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
using Clock = date_independent::clock;
std::string render(int hour, int minute) { return static_cast<std::string>(Clock::at(hour, minute)); }
int main() {
    if (render(0, 0) != "00:00") return 1;
    if (render(8, 3) != "08:03") return 2;
    if (render(0, -1) != "23:59") return 3;
    if (render(0, 1723) != "04:43") return 4;
    std::cout << "format-ok\n";
}
'''
CONST_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
int main() {
    const auto value = date_independent::clock::at(8, 3);
    const std::string first = static_cast<std::string>(value);
    const std::string second = static_cast<std::string>(value);
    if (first != "08:03" || second != first || first.size() != 5 || first[2] != ':') return 1;
    std::cout << "const-format-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_implementation_only(ctx, "CL2-C06-A", "warning_clean_implementation"),
        compile_and_run(ctx, "CL2-C06-B", "format_boundaries", "format_boundaries.cpp", BOUNDARY_PROBE, "format-ok\n"),
        compile_and_run(ctx, "CL2-C06-C", "const_repeat_format", "const_repeat_format.cpp", CONST_PROBE, "const-format-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
