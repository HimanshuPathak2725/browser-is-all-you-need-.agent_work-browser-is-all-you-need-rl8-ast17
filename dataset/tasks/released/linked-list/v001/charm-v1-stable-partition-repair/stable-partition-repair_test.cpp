#include "stable-partition-repair.h"
#include <cassert>
#include <vector>
using charm::list::StableList;
int main() {
    StableList empty; empty.partition(3); assert(empty.values().empty());
    StableList list; for (int value : {5,1,4,2,3,2}) list.push_back(value);
    list.partition(3);
    assert((list.values() == std::vector<int>{1,2,2,5,4,3}));
    list.partition(3);
    assert((list.values() == std::vector<int>{1,2,2,5,4,3}));
    StableList low; for (int value : {1,2}) low.push_back(value); low.partition(9);
    assert((low.values() == std::vector<int>{1,2}));
    StableList high; for (int value : {9,8}) high.push_back(value); high.partition(0);
    assert((high.values() == std::vector<int>{9,8}));
    return 0;
}
