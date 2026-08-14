#include "decontamination-cover.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::allergies;
int main() {
CHECK(minimum_cleaning_cover({1,2,3},3,3).value()==std::vector<std::size_t>{2});
CHECK(minimum_cleaning_cover({1,2},3,3).value()==(std::vector<std::size_t>{0,1}));
CHECK(minimum_cleaning_cover({},0,7).value().empty());
CHECK(minimum_cleaning_cover({},1,1).value().empty());
CHECK(!minimum_cleaning_cover({8},1,3));
return 0;
}
