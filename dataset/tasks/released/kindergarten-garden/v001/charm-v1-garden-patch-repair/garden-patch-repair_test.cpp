#include "garden-patch-repair.h"
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
