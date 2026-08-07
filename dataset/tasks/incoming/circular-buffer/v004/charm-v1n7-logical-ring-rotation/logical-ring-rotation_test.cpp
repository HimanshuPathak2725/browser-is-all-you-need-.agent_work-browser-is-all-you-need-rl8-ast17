#include "logical-ring-rotation.hpp"

#include <cassert>

using charm::v1n7::circular_buffer::rotate_ring_snapshot;
int main() {
    assert((rotate_ring_snapshot({1,2,3,4},1)==std::vector<int>{2,3,4,1}));
    assert((rotate_ring_snapshot({1,2,3,4},-1)==std::vector<int>{4,1,2,3}));
    assert(rotate_ring_snapshot({},99).empty());
    assert((rotate_ring_snapshot({7},-100)==std::vector<int>{7}));
    assert((rotate_ring_snapshot({1,2},4)==std::vector<int>{1,2}));
    return 0;
}
