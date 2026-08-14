#include "eastward-shadow-profile.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
CHECK(eastward_shadow_profile({5,2,2},1).value()==std::vector<bool>({false,true,true}));
CHECK(eastward_shadow_profile({1,2,3},1).value()==std::vector<bool>({false,false,false}));
CHECK(eastward_shadow_profile({},2).value().empty());
CHECK(!eastward_shadow_profile({1},0));
CHECK(!eastward_shadow_profile({-1},1));
return 0;
}
