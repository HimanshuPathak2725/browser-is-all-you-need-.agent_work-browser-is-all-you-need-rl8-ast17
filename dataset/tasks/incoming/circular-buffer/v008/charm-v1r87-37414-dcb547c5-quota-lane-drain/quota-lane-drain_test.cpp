#include "quota-lane-drain.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::circular_buffer;
int main() {
require_case(drain_fifo_lanes({{1,2,3},{9,8}},{2,1}).value()==std::vector<int>({1,2,9,3,8}));
require_case(drain_fifo_lanes({},{}).value().empty());
require_case(drain_fifo_lanes({{}, {1}},{1,2}).value()==std::vector<int>{1});
require_case(!drain_fifo_lanes({{1}},{0}));
require_case(!drain_fifo_lanes({{1}},{}));
return 0;
}
