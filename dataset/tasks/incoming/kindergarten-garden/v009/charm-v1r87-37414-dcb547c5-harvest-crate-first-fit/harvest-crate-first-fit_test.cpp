#include "harvest-crate-first-fit.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::kindergarten_garden;
int main() {
CHECK(first_fit_harvest_crates({6,4,5,5},10).value()==std::vector<std::size_t>({0,0,1,1}));
CHECK(first_fit_harvest_crates({},10).value().empty());
CHECK(first_fit_harvest_crates({4,7,3},10).value()==std::vector<std::size_t>({0,1,0}));
CHECK(!first_fit_harvest_crates({11},10));
CHECK(!first_fit_harvest_crates({1},0));
return 0;
}
