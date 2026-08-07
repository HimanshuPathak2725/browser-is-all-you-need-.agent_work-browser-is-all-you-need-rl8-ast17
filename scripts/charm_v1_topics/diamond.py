"""Owner source for the three CHARM V1 Diamond tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


HOLLOW = r'''#pragma once
#include <cstdlib>
#include <optional>
#include <string>
#include <vector>
namespace charm::diamond {
inline std::optional<std::vector<std::string>> render_hollow(int height, char edge, char background) {
    if (height <= 0 || height % 2 == 0 || edge == '\n' || background == '\n') return std::nullopt;
    const int middle = height / 2;
    std::vector<std::string> lines;
    for (int row = 0; row < height; ++row) {
        const int half_width = middle - std::abs(middle - row);
        std::string line(static_cast<std::size_t>(height), background);
        line[static_cast<std::size_t>(middle - half_width)] = edge;
        line[static_cast<std::size_t>(middle + half_width)] = edge;
        while (!line.empty() && line.back() == ' ') line.pop_back();
        lines.push_back(std::move(line));
    }
    return lines;
}
}
'''
HOLLOW_START = HOLLOW.replace("middle - std::abs(middle - row)", "std::abs(middle - row)")
HOLLOW_TEST = r'''#include "styled-hollow-diamond.h"
#include <cassert>
#include <string>
#include <vector>
using charm::diamond::render_hollow;
int main() {
    assert(!render_hollow(0, '*', ' ') && !render_hollow(4, '*', ' '));
    assert((render_hollow(1, '#', ' ').value() == std::vector<std::string>{"#"}));
    assert((render_hollow(3, '*', ' ').value() == std::vector<std::string>{" *", "* *", " *"}));
    assert((render_hollow(3, '@', '.').value() == std::vector<std::string>{".@.", "@.@", ".@."}));
    assert(!render_hollow(3, '\n', '.'));
    const auto five = render_hollow(5, 'X', ' ');
    assert(five && five->size() == 5 && (*five)[2] == "X   X");
    for (const auto& line : *five) assert(line.empty() || line.back() != ' ');
    return 0;
}
'''


SHELL = r'''#include <vector>
namespace charm::diamond {
struct Point {
    int x;
    int y;
    bool operator==(const Point& other) const { return x == other.x && y == other.y; }
};
inline std::vector<Point> shell(Point center, int radius) {
    if (radius < 0) return {};
    if (radius == 0) return {center};
    std::vector<Point> out;
    out.reserve(static_cast<std::size_t>(4 * radius));
    for (int step = 0; step < radius; ++step) out.push_back({center.x + step, center.y - radius + step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x + radius - step, center.y + step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x - step, center.y + radius - step});
    for (int step = 0; step < radius; ++step) out.push_back({center.x - radius + step, center.y - step});
    return out;
}
}
'''
SHELL_TEST = r'''#include "manhattan-shell.cpp"
#include <cassert>
#include <set>
#include <utility>
#include <vector>
#include <cstdlib>
using charm::diamond::Point;
using charm::diamond::shell;
int main() {
    assert(shell({2, 3}, -1).empty());
    const auto radius_zero = shell({2, 3}, 0);
    const std::vector<Point> expected_zero{{2, 3}};
    assert(radius_zero == expected_zero);
    const auto radius_one = shell({0, 0}, 1);
    const std::vector<Point> expected_one{{0,-1},{1,0},{0,1},{-1,0}};
    assert(radius_one == expected_one);
    const auto radius_two = shell({1, -1}, 2);
    assert((radius_two.size() == 8 && radius_two.front() == Point{1, -3}));
    assert((radius_two[2] == Point{3, -1} && radius_two[4] == Point{1, 1}));
    std::set<std::pair<int,int>> unique;
    for (Point point : radius_two) unique.insert({point.x, point.y});
    assert(unique.size() == radius_two.size());
    for (Point point : radius_two) assert(std::abs(point.x - 1) + std::abs(point.y + 1) == 2);
    return 0;
}
'''


CLIPPED = r'''#pragma once
#include <cstdlib>
#include <utility>
#include <vector>
namespace charm::diamond {
struct Rect { int x0; int y0; int x1; int y1; };
inline std::vector<std::pair<int,int>> clipped_cells(int center_x, int center_y, int radius, Rect view) {
    if (radius < 0 || view.x0 > view.x1 || view.y0 > view.y1) return {};
    std::vector<std::pair<int,int>> out;
    for (int y = view.y0; y < view.y1; ++y)
        for (int x = view.x0; x < view.x1; ++x)
            if (std::abs(static_cast<long long>(x) - center_x) + std::abs(static_cast<long long>(y) - center_y) <= radius)
                out.push_back({x - view.x0, y - view.y0});
    return out;
}
}
'''
CLIPPED_START = CLIPPED.replace("<= radius", "< radius")
CLIPPED_TEST = r'''#include "clipped-diamond-repair.hpp"
#include <cassert>
#include <utility>
#include <vector>
using charm::diamond::Rect;
using charm::diamond::clipped_cells;
int main() {
    assert(clipped_cells(0, 0, -1, {0,0,2,2}).empty());
    assert(clipped_cells(0, 0, 1, {2,2,1,3}).empty());
    assert((clipped_cells(0, 0, 0, {-1,-1,2,2}) == std::vector<std::pair<int,int>>{{1,1}}));
    assert((clipped_cells(0, 0, 1, {0,0,2,2}) == std::vector<std::pair<int,int>>{{0,0},{1,0},{0,1}}));
    const auto cells = clipped_cells(5, 5, 2, {4,4,7,7});
    assert(cells.size() == 9);
    assert(cells.front() == std::make_pair(0,0) && cells.back() == std::make_pair(2,2));
    assert(clipped_cells(0, 0, 5, {1,1,1,4}).empty());
    return 0;
}
'''


def tasks() -> list[dict]:
    hollow = ["styled-hollow-diamond.h", "styled-hollow-diamond.cpp"]
    shell_files = ["manhattan-shell.cpp"]
    clipped = ["clipped-diamond-repair.hpp"]
    return [
        package(topic="Diamond", task_id="charm-v1-styled-hollow-diamond", instructions=prompt("Styled hollow diamond", "Render a centered odd-height hollow diamond with selected edge and background bytes; literal trailing spaces must be removed.", "namespace charm::diamond { std::optional<std::vector<std::string>> render_hollow(int,char,char); }", ["height is positive and odd", "height one", "newline style bytes reject", "edge positions are symmetric", "no returned line ends in a space"], hollow), editable={hollow[0]: HOLLOW_START, hollow[1]: support(hollow[0], 71)}, reference={hollow[0]: HOLLOW, hollow[1]: support(hollow[0], 72)}, hidden_name="styled-hollow-diamond_test.cpp", hidden=HOLLOW_TEST, category="hollow-rendering", tags=["runtime-repair", "formatting", "symmetry", "header-edit"]),
        package(topic="Diamond", task_id="charm-v1-manhattan-shell", instructions=prompt("Manhattan shell", "Enumerate every integer cell at an exact Manhattan radius clockwise from the top cell, without duplicate corner cells.", "namespace charm::diamond { struct Point { int x; int y; bool operator==(const Point&) const; }; std::vector<Point> shell(Point,int); }", ["negative radius is empty", "radius zero is the center", "positive shells contain exactly 4r cells", "first cell is top", "center offsets may be negative"], shell_files), editable={shell_files[0]: "#include <vector>\nnamespace charm::diamond { struct Point { int x; int y; }; std::vector<Point> shell(Point,int); }\n"}, reference={shell_files[0]: SHELL}, hidden_name="manhattan-shell_test.cpp", hidden=SHELL_TEST, category="grid-enumeration", tags=["cpp-only", "clockwise", "coordinates", "deduplication"]),
        package(topic="Diamond", task_id="charm-v1-clipped-diamond-repair", instructions=prompt("Clipped filled diamond", "Clip a filled Manhattan diamond to a half-open viewport and return occupied positions row-major relative to the viewport origin.", "namespace charm::diamond { struct Rect { int x0; int y0; int x1; int y1; }; std::vector<std::pair<int,int>> clipped_cells(int,int,int,Rect); }", ["negative radius rejects", "reversed viewport rejects", "empty viewport", "diamond boundary is included", "coordinates are viewport-relative"], clipped), editable={clipped[0]: CLIPPED_START}, reference={clipped[0]: CLIPPED}, hidden_name="clipped-diamond-repair_test.cpp", hidden=CLIPPED_TEST, category="viewport-clipping", tags=["header-only", "near-correct", "half-open", "boundary"]),
    ]
