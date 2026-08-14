#include "harvest-crate-first-fit.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
require_case(first_fit_harvest_crates({6,4,5,5},10).value()==std::vector<std::size_t>({0,0,1,1}));
require_case(first_fit_harvest_crates({},10).value().empty());
require_case(first_fit_harvest_crates({4,7,3},10).value()==std::vector<std::size_t>({0,1,0}));
require_case(!first_fit_harvest_crates({11},10));
require_case(!first_fit_harvest_crates({1},0));
return 0;
}
