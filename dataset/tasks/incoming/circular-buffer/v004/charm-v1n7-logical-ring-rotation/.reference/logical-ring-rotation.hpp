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

namespace charm::v1n7::circular_buffer {

std::vector<int> rotate_ring_snapshot(std::vector<int> values, long long offset);
}

inline std::vector<int> charm::v1n7::circular_buffer::rotate_ring_snapshot(std::vector<int> values, long long offset) {
    if (values.empty()) return values;
    long long n=static_cast<long long>(values.size());long long shift=offset%n;if(shift<0)shift+=n;std::rotate(values.begin(),values.begin()+shift,values.end());return values;
}
