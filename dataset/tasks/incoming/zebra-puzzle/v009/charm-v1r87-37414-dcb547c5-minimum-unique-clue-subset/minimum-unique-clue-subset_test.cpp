#include "minimum-unique-clue-subset.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::zebra_puzzle;
int main() {
CHECK(minimum_unique_clue_subset(7,0,{2,4,6}).value()==std::vector<std::size_t>{2});
CHECK(minimum_unique_clue_subset(1,0,{}).value().empty());
CHECK(minimum_unique_clue_subset(3,0,{}).value().empty());
CHECK(!minimum_unique_clue_subset(0,0,{}));
CHECK(!minimum_unique_clue_subset(3,0,{1}));
return 0;
}
