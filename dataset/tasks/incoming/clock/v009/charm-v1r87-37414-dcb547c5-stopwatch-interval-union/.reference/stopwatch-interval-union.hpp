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

namespace charm::v1r87_37414::clock {

std::optional<std::pair<std::vector<std::pair<std::int64_t,std::int64_t>>,std::int64_t>> merge_stopwatch_intervals(std::vector<std::pair<std::int64_t,std::int64_t>> intervals);
}

namespace charm::v1r87_37414::clock {
inline std::optional<std::pair<std::vector<std::pair<std::int64_t,std::int64_t>>,std::int64_t>> merge_stopwatch_intervals(std::vector<std::pair<std::int64_t,std::int64_t>> intervals) {
for(auto [a,b]:intervals)if(a<0||a>b)return std::nullopt;
std::sort(intervals.begin(),intervals.end());
std::vector<std::pair<std::int64_t,std::int64_t>> out;
for(auto p:intervals){if(out.empty()||p.first>out.back().second+1)out.push_back(p);
else out.back().second=std::max(out.back().second,p.second);
}std::int64_t total=0;
for(auto [a,b]:out){if(b-a==std::numeric_limits<std::int64_t>::max()||total>std::numeric_limits<std::int64_t>::max()-(b-a+1))return std::nullopt;
total+=b-a+1;
}return std::pair{out,total};

}
}
