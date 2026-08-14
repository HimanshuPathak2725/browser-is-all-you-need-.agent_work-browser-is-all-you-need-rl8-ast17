#include "decontamination-cover.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::allergies;
int main() {
require_case(minimum_cleaning_cover({1,2,3},3,3).value()==std::vector<std::size_t>{2});
require_case(minimum_cleaning_cover({1,2},3,3).value()==(std::vector<std::size_t>{0,1}));
require_case(minimum_cleaning_cover({},0,7).value().empty());
require_case(minimum_cleaning_cover({},1,1).value().empty());
require_case(!minimum_cleaning_cover({8},1,3));
return 0;
}
