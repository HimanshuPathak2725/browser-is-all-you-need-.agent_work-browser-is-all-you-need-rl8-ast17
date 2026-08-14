#include "persistent-common-tail.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::linked_list;
int main() {
require_case(persistent_common_tail({2,2,3,-1},0,1)==2);
require_case(persistent_common_tail({1,-1,3,-1},0,2)==-1);
require_case(persistent_common_tail({},-1,-1)==-1);
require_case(!persistent_common_tail({0},0,-1));
require_case(!persistent_common_tail({2},0,-1));
return 0;
}
