#include "string-ring-lifetime-replay.h"

#include <cassert>

using namespace charm::v1n7::circular_buffer;
int main() {
    auto r=replay_string_ring(2,true,{{RingOpKind::push,"a"},{RingOpKind::push,"b"},{RingOpKind::push,"c"},{RingOpKind::pop,""}});assert(r&&r->popped==std::vector<std::string>{"b"}&&r->remaining==std::vector<std::string>{"c"});
    assert(replay_string_ring(0,false,{{RingOpKind::clear,""}})->remaining.empty());
    assert(!replay_string_ring(0,true,{{RingOpKind::push,"x"}}));
    assert(!replay_string_ring(1,false,{{RingOpKind::pop,""}}));
    assert(!replay_string_ring(1,false,{{RingOpKind::push,"x"},{RingOpKind::push,"y"}}));
    return 0;
}
