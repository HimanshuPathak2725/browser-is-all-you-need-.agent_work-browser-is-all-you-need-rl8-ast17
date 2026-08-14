#include "equal-sum-dice-partition.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::yacht;
int main() {
require_case(equal_sum_dice_partition({1,1}).value()==std::vector<std::size_t>{0});
require_case(equal_sum_dice_partition({1,2,3}).value()==std::vector<std::size_t>({0,1}));
require_case(equal_sum_dice_partition({1,2}).value().empty());
require_case(!equal_sum_dice_partition({1}));
require_case(!equal_sum_dice_partition({1,0}));
return 0;
}
