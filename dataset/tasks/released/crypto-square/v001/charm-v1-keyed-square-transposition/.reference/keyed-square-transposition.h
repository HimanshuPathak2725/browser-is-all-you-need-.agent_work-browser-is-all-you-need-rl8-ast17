#pragma once
#include <algorithm>
#include <cctype>
#include <cmath>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
namespace charm::cryptosquare {
inline std::optional<std::string> encode_keyed(std::string_view input, const std::vector<std::size_t>& key) {
    std::string normalized;
    for (unsigned char ch : input) if (std::isalnum(ch)) normalized.push_back(static_cast<char>(std::tolower(ch)));
    if (normalized.empty()) return key.empty() ? std::optional<std::string>("") : std::nullopt;
    std::size_t rows = static_cast<std::size_t>(std::sqrt(static_cast<long double>(normalized.size())));
    if (rows == 0) rows = 1;
    std::size_t columns = (normalized.size() + rows - 1) / rows;
    while (columns > rows + 1) { ++rows; columns = (normalized.size() + rows - 1) / rows; }
    if (key.size() != columns) return std::nullopt;
    std::vector<bool> seen(columns, false);
    for (std::size_t value : key) { if (value >= columns || seen[value]) return std::nullopt; seen[value] = true; }
    normalized.resize(rows * columns, 'x');
    std::string out;
    for (std::size_t row = 0; row < rows; ++row) {
        if (row != 0) out.push_back(' ');
        for (std::size_t destination = 0; destination < columns; ++destination)
            out.push_back(normalized[row * columns + key[destination]]);
    }
    return out;
}
}
