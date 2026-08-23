#include "diamond.h"

#include <cstddef>
#include <string>
#include <vector>

namespace diamond {

std::vector<std::string> rows(char middle_letter) {
    const std::size_t n = static_cast<std::size_t>(middle_letter - 'A');
    const std::size_t height = 2 * n + 1;
    const std::size_t width = 2 * height - 1;
    std::vector<std::string> result;

    const std::size_t outer = (width - 1) / 2;

    for (std::size_t row = 0; row < height; ++row) {
        std::string row_str(width, ' ');
        const std::size_t dist = std::max(row, height - 1 - row);

        if (row == 0 || row == height - 1) {
            row_str[outer] = middle_letter;
        } else {
            const std::size_t current_dist = outer - dist;
            row_str[current_dist] = middle_letter - dist;
            row_str[width - 1 - current_dist] = middle_letter - dist;
        }
        result.push_back(row_str);
    }
    for (std::size_t row = height; row-- > 0;) {
        std::string row_str(width, ' ');
        const std::size_t dist = std::max(row, height - 1 - row);

        if (row == 0 || row == height - 1) {
            row_str[outer] = middle_letter;
        } else {
            const std::size_t current_dist = outer - dist;
            row_str[current_dist] = middle_letter - dist;
            row_str[width - 1 - current_dist] = middle_letter - dist;
        }
        result.push_back(row_str);
    }
    return result;
}

}  // namespace diamond
