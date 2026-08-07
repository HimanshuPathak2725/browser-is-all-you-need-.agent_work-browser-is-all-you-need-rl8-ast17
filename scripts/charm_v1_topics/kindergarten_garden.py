"""Owner source for the three CHARM V1 Kindergarten Garden tasks."""

from __future__ import annotations

from scripts.charm_v1_topics.common import package, prompt, support


CUPS = r'''#pragma once
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class CupGarden {
public:
    static std::optional<CupGarden> parse(std::vector<std::string> rows, std::vector<std::string> students, std::size_t cups) {
        if (rows.empty() || students.empty() || cups == 0) return std::nullopt;
        const std::size_t width = students.size() * cups;
        for (const std::string& row : rows) if (row.size() != width) return std::nullopt;
        std::set<std::string> unique;
        for (const std::string& student : students) if (student.empty() || !unique.insert(student).second) return std::nullopt;
        return CupGarden(std::move(rows), std::move(students), cups);
    }
    std::vector<char> plants(std::string_view student) const {
        std::size_t index = students_.size();
        for (std::size_t i = 0; i < students_.size(); ++i) if (students_[i] == student) index = i;
        if (index == students_.size()) return {};
        std::vector<char> out;
        for (const std::string& row : rows_)
            for (std::size_t cup = 0; cup < cups_; ++cup) out.push_back(row[index * cups_ + cup]);
        return out;
    }
private:
    CupGarden(std::vector<std::string> rows, std::vector<std::string> students, std::size_t cups)
        : rows_(std::move(rows)), students_(std::move(students)), cups_(cups) {}
    std::vector<std::string> rows_;
    std::vector<std::string> students_;
    std::size_t cups_;
};
}
'''
CUPS_TEST = r'''#include "variable-cup-garden.h"
#include <cassert>
#include <vector>
using charm::garden::CupGarden;
int main() {
    assert(!CupGarden::parse({}, {"Ada"}, 2));
    assert(!CupGarden::parse({"AB"}, {}, 2));
    assert(!CupGarden::parse({"ABC"}, {"Ada","Bob"}, 2));
    assert(!CupGarden::parse({"ABCD"}, {"Ada","Ada"}, 2));
    const auto garden = CupGarden::parse({"ABCD", "EFGH", "IJKL"}, {"Ada","Bob"}, 2);
    assert(garden);
    assert((garden->plants("Ada") == std::vector<char>{'A','B','E','F','I','J'}));
    assert((garden->plants("Bob") == std::vector<char>{'C','D','G','H','K','L'}));
    assert(garden->plants("Eve").empty());
    return 0;
}
'''


ROTATING = r'''#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class RotatingGarden {
public:
    RotatingGarden(std::vector<std::string> students, std::vector<char> plants)
        : students_(std::move(students)), plants_(std::move(plants)) {}
    std::vector<char> plants_for(std::string_view student, long long day) const {
        if (students_.empty() || plants_.size() % students_.size() != 0) return {};
        std::size_t student_index = students_.size();
        for (std::size_t i = 0; i < students_.size(); ++i) if (students_[i] == student) student_index = i;
        if (student_index == students_.size()) return {};
        const long long count = static_cast<long long>(students_.size());
        long long shift = day % count;
        if (shift < 0) shift += count;
        const std::size_t seat = (student_index + static_cast<std::size_t>(shift)) % students_.size();
        const std::size_t cups = plants_.size() / students_.size();
        return {plants_.begin() + static_cast<long long>(seat * cups), plants_.begin() + static_cast<long long>((seat + 1) * cups)};
    }
private:
    std::vector<std::string> students_;
    std::vector<char> plants_;
};
}
'''
ROTATING_TEST = r'''#include "rotating-garden-seats.cpp"
#include <cassert>
#include <vector>
using charm::garden::RotatingGarden;
int main() {
    RotatingGarden garden({"Ada","Bob","Cid"}, {'A','a','B','b','C','c'});
    assert((garden.plants_for("Ada", 0) == std::vector<char>{'A','a'}));
    assert((garden.plants_for("Ada", 1) == std::vector<char>{'B','b'}));
    assert((garden.plants_for("Cid", 1) == std::vector<char>{'A','a'}));
    assert((garden.plants_for("Ada", -1) == std::vector<char>{'C','c'}));
    assert((garden.plants_for("Bob", 7) == std::vector<char>{'C','c'}));
    assert(garden.plants_for("Eve", 0).empty());
    RotatingGarden malformed({"A","B"}, {'x','y','z'});
    assert(malformed.plants_for("A", 0).empty());
    return 0;
}
'''


