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

namespace charm::v1n7::allergies {
struct MaskedMeal { std::string id; std::uint32_t allergens; };
std::optional<std::vector<std::string>> meals_avoiding_mask(const std::vector<MaskedMeal>& meals, std::uint32_t known_mask, std::uint32_t blocked_mask);
}

inline std::optional<std::vector<std::string>> charm::v1n7::allergies::meals_avoiding_mask(const std::vector<charm::v1n7::allergies::MaskedMeal>& meals, std::uint32_t known_mask, std::uint32_t blocked_mask) {
    if ((blocked_mask & ~known_mask) != 0U) return std::nullopt;
    std::set<std::string> ids;
    std::vector<std::string> result;
    for (const auto& meal : meals) {
        if (meal.id.empty() || !ids.insert(meal.id).second || (meal.allergens & ~known_mask) != 0U) return std::nullopt;
        if ((meal.allergens & blocked_mask) == 0U) result.push_back(meal.id);
    }
    return result;
}
