#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <vector>
namespace charm::zebra {
enum class ClueKind { same_house, adjacent, immediately_left };
struct Clue { ClueKind kind; std::string a; std::string b; };
inline bool core_satisfiable(
    int houses,
    const std::vector<std::vector<std::string>>& categories,
    const std::vector<Clue>& clues,
    const std::vector<std::size_t>& selected) {
    if (houses <= 0 || categories.empty()) return false;
    std::set<std::string> items;
    for (const auto& category : categories) {
        if (category.size() != static_cast<std::size_t>(houses)) return false;
        for (const auto& item : category) if (!items.insert(item).second) return false;
    }
    for (std::size_t index : selected)
        if (index >= clues.size() || items.count(clues[index].a) == 0U || items.count(clues[index].b) == 0U) return false;
    std::map<std::string,int> current;
    bool found = false;
    std::function<void(std::size_t)> search = [&](std::size_t category_index) {
        if (found) return;
        if (category_index == categories.size()) {
            for (std::size_t index : selected) {
                const auto& clue = clues[index];
                const int a = current[clue.a];
                const int b = current[clue.b];
                if (clue.kind == ClueKind::same_house && a != b) return;
                if (clue.kind == ClueKind::adjacent && std::abs(a - b) != 1) return;
                if (clue.kind == ClueKind::immediately_left && a + 1 != b) return;
            }
            found = true;
            return;
        }
        std::vector<int> order(static_cast<std::size_t>(houses));
        std::iota(order.begin(), order.end(), 0);
        do {
            for (int house = 0; house < houses; ++house)
                current[categories[category_index][static_cast<std::size_t>(house)]] = order[static_cast<std::size_t>(house)];
            search(category_index + 1);
        } while (std::next_permutation(order.begin(), order.end()));
    };
    search(0);
    return found;
}
inline std::vector<std::size_t> contradiction_core(
    int houses,
    const std::vector<std::vector<std::string>>& categories,
    const std::vector<Clue>& clues) {
    std::vector<std::size_t> core(clues.size());
    std::iota(core.begin(), core.end(), 0);
    if (core_satisfiable(houses, categories, clues, core)) return {};
    for (std::size_t position = 0; position < core.size();) {
        auto candidate = core;
        candidate.erase(candidate.begin() + static_cast<long long>(position));
        if (!core_satisfiable(houses, categories, clues, candidate)) core = std::move(candidate);
        else ++position;
    }
    return core;
}
}
