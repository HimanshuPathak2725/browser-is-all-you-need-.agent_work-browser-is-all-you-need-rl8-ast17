#include "generation-overwrite-ring.h"
#include <cassert>
#include <vector>
using charm::ring::OverwriteRing;
int main() {
    OverwriteRing ring(2);
    const auto a = ring.push(10);
    const auto b = ring.push(20);
    assert((ring.snapshot() == std::vector<int>{10, 20}));
    assert(ring.read(a) == 10 && ring.read(b) == 20);
    const auto c = ring.push(30);
    assert(!ring.read(a).has_value() && ring.read(c) == 30);
    assert((ring.snapshot() == std::vector<int>{20, 30}));
    const auto d = ring.push(40);
    assert(!ring.read(b).has_value() && ring.read(d) == 40);
    OverwriteRing empty(0);
    const auto invalid = empty.push(1);
    assert(!empty.read(invalid).has_value() && empty.snapshot().empty());
    return 0;
}
