#include "tick-rate-fit.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::clock;
int main() {
CHECK(fit_exact_tick_rate({{0,0},{2,3},{4,6}}).value()==std::pair<std::int64_t,std::int64_t>{3,2});
CHECK(fit_exact_tick_rate({{1,5},{3,5}}).value()==std::pair<std::int64_t,std::int64_t>{0,1});
CHECK(!fit_exact_tick_rate({{0,0}}));
CHECK(!fit_exact_tick_rate({{0,0},{0,1}}));
CHECK(!fit_exact_tick_rate({{0,0},{2,2},{3,4}}));
return 0;
}
