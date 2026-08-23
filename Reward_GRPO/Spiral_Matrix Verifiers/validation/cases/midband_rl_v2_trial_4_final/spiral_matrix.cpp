#include "spiral_matrix.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace spiral_matrix {

std::vector<std::vector<uint32_t>> spiral_matrix(uint32_t size) {
    if (size == 0U) {
        return {};
    }
    std::vector<std::vector<uint32_t>> matrix(
        size, std::vector<uint32_t>(size, 0U));
    std::int64_t top = 0;
    std::int64_t bottom = static_cast<std::int64_t>(size) - 1;
    std::int64_t left = 0;
    std::int64_t right = static_cast<std::int64_t>(size) - 1;
    std::uint32_t value = 1U;

    while (top <= bottom && left <= right) {
        for (std::int64_t column = left; column <= right; ++column) {
            matrix[static_cast<std::size_t>(top)]
                  [static_cast<std::size_t>(column)] = value++;
        }
        ++top;

        for (std::int64_t row = top; row <= bottom; ++row) {
            matrix[static_cast<std::size_t>(row)]
                  [static_cast<std::size_t>(right)] = value++;
        }
        --right;

        if (top <= bottom) {
            for (std::int64_t column = right; column >= left; --column) {
                matrix[static_cast<std::size_t>(bottom)]
                      [static_cast<std::size_t>(column)] = value++;
            }
            --bottom;
        }

        if (left <= right) {
            for (std::int64_t row = bottom; row >= top; --row) {
                matrix[static_cast<std::size_t>(row)]
                      [static_cast<std::size_t>(left)] = value++;
            }
            ++left;
        }
    }
    return matrix;
}

}  // namespace spiral_matrix
