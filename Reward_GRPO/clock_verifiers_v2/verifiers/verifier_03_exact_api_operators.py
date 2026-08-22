from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, compile_only, execute

from _contract import CONTRACT


POLICY_ID = "CL2-C03"
NAMES_PROBE = r'''#include "clock.h"
#include <string>
int main() {
    auto value = date_independent::clock::at(1);
    value.plus(1).minus(1);
    const std::string rendered = static_cast<std::string>(value);
    return (value == date_independent::clock::at(1, 0)) && !rendered.empty() ? 0 : 1;
}
'''
SIGNATURE_PROBE = r'''#include "clock.h"
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
int main() { return 0; }
'''
FREE_OPERATOR_PROBE = r'''#include "clock.h"
#include <iostream>
using Clock = date_independent::clock;
using NotEqual = bool (*)(const Clock&, const Clock&);
int main() {
    const NotEqual not_equal = &date_independent::operator!=;
    const auto first = Clock::at(1, 0);
    const auto second = Clock::at(2, 0);
    std::cout << (not_equal(first, second) ? "different" : "same") << '\n';
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_only(ctx, "CL2-C03-A", "public_names", "api_names.cpp", NAMES_PROBE),
        compile_only(ctx, "CL2-C03-B", "exact_member_signatures", "api_signatures.cpp", SIGNATURE_PROBE),
        compile_and_run(ctx, "CL2-C03-C", "free_inequality", "api_free_inequality.cpp", FREE_OPERATOR_PROBE, "different\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
