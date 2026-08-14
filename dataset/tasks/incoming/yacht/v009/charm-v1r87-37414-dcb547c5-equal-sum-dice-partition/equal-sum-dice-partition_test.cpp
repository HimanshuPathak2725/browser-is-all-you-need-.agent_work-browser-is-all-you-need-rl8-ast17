#include "equal-sum-dice-partition.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::yacht;
int main() {
CHECK(equal_sum_dice_partition({1,1}).value()==std::vector<std::size_t>{0});
CHECK(equal_sum_dice_partition({1,2,3}).value()==std::vector<std::size_t>({0,1}));
CHECK(equal_sum_dice_partition({1,2}).value().empty());
CHECK(!equal_sum_dice_partition({1}));
CHECK(!equal_sum_dice_partition({1,0}));
return 0;
}
