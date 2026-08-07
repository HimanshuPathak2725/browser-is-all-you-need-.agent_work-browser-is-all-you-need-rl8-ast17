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
class ExactClock { public: explicit ExactClock(int minute); int minutes_since_midnight() const; ExactClock operator+(long long delta) const; bool operator==(const ExactClock& other) const; private: int minute_; };
ExactClock make_exact_clock(long long hours, long long minutes);
}
