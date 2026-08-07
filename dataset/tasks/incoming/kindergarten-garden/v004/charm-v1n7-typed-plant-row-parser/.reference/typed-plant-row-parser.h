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

namespace charm::v1n7::kindergarten_garden {
enum class PlantCode { clover, grass, radish, violet }; using ChildPlants = std::pair<std::string,std::array<PlantCode,4>>;
std::optional<std::vector<ChildPlants>> parse_typed_garden(std::string_view top, std::string_view bottom, const std::vector<std::string>& children);
}
