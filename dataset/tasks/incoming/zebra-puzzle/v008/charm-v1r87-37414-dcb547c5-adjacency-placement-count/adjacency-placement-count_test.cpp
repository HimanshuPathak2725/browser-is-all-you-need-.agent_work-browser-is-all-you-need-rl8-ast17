#include "adjacency-placement-count.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
require_case(count_adjacency_placements({"a","b","c"},{{"a",0}},{{"a","b"}})==1);
require_case(count_adjacency_placements({"a","b"}, {},{{"a","b"}})==2);
require_case(count_adjacency_placements({}, {},{})==1);
require_case(!count_adjacency_placements({"a","a"}, {},{}));
require_case(!count_adjacency_placements({"a"}, {},{{"a","a"}}));
return 0;
}
