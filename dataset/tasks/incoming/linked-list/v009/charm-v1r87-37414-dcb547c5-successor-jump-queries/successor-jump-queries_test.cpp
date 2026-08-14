#include "successor-jump-queries.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::linked_list;
int main() {
CHECK(successor_jump_queries({1,2,-1},{{0,0},{0,2},{0,3}}).value()==std::vector<int>({0,2,-1}));
CHECK(successor_jump_queries({0},{{0,999}}).value()==std::vector<int>{0});
CHECK(successor_jump_queries({},{}).value().empty());
CHECK(!successor_jump_queries({2},{}));
CHECK(!successor_jump_queries({-1},{{1,0}}));
return 0;
}
