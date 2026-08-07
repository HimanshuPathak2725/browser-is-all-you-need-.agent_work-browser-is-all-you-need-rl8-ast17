#include "transactional-ring-batches.cpp"

#include <cassert>

using namespace charm::v1n7::circular_buffer;
int main() {
    auto r=apply_ring_batches(3,true,{{1,2},{3,4},{5}});assert(r&&r->values==(std::vector<int>{1,2,5})&&r->accepted==(std::vector<bool>{true,false,true}));
    auto o=apply_ring_batches(2,false,{{1,2,3}});assert(o&&o->values==(std::vector<int>{2,3}));
    assert(apply_ring_batches(0,true,{{}})->accepted==std::vector<bool>{true});
    assert(!apply_ring_batches(0,false,{{1}}));
    assert(apply_ring_batches(2,true,{})->values.empty());
    return 0;
}
