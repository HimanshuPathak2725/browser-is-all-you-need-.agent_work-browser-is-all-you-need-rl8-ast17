#include "adjacency-placement-count.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
CHECK(count_adjacency_placements({"a","b","c"},{{"a",0}},{{"a","b"}})==1);
CHECK(count_adjacency_placements({"a","b"}, {},{{"a","b"}})==2);
CHECK(count_adjacency_placements({}, {},{})==1);
CHECK(!count_adjacency_placements({"a","a"}, {},{}));
CHECK(!count_adjacency_placements({"a"}, {},{{"a","a"}}));
return 0;
}
