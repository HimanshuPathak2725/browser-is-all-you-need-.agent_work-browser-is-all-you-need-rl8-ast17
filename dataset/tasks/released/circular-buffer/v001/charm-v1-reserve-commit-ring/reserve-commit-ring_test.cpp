#include "reserve-commit-ring.cpp"
#include <cassert>
using charm::ring::CommitRing;
int main() {
    CommitRing ring(2);
    const auto first = ring.reserve();
    const auto second = ring.reserve();
    assert(first && second && !ring.reserve());
    assert(ring.commit(*second, 20));
    assert(!ring.pop().has_value());
    assert(ring.cancel(*first));
    assert(ring.pop() == 20);
    assert(!ring.commit(*second, 99) && !ring.cancel(*second));
    const auto third = ring.reserve();
    assert(third && ring.commit(*third, -4) && ring.pop() == -4);
    assert(!ring.pop().has_value());
    return 0;
}
