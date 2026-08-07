#include "rotating-garden-seats.cpp"
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
