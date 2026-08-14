#include "crop-rotation-audit.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
CHECK(audit_crop_rotation({{"pea","corn"},{"bean","corn"}},1).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{1,1}}));
CHECK(audit_crop_rotation({{"a"},{"b"},{"a"}},1).value().empty());
CHECK(audit_crop_rotation({{"a"},{"b"},{"a"}},2).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{2,0}}));
CHECK(!audit_crop_rotation({},1));
CHECK(!audit_crop_rotation({{"A"}},1));
return 0;
}
