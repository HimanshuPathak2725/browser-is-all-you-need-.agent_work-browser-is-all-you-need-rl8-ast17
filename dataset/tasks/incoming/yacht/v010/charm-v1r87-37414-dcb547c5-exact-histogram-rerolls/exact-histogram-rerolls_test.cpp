#include "exact-histogram-rerolls.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::yacht;
int main() {
CHECK(minimum_exact_histogram_rerolls({1,1,2},3,{1,1,1})==1);
CHECK(minimum_exact_histogram_rerolls({2,2},2,{0,2})==0);
CHECK(minimum_exact_histogram_rerolls({},1,{0})==0);
CHECK(!minimum_exact_histogram_rerolls({1},0,{}));
CHECK(!minimum_exact_histogram_rerolls({3},2,{1,0}));
return 0;
}
