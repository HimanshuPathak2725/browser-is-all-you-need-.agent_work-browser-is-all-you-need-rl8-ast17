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
enum class RingOpKind { push, pop, clear }; struct RingOp { RingOpKind kind; std::string value; }; struct RingReplay { std::vector<std::string> remaining; std::vector<std::string> popped; };
std::optional<RingReplay> replay_string_ring(std::size_t capacity, bool overwrite, const std::vector<RingOp>& operations);
}
