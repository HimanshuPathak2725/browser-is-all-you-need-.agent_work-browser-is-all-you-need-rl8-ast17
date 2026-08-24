from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DNF-C04"
SUPPORT = r"""#include "dnd_character.h"
#include <array>
#include <iostream>
int main() {
    std::array<int, 19> counts{};
    int minimum = 19;
    int maximum = 0;
    for (int i = 0; i < 20000; ++i) {
        const int value = dnd_character::ability();
        if (value < 3 || value > 18) return 1;
        ++counts[static_cast<std::size_t>(value)];
        if (value < minimum) minimum = value;
        if (value > maximum) maximum = value;
    }
    int distinct = 0;
    for (int value = 3; value <= 18; ++value) distinct += counts[static_cast<std::size_t>(value)] > 0;
    if (distinct < 14 || minimum > 5 || maximum < 17) return 2;
    std::cout << "support-ok\n";
}
"""
DISTRIBUTION = r"""#include "dnd_character.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
int main() {
    std::array<long long, 19> expected{};
    for (int a = 1; a <= 6; ++a) for (int b = 1; b <= 6; ++b)
    for (int c = 1; c <= 6; ++c) for (int d = 1; d <= 6; ++d) {
        const int value = a + b + c + d - std::min(std::min(a, b), std::min(c, d));
        ++expected[static_cast<std::size_t>(value)];
    }
    constexpr int sample_count = 100000;
    std::array<long long, 19> observed{};
    long long observed_sum = 0;
    for (int i = 0; i < sample_count; ++i) {
        const int value = dnd_character::ability();
        if (value < 3 || value > 18) return 1;
        ++observed[static_cast<std::size_t>(value)];
        observed_sum += value;
    }
    double total_variation = 0.0;
    double expected_mean = 0.0;
    for (int value = 3; value <= 18; ++value) {
        const double expected_probability = static_cast<double>(expected[static_cast<std::size_t>(value)]) / 1296.0;
        const double observed_probability = static_cast<double>(observed[static_cast<std::size_t>(value)]) / sample_count;
        total_variation += std::abs(observed_probability - expected_probability);
        expected_mean += value * expected_probability;
    }
    total_variation /= 2.0;
    const double observed_mean = static_cast<double>(observed_sum) / sample_count;
    if (total_variation > 0.06 || std::abs(observed_mean - expected_mean) > 0.20) return 2;
    std::cout << "distribution-ok\n";
}
"""
SAFETY_FLAGS = (
    "-O1",
    "-D_GLIBCXX_ASSERTIONS",
    "-fsanitize=undefined",
    "-fno-sanitize-recover=undefined",
)


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(
            ctx,
            "DNF-C04-A",
            "ability_support_and_range",
            "ability_support.cpp",
            SUPPORT,
            "support-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
        compile_and_run(
            ctx,
            "DNF-C04-B",
            "four_dice_drop_lowest_distribution",
            "ability_distribution.cpp",
            DISTRIBUTION,
            "distribution-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
