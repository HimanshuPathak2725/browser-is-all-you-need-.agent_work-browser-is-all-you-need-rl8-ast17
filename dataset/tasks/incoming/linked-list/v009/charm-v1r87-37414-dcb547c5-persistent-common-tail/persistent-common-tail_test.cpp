#include "persistent-common-tail.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::linked_list;
int main() {
CHECK(persistent_common_tail({2,2,3,-1},0,1)==2);
CHECK(persistent_common_tail({1,-1,3,-1},0,2)==-1);
CHECK(persistent_common_tail({},-1,-1)==-1);
CHECK(!persistent_common_tail({0},0,-1));
CHECK(!persistent_common_tail({2},0,-1));
return 0;
}
