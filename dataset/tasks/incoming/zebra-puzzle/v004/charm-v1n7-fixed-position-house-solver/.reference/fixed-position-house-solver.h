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

namespace charm::v1n7::zebra_puzzle {
struct FixedHouseClue { std::string item; std::size_t position; }; struct HouseAssignment { std::vector<std::string> item_at_position; };
std::optional<HouseAssignment> solve_house_assignment(std::size_t house_count, const std::vector<std::string>& items, const std::vector<FixedHouseClue>& clues);
}
