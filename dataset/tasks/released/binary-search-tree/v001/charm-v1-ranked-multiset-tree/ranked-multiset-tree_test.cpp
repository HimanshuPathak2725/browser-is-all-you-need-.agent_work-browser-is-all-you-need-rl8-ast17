#include "ranked-multiset-tree.h"
#include <cassert>
#include <optional>
using charm::bst::RankedTree;
int main() {
    RankedTree tree;
    assert(!tree.kth(0).has_value() && tree.rank(5) == 0);
    for (int value : {5, 2, 5, 1, 9}) tree.insert(value);
    assert(tree.kth(0) == std::optional<int>(1));
    assert(tree.kth(3) == std::optional<int>(5));
    assert(tree.rank(5) == 2);
    assert(tree.erase_one(5) && tree.rank(9) == 3);
    assert(tree.kth(2) == std::optional<int>(5));
    assert(!tree.erase_one(7) && !tree.kth(4).has_value());
    assert(tree.erase_one(1) && tree.kth(0) == std::optional<int>(2));
    return 0;
}
