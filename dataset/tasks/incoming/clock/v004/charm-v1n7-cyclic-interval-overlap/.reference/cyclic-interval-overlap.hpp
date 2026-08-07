#pragma once

#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
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

namespace charm::v1n7::clock {
struct DailyInterval { int start_minute; int duration; };
std::optional<int> cyclic_overlap_minutes(DailyInterval first, DailyInterval second);
}

inline std::optional<int> charm::v1n7::clock::cyclic_overlap_minutes(charm::v1n7::clock::DailyInterval first, charm::v1n7::clock::DailyInterval second) {
    auto valid=[](DailyInterval x){return x.start_minute>=0&&x.start_minute<1440&&x.duration>=0&&x.duration<=1440;};if(!valid(first)||!valid(second))return std::nullopt;int total=0;for(int minute=0;minute<1440;++minute){auto inside=[&](DailyInterval x){int delta=(minute-x.start_minute+1440)%1440;return delta<x.duration;};if(inside(first)&&inside(second))++total;}return total;
}
