#include "successor-thread-audit.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
require_case(audit_successor_threads({{2,1,2,2},{1,-1,-1,0},{3,-1,-1,-1}},0).value().empty());
require_case(audit_successor_threads({{2,1,2,-1},{1,-1,-1,0},{3,-1,-1,-1}},0).value()==std::vector<int>{0});
require_case(audit_successor_threads({},-1).value().empty());
require_case(!audit_successor_threads({{1,0,-1,-1}},0));
require_case(!audit_successor_threads({{2,-1,-1,-1},{1,-1,-1,-1}},0));
return 0;
}
