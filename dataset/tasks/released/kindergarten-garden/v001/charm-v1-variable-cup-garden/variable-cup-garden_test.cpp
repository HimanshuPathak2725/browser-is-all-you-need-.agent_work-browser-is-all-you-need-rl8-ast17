#include "variable-cup-garden.h"
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
