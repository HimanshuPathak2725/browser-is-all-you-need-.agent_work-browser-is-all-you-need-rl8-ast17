#include "eastward-shadow-profile.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
require_case(eastward_shadow_profile({5,2,2},1).value()==std::vector<bool>({false,true,true}));
require_case(eastward_shadow_profile({1,2,3},1).value()==std::vector<bool>({false,false,false}));
require_case(eastward_shadow_profile({},2).value().empty());
require_case(!eastward_shadow_profile({1},0));
require_case(!eastward_shadow_profile({-1},1));
return 0;
}
