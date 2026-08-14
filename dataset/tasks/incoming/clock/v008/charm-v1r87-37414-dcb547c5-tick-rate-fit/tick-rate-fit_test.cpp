#include "tick-rate-fit.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::clock;
int main() {
require_case(fit_exact_tick_rate({{0,0},{2,3},{4,6}}).value()==std::pair<std::int64_t,std::int64_t>{3,2});
require_case(fit_exact_tick_rate({{1,5},{3,5}}).value()==std::pair<std::int64_t,std::int64_t>{0,1});
require_case(!fit_exact_tick_rate({{0,0}}));
require_case(!fit_exact_tick_rate({{0,0},{0,1}}));
require_case(!fit_exact_tick_rate({{0,0},{2,2},{3,4}}));
return 0;
}
