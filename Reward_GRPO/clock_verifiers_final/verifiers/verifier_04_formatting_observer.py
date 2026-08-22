from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CLF-C04"
CANONICAL_FORMAT = r'''#include "clock.h"
#include <iostream>
#include <string>
using Clock = date_independent::clock;
std::string expected(int total) {
    const int hour = total / 60;
    const int minute = total % 60;
    std::string value;
    value += static_cast<char>('0' + hour / 10);
    value += static_cast<char>('0' + hour % 10);
    value += ':';
    value += static_cast<char>('0' + minute / 10);
    value += static_cast<char>('0' + minute % 10);
    return value;
}
int main() {
    for (int total = 0; total < 1440; ++total) {
        const std::string observed = static_cast<std::string>(Clock::at(total / 60, total % 60));
        if (observed != expected(total)) return 1;
    }
    std::cout << "canonical-format-ok\n";
}
'''
SIGNED_FORMAT = r'''#include "clock.h"
#include <array>
#include <iostream>
#include <string>
using Clock = date_independent::clock;
struct Input { int hour; int minute; };
std::string expected(int hour, int minute) {
    long long total = static_cast<long long>(hour) * 60 + minute;
    total %= 1440;
    if (total < 0) total += 1440;
    const int h = static_cast<int>(total / 60);
    const int m = static_cast<int>(total % 60);
    std::string value;
    value += static_cast<char>('0' + h / 10);
    value += static_cast<char>('0' + h % 10);
    value += ':';
    value += static_cast<char>('0' + m / 10);
    value += static_cast<char>('0' + m % 10);
    return value;
}
int main() {
    const std::array<Input, 17> inputs{{
        {0, -1}, {-1, 0}, {-24, 0}, {-48, -1440}, {24, 0}, {48, 1440},
        {25, 160}, {-25, -160}, {100, -3000}, {-121, -5810},
        {-9999, 999999}, {9999, -999999}, {0, 60}, {0, -60}, {23, 59},
        {23, 60}, {-23, -60}
    }};
    for (const auto input : inputs) {
        if (static_cast<std::string>(Clock::at(input.hour, input.minute)) != expected(input.hour, input.minute)) return 1;
    }
    std::cout << "signed-format-ok\n";
}
'''
OBSERVER_STABILITY = r'''#include "clock.h"
#include <array>
#include <cctype>
#include <iostream>
#include <string>
using Clock = date_independent::clock;
int main() {
    const std::array<Clock, 5> values{{Clock::at(0), Clock::at(8, 3), Clock::at(23, 59), Clock::at(-24), Clock::at(100, -3000)}};
    for (const auto& value : values) {
        const std::string first = static_cast<std::string>(value);
        for (int repeat = 0; repeat < 100; ++repeat) {
            const std::string current = static_cast<std::string>(value);
            if (current != first || current.size() != 5 || current[2] != ':') return 1;
            if (!std::isdigit(static_cast<unsigned char>(current[0])) || !std::isdigit(static_cast<unsigned char>(current[1])) ||
                !std::isdigit(static_cast<unsigned char>(current[3])) || !std::isdigit(static_cast<unsigned char>(current[4]))) return 2;
        }
    }
    std::cout << "observer-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CLF-C04-A", "all_canonical_formats", "canonical_format.cpp", CANONICAL_FORMAT, "canonical-format-ok\n"),
        compile_and_run(ctx, "CLF-C04-B", "signed_boundary_formats", "signed_format.cpp", SIGNED_FORMAT, "signed-format-ok\n"),
        compile_and_run(ctx, "CLF-C04-C", "const_observer_stability", "observer_stability.cpp", OBSERVER_STABILITY, "observer-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
