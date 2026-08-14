#include "minimum-unique-clue-subset.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
require_case(minimum_unique_clue_subset(7,0,{2,4,6}).value()==std::vector<std::size_t>{2});
require_case(minimum_unique_clue_subset(1,0,{}).value().empty());
require_case(minimum_unique_clue_subset(3,0,{}).value().empty());
require_case(!minimum_unique_clue_subset(0,0,{}));
require_case(!minimum_unique_clue_subset(3,0,{1}));
return 0;
}
