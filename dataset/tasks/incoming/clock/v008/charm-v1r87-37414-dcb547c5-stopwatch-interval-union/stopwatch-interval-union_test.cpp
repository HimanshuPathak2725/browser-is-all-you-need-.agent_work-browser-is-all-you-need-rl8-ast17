#include "stopwatch-interval-union.hpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::clock;
int main() {
require_case(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().first==(std::vector<std::pair<std::int64_t,std::int64_t>>{{1,5},{9,9}}));
require_case(merge_stopwatch_intervals({{4,5},{1,3},{9,9}}).value().second==6);
require_case(merge_stopwatch_intervals({}).value().second==0);
require_case(!merge_stopwatch_intervals({{2,1}}));
require_case(!merge_stopwatch_intervals({{-1,2}}));
return 0;
}
