#include "exposure-rotation-audit.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::allergies;
int main() {
CHECK(audit_exposure_rotation({{1,"a"},{3,"b"},{4,"a"}},{{"a",5},{"b",0}}).value()==(std::vector<std::pair<std::size_t,std::size_t>>{{0,2}}));
CHECK(audit_exposure_rotation({},{}).value().empty());
CHECK(!audit_exposure_rotation({{1,"x"}},{}));
CHECK(!audit_exposure_rotation({{2,"a"},{2,"a"}},{{"a",1}}));
CHECK(audit_exposure_rotation({{1,"a"},{6,"a"}},{{"a",5}}).value().empty());
return 0;
}
