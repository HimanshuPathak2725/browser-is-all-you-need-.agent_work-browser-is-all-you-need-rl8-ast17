#include "closed-conversion-cycle.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::bank_account;
int main() {
require_case(closes_exact_conversion_cycle(10,{{3,2},{2,3}})==true);
require_case(closes_exact_conversion_cycle(10,{{2,1}})==false);
require_case(!closes_exact_conversion_cycle(5,{{1,2}}));
require_case(!closes_exact_conversion_cycle(0,{}));
require_case(!closes_exact_conversion_cycle(2,{{0,1}}));
return 0;
}
