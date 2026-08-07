#pragma once
#include <algorithm>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
namespace charm::garden {
class PatchGrid {
public:
    static std::optional<PatchGrid> parse(const std::vector<std::string>& rows, std::string_view allowed) {
        if (rows.empty() || rows.front().empty() || allowed.empty()) return std::nullopt;
        std::set<char> codes(allowed.begin(), allowed.end());
        if (codes.size() != allowed.size()) return std::nullopt;
        for (const std::string& row : rows) {
            if (row.size() != rows.front().size()) return std::nullopt;
            for (char plant : row) if (codes.count(plant) == 0U) return std::nullopt;
        }
        return PatchGrid(rows);
    }
    std::map<char,int> count_patch(int x0, int y0, int x1, int y1) const {
        if (x0 > x1 || y0 > y1) return {};
        x0 = std::max(x0, 0); y0 = std::max(y0, 0);
        x1 = std::min(x1, static_cast<int>(rows_.size()));
        y1 = std::min(y1, static_cast<int>(rows_.size()));
        std::map<char,int> counts;
        for (int y = y0; y < y1; ++y) for (int x = x0; x < x1; ++x) ++counts[rows_[y][x]];
        return counts;
    }
private:
    explicit PatchGrid(std::vector<std::string> rows) : rows_(std::move(rows)) {}
    std::vector<std::string> rows_;
};
}
