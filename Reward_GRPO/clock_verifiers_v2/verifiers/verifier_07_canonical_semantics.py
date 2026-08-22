from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CL2-C07"
WHOLE_DAY_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
using Clock = date_independent::clock;
std::string text(const Clock& value) { return static_cast<std::string>(value); }
int main() {
    const auto zero = Clock::at(0, 0);
    if (text(Clock::at(24, 0)) != "00:00" || text(Clock::at(-24, 0)) != "00:00") return 1;
    if (text(Clock::at(-48, 0)) != "00:00" || !(zero == Clock::at(72, 8640))) return 2;
    if (text(Clock::at(-121, -5810)) != "22:10") return 3;
    std::cout << "whole-day-ok\n";
}
'''
ARITHMETIC_PROBE = r'''#include "clock.h"
#include <iostream>
#include <string>
using Clock = date_independent::clock;
std::string text(const Clock& value) { return static_cast<std::string>(value); }
int main() {
    auto a = Clock::at(23, 59); a.plus(2 + 5 * 1440);
    auto b = Clock::at(0, 1); b.minus(2 + 7 * 1440);
    auto c = Clock::at(12, 34); c.plus(100000).minus(100000);
    auto d = Clock::at(10, 3); d.plus(-70);
    if (text(a) != "00:01" || text(b) != "23:59" || text(c) != "12:34" || text(d) != "08:53") return 1;
    std::cout << "arithmetic-ok\n";
}
'''
EQUALITY_PROBE = r'''#include "clock.h"
#include <iostream>
using Clock = date_independent::clock;
int main() {
    if (!(Clock::at(0, 0) == Clock::at(24, 0))) return 1;
    if (!(Clock::at(22, 40) == Clock::at(-2, 40))) return 2;
    if (!(Clock::at(6, 15) == Clock::at(6, -4305))) return 3;
    if (Clock::at(15, 36) == Clock::at(15, 37)) return 4;
    if (!(Clock::at(15, 36) != Clock::at(15, 37))) return 5;
    std::cout << "equality-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CL2-C07-A", "whole_day_normalization", "whole_day.cpp", WHOLE_DAY_PROBE, "whole-day-ok\n"),
        compile_and_run(ctx, "CL2-C07-B", "signed_arithmetic", "signed_arithmetic.cpp", ARITHMETIC_PROBE, "arithmetic-ok\n"),
        compile_and_run(ctx, "CL2-C07-C", "normalized_equality", "normalized_equality.cpp", EQUALITY_PROBE, "equality-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
