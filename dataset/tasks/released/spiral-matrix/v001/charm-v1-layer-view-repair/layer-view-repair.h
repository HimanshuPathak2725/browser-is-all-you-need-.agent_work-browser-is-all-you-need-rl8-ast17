#pragma once
#include <cstddef>
#include <vector>
namespace charm::spiral {
inline std::vector<int> layer_clockwise(const std::vector<std::vector<int>>& matrix, std::size_t layer) {
    if (matrix.empty() || matrix.front().empty()) return {};
    for (const auto& row : matrix) if (row.size() != matrix.front().size()) return {};
    const std::size_t top = layer, left = layer;
    if (top >= matrix.size() || left >= matrix.front().size()) return {};
    const std::size_t bottom = matrix.size() - 1 - layer;
    const std::size_t right = matrix.front().size() - 1 - layer;
    if (top > bottom || left > right) return {};
    std::vector<int> out;
    for (std::size_t column = left; column <= right; ++column) out.push_back(matrix[top][column]);
    for (std::size_t row = top + 1; row <= bottom; ++row) out.push_back(matrix[row][right]);
    if (bottom > top) for (std::size_t column = right; column-- > left;) out.push_back(matrix[bottom][column]);
    if (right > left) for (std::size_t row = bottom; row-- > top + 1;) out.push_back(matrix[row][left]);
    return out;
}
}
