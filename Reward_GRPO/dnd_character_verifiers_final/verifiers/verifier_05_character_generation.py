from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "DNF-C05"
INVARIANTS = r"""#include "dnd_character.h"
#include <array>
#include <iostream>
int main() {
    for (int i = 0; i < 5000; ++i) {
        const dnd_character::Character value;
        const std::array<int, 6> abilities{value.strength, value.dexterity, value.constitution,
                                           value.intelligence, value.wisdom, value.charisma};
        for (const int ability : abilities) if (ability < 3 || ability > 18) return 1;
        if (value.hitpoints != 10 + dnd_character::modifier(value.constitution)) return 2;
    }
    std::cout << "character-invariants-ok\n";
}
"""
INDEPENDENCE = r"""#include "dnd_character.h"
#include <array>
#include <iostream>
int main() {
    constexpr int sample_count = 5000;
    std::array<std::array<int, 19>, 6> counts{};
    std::array<long long, 6> sums{};
    int all_equal = 0;
    for (int i = 0; i < sample_count; ++i) {
        const dnd_character::Character value;
        const std::array<int, 6> abilities{value.strength, value.dexterity, value.constitution,
                                           value.intelligence, value.wisdom, value.charisma};
        bool same = true;
        for (std::size_t field = 0; field < abilities.size(); ++field) {
            const int ability = abilities[field];
            if (ability < 3 || ability > 18) return 1;
            ++counts[field][static_cast<std::size_t>(ability)];
            sums[field] += ability;
            if (ability != abilities[0]) same = false;
        }
        all_equal += same;
    }
    if (all_equal > sample_count / 20) return 2;
    for (std::size_t field = 0; field < counts.size(); ++field) {
        int distinct = 0;
        for (int value = 3; value <= 18; ++value) distinct += counts[field][static_cast<std::size_t>(value)] > 0;
        const double mean = static_cast<double>(sums[field]) / sample_count;
        if (distinct < 13 || mean < 11.5 || mean > 13.0) return 3;
    }
    std::cout << "character-independence-ok\n";
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
            "DNF-C05-A",
            "character_field_and_hitpoint_invariants",
            "character_invariants.cpp",
            INVARIANTS,
            "character-invariants-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
        compile_and_run(
            ctx,
            "DNF-C05-B",
            "six_ability_generation_independence",
            "character_independence.cpp",
            INDEPENDENCE,
            "character-independence-ok\n",
            extra_flags=SAFETY_FLAGS,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
