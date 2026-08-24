from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from strange_cpp import Context, KernelReceipt, compile_and_run, execute

from _contract import CONTRACT


POLICY_ID = "KGF-C03"
ROSTER_SWEEP = r'''#include "kindergarten_garden.h"
#include <array>
#include <cstddef>
#include <iostream>
#include <string>
#include <string_view>
using P = kindergarten_garden::Plants;
constexpr std::array<std::string_view, 12> names{
    "Alice", "Bob", "Charlie", "David", "Eve", "Fred",
    "Ginny", "Harriet", "Ileana", "Joseph", "Kincaid", "Larry"};
std::array<P, 4> expected(const std::string& diagram, std::size_t student) {
    const std::size_t width = diagram.find('\n');
    const std::size_t offset = 2 * student;
    return {static_cast<P>(diagram.at(offset)), static_cast<P>(diagram.at(offset + 1)),
            static_cast<P>(diagram.at(width + 1 + offset)), static_cast<P>(diagram.at(width + 2 + offset))};
}
int main() {
    const std::string top = "CGRVVRGCCVRGGRVCCGRVVGRC";
    const std::string bottom = "VRGCCGVRRCGVVGRCCVRGCGVR";
    const std::string diagram = top + "\n" + bottom;
    for (std::size_t index = 0; index < names.size(); ++index) {
        if (kindergarten_garden::plants(diagram, names.at(index)) != expected(diagram, index)) return 1;
    }
    std::cout << "roster-ok 12\n";
}
'''
VIEW_AND_REPEAT = r'''#include "kindergarten_garden.h"
#include <array>
#include <cstddef>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>
using P = kindergarten_garden::Plants;
constexpr std::array<std::string_view, 12> names{
    "Alice", "Bob", "Charlie", "David", "Eve", "Fred",
    "Ginny", "Harriet", "Ileana", "Joseph", "Kincaid", "Larry"};
std::array<P, 4> expected(const std::string& diagram, std::size_t student) {
    const std::size_t width = diagram.find('\n');
    const std::size_t offset = 2 * student;
    return {static_cast<P>(diagram.at(offset)), static_cast<P>(diagram.at(offset + 1)),
            static_cast<P>(diagram.at(width + 1 + offset)), static_cast<P>(diagram.at(width + 2 + offset))};
}
int main() {
    const std::string clean = "VRCGVVRVCGGCCGVRGCVCGCGV\nVRCCCGCRRGVCGCRVVCVGCGCV";
    const std::string diagram_storage = clean + "TRAILING-POISON";
    const std::string_view diagram(diagram_storage.data(), clean.size());
    std::vector<std::array<P, 4>> saved;
    for (std::size_t index = 0; index < names.size(); ++index) {
        const std::string name_storage = std::string(names.at(index)) + "-not-part-of-view";
        const std::string_view name(name_storage.data(), names.at(index).size());
        const auto value = kindergarten_garden::plants(diagram, name);
        if (value != expected(clean, index)) return 1;
        saved.push_back(value);
    }
    for (int round = 0; round < 5; ++round) {
        for (std::size_t reverse = names.size(); reverse > 0; --reverse) {
            const std::size_t index = reverse - 1;
            if (kindergarten_garden::plants(diagram, names.at(index)) != saved.at(index)) return 2;
        }
    }
    std::cout << "views-repeat-ok\n";
}
'''


def checks(ctx: Context) -> list[KernelReceipt]:
    return [
        compile_and_run(ctx, "KGF-C03-A", "complete_roster_mapping", "roster_sweep.cpp", ROSTER_SWEEP, "roster-ok 12\n"),
        compile_and_run(ctx, "KGF-C03-B", "bounded_views_and_repeatability", "views_repeat.cpp", VIEW_AND_REPEAT, "views-repeat-ok\n"),
    ]


if __name__ == "__main__":
    raise SystemExit(execute(CONTRACT, POLICY_ID, Path(__file__), checks))
