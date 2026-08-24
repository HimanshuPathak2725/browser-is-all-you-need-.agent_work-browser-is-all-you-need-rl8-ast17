#include "spiral_matrix.h"

#include <cstdint>
#include <vector>

namespace spiral_matrix {

std::vector<std::vector<uint32_t>> spiral_matrix(uint32_t size) {
    if (size == 0) {
        return {};
    }
    std::vector<std::vector<uint32_t>> matrix(
        size, std::vector<uint32_t>(size, 0));
    int top = 0;
    int bottom = static_cast<int>(size) - 1;
    int left = 0;
    int right = static_cast<int>(size) - 1;
    uint32_t num = 1;

    while (top <= bottom && left <= right) {
        for (int column = left; column <= right; ++column) {
            matrix[static_cast<std::size_t>(top)][static_cast<std::size_t>(column)] = num++;
        }
        ++top;

        for (int row = top; row <= bottom; ++row) {
            matrix[static_cast<std::size_t>(row)][static_cast<std::size_t>(right)] = num++;
        }
        --right;

        if (top <= bottom) {
            for (int column = right; column >= left; --column) {
                matrix[static_cast<std::size_t>(bottom)][static_cast<std::size_t>(column)] = num++;
            }
            --bottom;
        }

        if (left <= right) {
            for (int row = bottom; row >= top; --row) {
                matrix[static_cast<std::size_t>(row)][static_cast<std::size_t>(left)] = num++;
            }
            ++left;
        }
    }
    return matrix;
}

}  // namespace spiral_matrix
