#pragma once

#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1r87_37414::bank_account {
struct StandingOrder { int requested_day; std::int64_t amount; };
std::optional<std::map<int,std::int64_t>> settle_standing_orders(const std::vector<StandingOrder>& orders, int weekday_of_day_zero, const std::set<int>& holidays);
}

namespace charm::v1r87_37414::bank_account {
inline std::optional<std::map<int,std::int64_t>> settle_standing_orders(const std::vector<StandingOrder>& orders, int weekday_of_day_zero, const std::set<int>& holidays) {
if(weekday_of_day_zero<0||weekday_of_day_zero>6)return std::nullopt;
for(int h:holidays)if(h<0)return std::nullopt;
std::map<int,std::int64_t> out;
for(const auto&o:orders){if(o.requested_day<0||o.amount<=0)return std::nullopt;
int d=o.requested_day;
while(((weekday_of_day_zero+d)%7)>=5||holidays.count(d)){if(d==std::numeric_limits<int>::max())return std::nullopt;
++d;
}auto&v=out[d];
if(v>std::numeric_limits<std::int64_t>::max()-o.amount)return std::nullopt;
v+=o.amount;
}return out;

}
}
