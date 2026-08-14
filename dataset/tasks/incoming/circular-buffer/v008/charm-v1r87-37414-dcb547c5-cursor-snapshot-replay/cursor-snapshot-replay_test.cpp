#include "cursor-snapshot-replay.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::circular_buffer;
int main() {
require_case(replay_ring_snapshots(3,{{"push","",1},{"save","a",0},{"push","",2},{"restore","a",0}}).value()==std::vector<int>{1});
require_case(replay_ring_snapshots(0,{}).value().empty());
require_case(!replay_ring_snapshots(1,{{"push","",1},{"push","",2}}));
require_case(!replay_ring_snapshots(2,{{"restore","x",0}}));
require_case(!replay_ring_snapshots(2,{{"save","x",0},{"save","x",0}}));
return 0;
}
