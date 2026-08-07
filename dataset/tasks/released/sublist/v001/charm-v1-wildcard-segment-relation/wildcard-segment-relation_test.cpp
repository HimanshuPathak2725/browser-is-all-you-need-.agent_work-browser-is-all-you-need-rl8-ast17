#include "wildcard-segment-relation.h"
#include <cassert>
using charm::sublist::Relation;
using charm::sublist::wildcard_relation;
int main() {
    assert(wildcard_relation({}, {}, -1) == Relation::equal);
    assert(wildcard_relation({1,-1,3}, {1,2,3}, -1) == Relation::equal);
    assert(wildcard_relation({2,-1}, {0,2,9,4}, -1) == Relation::subpattern);
    assert(wildcard_relation({0,2,9,4}, {2,-1}, -1) == Relation::superpattern);
    assert(wildcard_relation({1,2}, {1,3}, -1) == Relation::unequal);
    assert(wildcard_relation({}, {1}, -1) == Relation::subpattern);
    assert(wildcard_relation({1}, {}, -1) == Relation::superpattern);
    assert(wildcard_relation({-1}, {99}, -1) == Relation::equal);
    return 0;
}
