#include "wrapped-slice-repair.hpp"
#include <cassert>
#include <vector>
using charm::ring::SliceRing;
int main() {
    SliceRing ring(3);
    assert(ring.slice(0, 2).empty() && ring.size() == 0);
    for (int value : {1, 2, 3, 4}) ring.push(value);
    assert(ring.size() == 3 && (ring.slice(0, 9) == std::vector<int>{2, 3, 4}));
    assert((ring.slice(-1, 3) == std::vector<int>{4}));
    assert((ring.slice(-3, 2) == std::vector<int>{2, 3}));
    assert((ring.slice(-99, 1) == std::vector<int>{2}));
    assert(ring.slice(3, 1).empty());
    SliceRing zero(0); zero.push(8); assert(zero.size() == 0);
    return 0;
}
