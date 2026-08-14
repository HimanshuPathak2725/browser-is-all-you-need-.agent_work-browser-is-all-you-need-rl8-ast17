#include "cursor-snapshot-replay.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::circular_buffer;
int main() {
CHECK(replay_ring_snapshots(3,{{"push","",1},{"save","a",0},{"push","",2},{"restore","a",0}}).value()==std::vector<int>{1});
CHECK(replay_ring_snapshots(0,{}).value().empty());
CHECK(!replay_ring_snapshots(1,{{"push","",1},{"push","",2}}));
CHECK(!replay_ring_snapshots(2,{{"restore","x",0}}));
CHECK(!replay_ring_snapshots(2,{{"save","x",0},{"save","x",0}}));
return 0;
}
