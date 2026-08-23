#include "diamond.h"

#include <cstdlib>
#include <string>
#include <vector>

namespace diamond {

std::vector<std::string> rows(char middle_letter) {
    const int max_dist = static_cast<int>(middle_letter) - 'A';
    const int size = 2 * max_dist + 1;
    std::vector<std::string> result;

    for (int row = 0; row < size; ++row) {
        const int dist = std::abs(row - max_dist);
        const int width = 2 * dist + 1;
        const int padding = (size - width) / 2;

        const int left = middle_letter + dist;
        const char left_char = static_cast<char>(
            std::max('A', std::min('Z', static_cast<char>(left))));
        const char middle_char = middle_letter;
        const int right = middle_letter + dist;
        const char right_char = static_cast<char>(
            std::max('A', std::min('Z', static_cast<char>(right))));

        std::string row_str(padding, ' ');
        if (width > 1) {
            row_str.push_back(left_char);
        }
        if (width > 2) {
            row_str.push_back(middle_char);
        }
        if (width > 1) {
            row_str.push_back(right_char);
        }
        row_str.append(padding, ' ');

        result.push_back(row_str);
    }
    return result;
}

}  // namespace diamond
