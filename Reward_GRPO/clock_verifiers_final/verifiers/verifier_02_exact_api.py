from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT


POLICY_ID = "CLF-C02"
CALL_SURFACE = r'''#include "clock.h"
#include <string>
int main() {
    auto value = date_independent::clock::at(1);
    date_independent::clock& chained = value.plus(61).minus(61);
    const std::string rendered = static_cast<std::string>(chained);
    return value == date_independent::clock::at(1, 0) && !rendered.empty() ? 0 : 1;
}
'''
SIGNATURES = r'''#include "clock.h"
#include <string>
#include <type_traits>
using Clock = date_independent::clock;
using At = Clock (*)(int, int);
using Mutation = Clock& (Clock::*)(int);
using Equality = bool (Clock::*)(const Clock&) const;
using Conversion = std::string (Clock::*)() const;
static_assert(std::is_same_v<decltype(&Clock::at), At>);
static_assert(std::is_same_v<decltype(&Clock::plus), Mutation>);
static_assert(std::is_same_v<decltype(&Clock::minus), Mutation>);
static_assert(std::is_same_v<decltype(&Clock::operator==), Equality>);
static_assert(std::is_same_v<decltype(static_cast<Conversion>(&Clock::operator std::string)), Conversion>);
static_assert(!std::is_constructible_v<Clock, int, int>);
static_assert(std::is_copy_constructible_v<Clock>);
static_assert(std::is_copy_assignable_v<Clock>);
int main() { return 0; }
'''
FREE_INEQUALITY = r'''#include "clock.h"
#include <iostream>
using Clock = date_independent::clock;
using NotEqual = bool (*)(const Clock&, const Clock&);
int main() {
    const NotEqual not_equal = &date_independent::operator!=;
    const auto same_a = Clock::at(1, 0);
    const auto same_b = Clock::at(25, 0);
    const auto different = Clock::at(1, 1);
    if (not_equal(same_a, same_b) || !not_equal(same_a, different)) return 1;
    std::cout << "api-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CLF-C02-A", "default_and_chaining_surface", "api_surface.cpp", CALL_SURFACE),
        compile_only(ctx, "CLF-C02-B", "exact_member_types", "api_types.cpp", SIGNATURES),
        compile_and_run(ctx, "CLF-C02-C", "free_inequality_type_behavior", "free_inequality.cpp", FREE_INEQUALITY, "api-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
