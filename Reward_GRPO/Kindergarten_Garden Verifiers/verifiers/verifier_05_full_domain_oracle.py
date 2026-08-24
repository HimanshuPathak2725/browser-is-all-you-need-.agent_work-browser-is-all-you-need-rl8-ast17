from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "KGF-C05"
ORACLE_SUPPORT = r'''#include "kindergarten_garden.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>
using P = kindergarten_garden::Plants;
constexpr std::array<std::string_view, 12> names{
    "Alice", "Bob", "Charlie", "David", "Eve", "Fred",
    "Ginny", "Harriet", "Ileana", "Joseph", "Kincaid", "Larry"};
std::string generated_diagram(std::size_t students, std::uint32_t seed) {
    constexpr std::string_view symbols = "CGRV";
    std::string result;
    std::uint32_t state = seed + static_cast<std::uint32_t>(students * 104729U);
    for (std::size_t row = 0; row < 2; ++row) {
        if (row != 0) result.push_back('\n');
        for (std::size_t column = 0; column < 2 * students; ++column) {
            state = state * 1664525U + 1013904223U;
            result.push_back(symbols.at((state >> 29U) & 3U));
        }
    }
    return result;
}
std::array<P, 4> oracle(std::string_view diagram, std::size_t student) {
    const std::size_t width = diagram.find('\n');
    const std::size_t offset = 2 * student;
    return {static_cast<P>(diagram.at(offset)), static_cast<P>(diagram.at(offset + 1)),
            static_cast<P>(diagram.at(width + 1 + offset)), static_cast<P>(diagram.at(width + 2 + offset))};
}
bool exact(std::string_view diagram, std::string_view name, std::size_t student) {
    return kindergarten_garden::plants(diagram, name) == oracle(diagram, student);
}
'''
FULL_ORACLE = ORACLE_SUPPORT + r'''
int main() {
    std::size_t checked = 0;
    for (std::size_t students = 1; students <= names.size(); ++students) {
        for (std::uint32_t seed = 0; seed < 64U; ++seed) {
            const std::string diagram = generated_diagram(students, seed);
            for (std::size_t student = 0; student < students; ++student) {
                if (!exact(diagram, names.at(student), student)) return 1;
                ++checked;
            }
        }
    }
    if (checked != 4992) return 2;
    std::cout << "oracle-ok 4992\n";
}
'''
INTERLEAVED = ORACLE_SUPPORT + r'''
struct Case {
    std::string storage;
    std::string name_storage;
    std::string_view diagram;
    std::string_view name;
    std::size_t student;
    std::array<P, 4> expected;
    Case(std::size_t students, std::size_t index, std::uint32_t seed)
        : storage("XX" + generated_diagram(students, seed) + "TRAILING-POISON"),
          name_storage("!" + std::string(names.at(index)) + "?not-part-of-view"),
          diagram(storage.data() + 2, generated_diagram(students, seed).size()),
          name(name_storage.data() + 1, names.at(index).size()),
          student(index),
          expected(oracle(diagram, student)) {}
};
int main() {
    std::vector<Case> cases;
    for (std::size_t students = 1; students <= names.size(); ++students) {
        cases.emplace_back(students, 0, static_cast<std::uint32_t>(students * 17));
        cases.emplace_back(students, students - 1, static_cast<std::uint32_t>(students * 31));
        cases.emplace_back(students, students / 2, static_cast<std::uint32_t>(students * 47));
    }
    for (int round = 0; round < 8; ++round) {
        for (std::size_t reverse = cases.size(); reverse > 0; --reverse) {
            const Case& item = cases.at(reverse - 1);
    cases.reserve(36);
            if (kindergarten_garden::plants(item.diagram, item.name) != item.expected) return 1;
            if (!exact(item.diagram, item.name, item.student)) return 2;
        }
    }
    std::cout << "interleaved-ok 288\n";
}
'''
SAFETY_FLAGS = ("-O1", "-D_GLIBCXX_ASSERTIONS", "-fsanitize=undefined", "-fno-sanitize-recover=undefined")


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(
            ctx,
            "KGF-C05-A",
            "generated_full_domain_oracle",
            "full_oracle.cpp",
            FULL_ORACLE,
            "oracle-ok 4992\n",
            extra_flags=SAFETY_FLAGS,
        ),
        compile_and_run(
            ctx,
            "KGF-C05-B",
            "bounded_view_interleaved_oracle",
            "interleaved_oracle.cpp",
            INTERLEAVED,
            "interleaved-ok 288\n",
            extra_flags=SAFETY_FLAGS,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