PATCH = r'''#pragma once
#include <algorithm>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class PatchGrid {
public:
    static std::optional<PatchGrid> parse(const std::vector<std::string>& rows, std::string_view allowed) {
        if (rows.empty() || rows.front().empty() || allowed.empty()) return std::nullopt;
        std::set<char> codes(allowed.begin(), allowed.end());
        if (codes.size() != allowed.size()) return std::nullopt;
        for (const std::string& row : rows) {
            if (row.size() != rows.front().size()) return std::nullopt;
            for (char plant : row) if (codes.count(plant) == 0U) return std::nullopt;
        }
        return PatchGrid(rows);
    }
    std::map<char,int> count_patch(int x0, int y0, int x1, int y1) const {
        if (x0 > x1 || y0 > y1) return {};
        x0 = std::max(x0, 0); y0 = std::max(y0, 0);
        x1 = std::min(x1, static_cast<int>(rows_[0].size()));
        y1 = std::min(y1, static_cast<int>(rows_.size()));
        std::map<char,int> counts;
        for (int y = y0; y < y1; ++y) for (int x = x0; x < x1; ++x) ++counts[rows_[y][x]];
        return counts;
    }
private:
    explicit PatchGrid(std::vector<std::string> rows) : rows_(std::move(rows)) {}
    std::vector<std::string> rows_;
};
}
'''
PATCH_START = PATCH.replace("x1 = std::min(x1, static_cast<int>(rows_[0].size()));", "x1 = std::min(x1, static_cast<int>(rows_.size()));")
PATCH_TEST = r'''#include "garden-patch-repair.h"
#include <cassert>
#include <map>
using charm::garden::PatchGrid;
int main() {
    assert(!PatchGrid::parse({}, "AB"));
    assert(!PatchGrid::parse({"AB","A"}, "AB"));
    assert(!PatchGrid::parse({"AC"}, "AB"));
    assert(!PatchGrid::parse({"AB"}, "AA"));
    const auto grid = PatchGrid::parse({"ABBA","BAAB","AAAA"}, "AB");
    assert(grid);
    assert((grid->count_patch(0,0,4,3) == std::map<char,int>{{'A',8},{'B',4}}));
    assert((grid->count_patch(1,0,3,2) == std::map<char,int>{{'A',2},{'B',2}}));
    assert((grid->count_patch(-5,-5,1,1) == std::map<char,int>{{'A',1}}));
    assert(grid->count_patch(3,2,1,0).empty());
    return 0;
}
'''


def tasks() -> list[dict]:
    cups = ["variable-cup-garden.h", "variable-cup-garden.cpp"]
    rotate = ["rotating-garden-seats.cpp"]
    patch_files = ["garden-patch-repair.h", "garden-patch-repair.cpp"]
    return [
        package(topic="Kindergarten Garden", task_id="charm-v1-variable-cup-garden", instructions=prompt("Variable cup garden", "Parse equal-width plant rows for an ordered student list and configurable cups per student; return plants row-major within that student's cups.", "namespace charm::garden { class CupGarden { public: static std::optional<CupGarden> parse(std::vector<std::string>,std::vector<std::string>,std::size_t); std::vector<char> plants(std::string_view) const; }; }", ["nonempty rows and students", "positive cups", "width equals students times cups", "student names are unique", "unknown student returns empty"], cups), editable={cups[0]: "#pragma once\nnamespace charm::garden { class CupGarden; }\n", cups[1]: support(cups[0], 91)}, reference={cups[0]: CUPS, cups[1]: support(cups[0], 92)}, hidden_name="variable-cup-garden_test.cpp", hidden=CUPS_TEST, category="variable-layout", tags=["header-reconstruction", "parser", "multi-row", "indexing"]),
        package(topic="Kindergarten Garden", task_id="charm-v1-rotating-garden-seats", instructions=prompt("Rotating garden seats", "Keep plants at fixed equal-size seat blocks while student ownership rotates by signed day using floor-mod semantics.", "namespace charm::garden { class RotatingGarden { public: RotatingGarden(std::vector<std::string>,std::vector<char>); std::vector<char> plants_for(std::string_view,long long) const; }; }", ["day zero", "positive wrap", "negative rotation", "unknown student", "malformed unequal seat blocks return empty"], rotate), editable={rotate[0]: "#include <string>\nnamespace charm::garden { class RotatingGarden {}; }\n"}, reference={rotate[0]: ROTATING}, hidden_name="rotating-garden-seats_test.cpp", hidden=ROTATING_TEST, category="rotating-ownership", tags=["cpp-only", "floor-mod", "layout", "signed-day"]),
        package(topic="Kindergarten Garden", task_id="charm-v1-garden-patch-repair", instructions=prompt("Garden patch repair", "Parse a rectangular grid restricted to unique allowed plant codes, then count clipped half-open rectangular patches.", "namespace charm::garden { class PatchGrid { public: static std::optional<PatchGrid> parse(const std::vector<std::string>&,std::string_view); std::map<char,int> count_patch(int,int,int,int) const; }; }", ["empty or ragged grid rejects", "unknown and duplicate allowed codes reject", "patch coordinates clip", "reversed rectangles return empty", "counts omit absent codes"], patch_files), editable={patch_files[0]: PATCH_START, patch_files[1]: support(patch_files[0], 93)}, reference={patch_files[0]: PATCH, patch_files[1]: support(patch_files[0], 94)}, hidden_name="garden-patch-repair_test.cpp", hidden=PATCH_TEST, category="rectangular-query", tags=["sanitizer-repair", "clipping", "grid", "header-frozen"]),
    ]
