from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "CLF-C05"
SANITIZER_FLAGS = ("-fsanitize=undefined", "-fno-sanitize-recover=undefined")
CONSTRUCTION_PROPERTIES = r'''#include "clock.h"
#include <array>
#include <iostream>
using Clock = date_independent::clock;
int main() {
    const std::array<int, 17> hours{{-10000, -1000, -121, -49, -48, -25, -24, -1, 0, 1, 23, 24, 25, 48, 121, 1000, 10000}};
    const std::array<int, 17> minutes{{-1000000, -5810, -3001, -1441, -1440, -61, -60, -1, 0, 1, 59, 60, 61, 1439, 1440, 3001, 1000000}};
    for (const int hour : hours) for (const int minute : minutes) {
        long long total = static_cast<long long>(hour) * 60 + minute;
        total %= 1440;
        if (total < 0) total += 1440;
        const auto expected = Clock::at(static_cast<int>(total / 60), static_cast<int>(total % 60));
        const auto observed = Clock::at(hour, minute);
        if (!(observed == expected) || observed != expected) return 1;
    }
    std::cout << "construction-properties-ok\n";
}
'''
ARITHMETIC_PROPERTIES = r'''#include "clock.h"
#include <array>
#include <iostream>
using Clock = date_independent::clock;
int main() {
    const std::array<int, 9> starts{{-1000, -25, -1, 0, 1, 23, 24, 25, 1000}};
    const std::array<int, 17> deltas{{-1000000, -100001, -10080, -1441, -1440, -61, -1, 0, 1, 61, 1439, 1440, 1441, 10080, 100001, 999999, 1000000}};
    for (const int hour : starts) for (const int delta : deltas) {
        auto plus_value = Clock::at(hour, 37);
        Clock* plus_address = &plus_value;
        Clock& plus_result = plus_value.plus(delta);
        long long plus_total = static_cast<long long>(hour) * 60 + 37 + delta;
        plus_total %= 1440;
        if (plus_total < 0) plus_total += 1440;
        if (&plus_result != plus_address || !(plus_value == Clock::at(static_cast<int>(plus_total / 60), static_cast<int>(plus_total % 60)))) return 1;
        plus_value.minus(delta);
        if (!(plus_value == Clock::at(hour, 37))) return 2;

        auto minus_value = Clock::at(hour, 37);
        Clock* minus_address = &minus_value;
        Clock& minus_result = minus_value.minus(delta);
        long long minus_total = static_cast<long long>(hour) * 60 + 37 - delta;
        minus_total %= 1440;
        if (minus_total < 0) minus_total += 1440;
        if (&minus_result != minus_address || !(minus_value == Clock::at(static_cast<int>(minus_total / 60), static_cast<int>(minus_total % 60)))) return 3;
    }
    std::cout << "arithmetic-properties-ok\n";
}
'''
RELATION_PROPERTIES = r'''#include "clock.h"
#include <array>
#include <iostream>
using Clock = date_independent::clock;
int main() {
    const std::array<Clock, 9> values{{
        Clock::at(0), Clock::at(24), Clock::at(-24), Clock::at(0, 1), Clock::at(24, 1),
        Clock::at(23, 59), Clock::at(-1, -1), Clock::at(12, 34), Clock::at(12, 35)
    }};
    for (const auto& lhs : values) for (const auto& rhs : values) {
        if ((lhs == rhs) != (rhs == lhs)) return 1;
        if ((lhs != rhs) == (lhs == rhs)) return 2;
    }
    for (const auto& value : values) if (!(value == value) || value != value) return 3;
    if (!(values[0] == values[1]) || !(values[1] == values[2]) || !(values[0] == values[2])) return 4;
    auto first = Clock::at(1); const auto second = Clock::at(2); first.plus(60);
    if (!(first == second) || second != Clock::at(2)) return 5;
    if (Clock::at(0, 0) == Clock::at(0, 1) || !(Clock::at(0, 0) != Clock::at(0, 1))) return 6;
    if (Clock::at(0, 0) == Clock::at(1, 0) || !(Clock::at(0, 0) != Clock::at(1, 0))) return 7;
    if (!(Clock::at(23, 59) == Clock::at(0, -1)) || Clock::at(23, 59) != Clock::at(0, -1)) return 8;
    std::cout << "relation-properties-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "CLF-C05-A", "construction_property_sweep", "construction_properties.cpp", CONSTRUCTION_PROPERTIES, "construction-properties-ok\n", extra_flags=SANITIZER_FLAGS),
        compile_and_run(ctx, "CLF-C05-B", "arithmetic_property_sweep", "arithmetic_properties.cpp", ARITHMETIC_PROPERTIES, "arithmetic-properties-ok\n", extra_flags=SANITIZER_FLAGS),
        compile_and_run(ctx, "CLF-C05-C", "equality_relation_properties", "relation_properties.cpp", RELATION_PROPERTIES, "relation-properties-ok\n", extra_flags=SANITIZER_FLAGS),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
