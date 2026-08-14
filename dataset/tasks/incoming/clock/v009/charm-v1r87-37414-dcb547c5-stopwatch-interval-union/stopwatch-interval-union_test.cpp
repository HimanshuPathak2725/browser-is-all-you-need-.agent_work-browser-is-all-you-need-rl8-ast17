#include "stopwatch-interval-union.hpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::clock;
int main() {
CHECK(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().first==(std::vector<std::pair<std::int64_t,std::int64_t>>{{1,5},{9,9}}));
CHECK(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().second==6);
CHECK(merge_stopwatch_intervals({}).value().second==0);
CHECK(!merge_stopwatch_intervals({{2,1}}));
CHECK(!merge_stopwatch_intervals({{-1,2}}));
return 0;
}
