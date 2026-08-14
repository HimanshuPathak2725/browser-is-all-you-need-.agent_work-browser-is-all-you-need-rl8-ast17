#include "closed-conversion-cycle.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::bank_account;
int main() {
CHECK(closes_exact_conversion_cycle(10,{{3,2},{2,3}})==true);
CHECK(closes_exact_conversion_cycle(10,{{2,1}})==false);
CHECK(!closes_exact_conversion_cycle(5,{{1,2}}));
CHECK(!closes_exact_conversion_cycle(0,{}));
CHECK(!closes_exact_conversion_cycle(2,{{0,1}}));
return 0;
}
