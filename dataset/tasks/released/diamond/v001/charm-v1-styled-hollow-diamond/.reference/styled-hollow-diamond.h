#pragma once
#include <cstdlib>
#include <optional>
#include <string>
#include <vector>
namespace charm::diamond {
inline std::optional<std::vector<std::string>> render_hollow(int height, char edge, char background) {
    if (height <= 0 || height % 2 == 0 || edge == '\n' || background == '\n') return std::nullopt;
    const int middle = height / 2;
    std::vector<std::string> lines;
    for (int row = 0; row < height; ++row) {
        const int half_width = middle - std::abs(middle - row);
        std::string line(static_cast<std::size_t>(height), background);
        line[static_cast<std::size_t>(middle - half_width)] = edge;
        line[static_cast<std::size_t>(middle + half_width)] = edge;
        while (!line.empty() && line.back() == ' ') line.pop_back();
        lines.push_back(std::move(line));
    }
    return lines;
}
}
