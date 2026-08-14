#include "crop-rotation-audit.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
require_case(audit_crop_rotation({{"pea","corn"},{"bean","corn"}},1).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{1,1}}));
require_case(audit_crop_rotation({{"a"},{"b"},{"a"}},1).value().empty());
require_case(audit_crop_rotation({{"a"},{"b"},{"a"}},2).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{2,0}}));
require_case(!audit_crop_rotation({},1));
require_case(!audit_crop_rotation({{"A"}},1));
return 0;
}
