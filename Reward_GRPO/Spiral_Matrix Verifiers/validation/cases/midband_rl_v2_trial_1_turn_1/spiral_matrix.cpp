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
    uint32_t top = 0;
    uint32_t bottom = size - 1;
    uint32_t left = 0;
    uint32_t right = size - 1;
    uint32_t value = 1;

    while (top <= bottom && left <= right) {
        for (uint32_t column = left; column <= right; ++column) {
            matrix[top][column] = value++;
        }
        ++top;

        for (uint32_t row = top; row <= bottom; ++row) {
            matrix[row][right] = value++;
        }
        --right;

        if (top <= bottom) {
            for (uint32_t column = right;
                 column >= left; --column) {
                matrix[bottom][column] = value++;
            }
            --bottom;
        }

        if (left <= right) {
            for (uint32_t row = bottom; row >= top; --row) {
                matrix[row][left] = value++;
            }
            ++left;
        }
    }
    return matrix;
}

}  // namespace spiral_matrix
