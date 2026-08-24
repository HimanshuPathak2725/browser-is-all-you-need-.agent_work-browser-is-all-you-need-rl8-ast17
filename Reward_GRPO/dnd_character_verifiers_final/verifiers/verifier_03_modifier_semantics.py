from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DNF-C03"
NEGATIVE_FLOOR = r"""#include "dnd_character.h"
#include <array>
#include <iostream>
int main() {
    const std::array<int, 7> expected{-4, -3, -3, -2, -2, -1, -1};
    for (int repetition = 0; repetition < 64; ++repetition) {
        for (int score = 3; score <= 9; ++score) {
            if (dnd_character::modifier(score) != expected[static_cast<std::size_t>(score - 3)]) return 1;
        }
    }
    std::cout << "negative-floor-ok\n";
}
"""
NONNEGATIVE_TABLE = r"""#include "dnd_character.h"
#include <array>
#include <iostream>
int main() {
    const std::array<int, 9> expected{0, 0, 1, 1, 2, 2, 3, 3, 4};
    for (int repetition = 0; repetition < 64; ++repetition) {
        for (int score = 10; score <= 18; ++score) {
            if (dnd_character::modifier(score) != expected[static_cast<std::size_t>(score - 10)]) return 1;
        }
    }
    std::cout << "nonnegative-table-ok\n";
}
"""


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(
            ctx,
            "DNF-C03-A",
            "negative_odd_floor_table",
            "negative_floor.cpp",
            NEGATIVE_FLOOR,
            "negative-floor-ok\n",
        ),
        compile_and_run(
            ctx,
            "DNF-C03-B",
            "zero_positive_modifier_table",
            "nonnegative_table.cpp",
            NONNEGATIVE_TABLE,
            "nonnegative-table-ok\n",
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
