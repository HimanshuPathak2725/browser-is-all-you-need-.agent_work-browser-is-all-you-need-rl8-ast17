#include "quota-lane-drain.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::circular_buffer;
int main() {
CHECK(drain_fifo_lanes({{1,2,3},{9,8}},{2,1}).value()==std::vector<int>({1,2,9,3,8}));
CHECK(drain_fifo_lanes({},{}).value().empty());
CHECK(drain_fifo_lanes({{}, {1}},{1,2}).value()==std::vector<int>{1});
CHECK(!drain_fifo_lanes({{1}},{0}));
CHECK(!drain_fifo_lanes({{1}},{}));
return 0;
}
