from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT
from _helpers import compile_multi_tu_and_run


POLICY_ID = "DNF-C02"
EXACT_TYPES = r"""#include "dnd_character.h"
#include <type_traits>
using Character = dnd_character::Character;
static_assert(std::is_same_v<decltype(&dnd_character::modifier), int (*)(int)>);
static_assert(std::is_same_v<decltype(&dnd_character::ability), int (*)()>);
static_assert(std::is_default_constructible_v<Character>);
static_assert(std::is_same_v<decltype(&Character::strength), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::dexterity), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::constitution), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::intelligence), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::wisdom), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::charisma), int Character::*>);
static_assert(std::is_same_v<decltype(&Character::hitpoints), int Character::*>);
int main() { return 0; }
"""
CALL_SURFACE = r"""#include "dnd_character.h"
#include <iostream>
int main() {
    int (*modifier_fn)(int) = &dnd_character::modifier;
    int (*ability_fn)() = &dnd_character::ability;
    dnd_character::Character value;
    if (modifier_fn(18) != 4) return 1;
    const int generated = ability_fn();
    if (generated < 3 || generated > 18) return 2;
    if (value.hitpoints != 10 + modifier_fn(value.constitution)) return 3;
    std::cout << "api-ok\n";
}
"""
HELPER = r"""#include "dnd_character.h"
#include "dnd_character.h"
int modifier_elsewhere(int score) { return dnd_character::modifier(score); }
int ability_elsewhere() { return dnd_character::ability(); }
"""
MAIN = r"""#include "dnd_character.h"
#include <iostream>
int modifier_elsewhere(int);
int ability_elsewhere();
int main() {
    if (modifier_elsewhere(3) != -4 || modifier_elsewhere(18) != 4) return 1;
    const int value = ability_elsewhere();
    if (value < 3 || value > 18) return 2;
    const dnd_character::Character character;
    if (character.hitpoints != 10 + dnd_character::modifier(character.constitution)) return 3;
    std::cout << "multi-tu-ok\n";
}
"""


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "DNF-C02-A", "exact_public_types", "exact_types.cpp", EXACT_TYPES),
        compile_and_run(
            ctx,
            "DNF-C02-B",
            "callable_public_surface",
            "call_surface.cpp",
            CALL_SURFACE,
            "api-ok\n",
        ),
        compile_multi_tu_and_run(
            ctx,
            "DNF-C02-C",
            "repeated_include_multi_tu_odr",
            {"helper.cpp": HELPER, "main.cpp": MAIN},
            "multi-tu-ok\n",
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
