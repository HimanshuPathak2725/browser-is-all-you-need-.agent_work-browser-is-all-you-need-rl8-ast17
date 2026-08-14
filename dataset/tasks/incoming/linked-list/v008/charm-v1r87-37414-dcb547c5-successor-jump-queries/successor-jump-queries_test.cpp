#include "successor-jump-queries.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::linked_list;
int main() {
require_case(successor_jump_queries({1,2,-1},{{0,0},{0,2},{0,3}}).value()==std::vector<int>({0,2,-1}));
require_case(successor_jump_queries({0},{{0,999}}).value()==std::vector<int>{0});
require_case(successor_jump_queries({},{}).value().empty());
require_case(!successor_jump_queries({2},{}));
require_case(!successor_jump_queries({-1},{{1,0}}));
return 0;
}
