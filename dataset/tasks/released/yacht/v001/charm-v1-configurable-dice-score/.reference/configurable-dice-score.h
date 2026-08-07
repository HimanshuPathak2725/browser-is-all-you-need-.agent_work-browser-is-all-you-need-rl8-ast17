#pragma once
#include <algorithm>
#include <map>
#include <optional>
#include <set>
#include <vector>
namespace charm::yacht {
enum class RuleKind { exact_group, straight, value_sum };
struct Category { RuleKind kind; int argument; };
inline std::optional<int> score(const std::vector<int>& dice, int sides, Category category) {
    if (dice.size() != 5 || sides < 1) return std::nullopt;
    std::map<int,int> counts;
    for (int die : dice) { if (die < 1 || die > sides) return std::nullopt; ++counts[die]; }
    if (category.kind == RuleKind::value_sum) {
        if (category.argument < 1 || category.argument > sides) return std::nullopt;
        return category.argument * counts[category.argument];
    }
    if (category.kind == RuleKind::exact_group) {
        if (category.argument < 1 || category.argument > 5) return std::nullopt;
        int best = 0;
        for (const auto& item : counts) if (item.second == category.argument) best = std::max(best, item.first * item.second);
        return best;
    }
    if (category.argument < 1 || category.argument > 5) return std::nullopt;
    std::vector<int> unique;
    for (const auto& item : counts) unique.push_back(item.first);
    if (unique.size() != static_cast<std::size_t>(category.argument)) return 0;
    for (std::size_t i = 1; i < unique.size(); ++i) if (unique[i] != unique[i-1] + 1) return 0;
    int total = 0; for (int die : dice) total += die; return total;
}
}
