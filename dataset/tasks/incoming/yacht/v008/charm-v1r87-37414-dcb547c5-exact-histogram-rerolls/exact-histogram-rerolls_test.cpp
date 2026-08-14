#include "exact-histogram-rerolls.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::yacht;
int main() {
require_case(minimum_exact_histogram_rerolls({1,1,2},3,{1,1,1})==1);
require_case(minimum_exact_histogram_rerolls({2,2},2,{0,2})==0);
require_case(minimum_exact_histogram_rerolls({},1,{0})==0);
require_case(!minimum_exact_histogram_rerolls({1},0,{}));
require_case(!minimum_exact_histogram_rerolls({3},2,{1,0}));
return 0;
}
