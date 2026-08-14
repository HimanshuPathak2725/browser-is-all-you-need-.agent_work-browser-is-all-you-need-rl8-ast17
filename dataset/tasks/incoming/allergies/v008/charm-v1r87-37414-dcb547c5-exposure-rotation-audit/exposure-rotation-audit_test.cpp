#include "exposure-rotation-audit.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::allergies;
int main() {
require_case(audit_exposure_rotation({{1,"a"},{3,"b"},{4,"a"}},{{"a",5},{"b",0}}).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{0,2}}));
require_case(audit_exposure_rotation({},{}).value().empty());
require_case(!audit_exposure_rotation({{1,"x"}},{}));
require_case(!audit_exposure_rotation({{2,"a"},{2,"a"}},{{"a",1}}));
require_case(audit_exposure_rotation({{1,"a"},{6,"a"}},{{"a",5}}).value().empty());
return 0;
}
