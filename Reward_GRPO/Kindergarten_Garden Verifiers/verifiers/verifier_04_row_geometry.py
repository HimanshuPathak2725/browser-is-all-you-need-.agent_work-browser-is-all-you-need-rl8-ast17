from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "KGF-C04"
DYNAMIC_WIDTHS = r'''#include "kindergarten_garden.h"
#include <array>
#include <cstddef>
#include <iostream>
#include <string>
#include <string_view>
using P = kindergarten_garden::Plants;
constexpr std::array<std::string_view, 12> names{
    "Alice", "Bob", "Charlie", "David", "Eve", "Fred",
    "Ginny", "Harriet", "Ileana", "Joseph", "Kincaid", "Larry"};
std::string make_diagram(std::size_t students, std::size_t seed) {
    constexpr std::string_view symbols = "CGRV";
    std::string result;
    for (std::size_t index = 0; index < 2 * students; ++index) result.push_back(symbols.at((index + seed) % 4));
    result.push_back('\n');
    for (std::size_t index = 0; index < 2 * students; ++index) result.push_back(symbols.at((3 * index + seed + 1) % 4));
    return result;
}
std::array<P, 4> expected(const std::string& diagram, std::size_t student) {
    const std::size_t width = diagram.find('\n');
    const std::size_t offset = 2 * student;
    return {static_cast<P>(diagram.at(offset)), static_cast<P>(diagram.at(offset + 1)),
            static_cast<P>(diagram.at(width + 1 + offset)), static_cast<P>(diagram.at(width + 2 + offset))};
}
int main() {
    std::size_t checked = 0;
    for (std::size_t students = 1; students <= names.size(); ++students) {
        for (std::size_t seed = 0; seed < 4; ++seed) {
            const std::string diagram = make_diagram(students, seed);
            for (std::size_t index = 0; index < students; ++index) {
                if (kindergarten_garden::plants(diagram, names.at(index)) != expected(diagram, index)) return 1;
                ++checked;
            }
        }
    }
    if (checked != 312) return 2;
    std::cout << "widths-ok 312\n";
}
'''
POSITION_ORDER = r'''#include "kindergarten_garden.h"
#include <array>
#include <cstddef>
#include <iostream>
#include <string>
#include <string_view>
using P = kindergarten_garden::Plants;
constexpr std::array<std::string_view, 12> names{
    "Alice", "Bob", "Charlie", "David", "Eve", "Fred",
    "Ginny", "Harriet", "Ileana", "Joseph", "Kincaid", "Larry"};
int main() {
    const std::array<P, 4> expected{P::clover, P::grass, P::radishes, P::violets};
    std::size_t checked = 0;
    for (std::size_t students = 1; students <= names.size(); ++students) {
        for (std::size_t target = 0; target < students; ++target) {
            std::string top(2 * students, 'V');
            std::string bottom(2 * students, 'C');
            top.at(2 * target) = 'C';
            top.at(2 * target + 1) = 'G';
            bottom.at(2 * target) = 'R';
            bottom.at(2 * target + 1) = 'V';
            const std::string diagram = top + "\n" + bottom;
            if (kindergarten_garden::plants(diagram, names.at(target)) != expected) return 1;
            ++checked;
        }
    }
    if (checked != 78) return 2;
    std::cout << "order-ok 78\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "KGF-C04-A", "all_supported_row_widths", "dynamic_widths.cpp", DYNAMIC_WIDTHS, "widths-ok 312\n"),
        compile_and_run(ctx, "KGF-C04-B", "exact_cup_position_order", "position_order.cpp", POSITION_ORDER, "order-ok 78\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
