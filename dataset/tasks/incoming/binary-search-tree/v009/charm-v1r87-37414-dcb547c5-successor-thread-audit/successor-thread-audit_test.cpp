#include "successor-thread-audit.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
CHECK(audit_successor_threads({{2,1,2,2},{1,-1,-1,0},{3,-1,-1,-1}},0).value().empty());
CHECK(audit_successor_threads({{2,1,2,-1},{1,-1,-1,0},{3,-1,-1,-1}},0).value()==std::vector<int>{0});
CHECK(audit_successor_threads({},-1).value().empty());
CHECK(!audit_successor_threads({{1,0,-1,-1}},0));
CHECK(!audit_successor_threads({{2,-1,-1,-1},{1,-1,-1,-1}},0));
return 0;
}
