#include "interval-coverage-tree.cpp"
#include <cassert>
#include <string>
#include <vector>
using charm::bst::IntervalIndex;
int main() {
    IntervalIndex index;
    assert(!index.add(4, 3, "reverse") && !index.add(1, 2, ""));
    assert(index.add(-2, 2, "wide"));
    assert(index.add(0, 0, "point"));
    assert(index.add(-1, 1, "beta") && index.add(-1, 1, "alpha"));
    assert((index.containing(0) == std::vector<std::string>{"point", "alpha", "beta", "wide"}));
    assert((index.containing(2) == std::vector<std::string>{"wide"}));
    assert(index.containing(3).empty());
    assert(index.add(2, 2, "edge") && (index.containing(2) == std::vector<std::string>{"edge", "wide"}));
    return 0;
}
