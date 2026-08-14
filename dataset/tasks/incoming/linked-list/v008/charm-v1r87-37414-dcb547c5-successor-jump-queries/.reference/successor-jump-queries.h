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

namespace charm::v1r87_37414::linked_list {
struct JumpQuery { int start; std::uint64_t steps; };
std::optional<std::vector<int>> successor_jump_queries(const std::vector<int>& next, const std::vector<JumpQuery>& queries);
}
