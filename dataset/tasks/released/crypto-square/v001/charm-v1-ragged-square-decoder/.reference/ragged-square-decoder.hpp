#pragma once
#include <cctype>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>
namespace charm::cryptosquare {
inline std::optional<std::string> decode_columns(std::string_view encoded) {
    std::istringstream input{std::string(encoded)};
    std::vector<std::string> columns;
    for (std::string column; input >> column;) columns.push_back(column);
    if (columns.empty()) return std::string{};
    const std::size_t high = columns.front().size();
    if (high == 0) return std::nullopt;
    bool saw_short = false;
    for (const std::string& column : columns) {
        if (column.size() + 1 < high || column.size() > high) return std::nullopt;
        if (column.size() < high) saw_short = true;
        else if (saw_short) return std::nullopt;
        for (unsigned char ch : column) if (!std::isalnum(ch)) return std::nullopt;
    }
    std::string out;
    for (std::size_t row = 0; row < high; ++row)
        for (const std::string& column : columns) if (row < column.size()) out.push_back(column[row]);
    return out;
}
}
