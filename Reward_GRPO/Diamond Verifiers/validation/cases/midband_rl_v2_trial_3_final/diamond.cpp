#include "diamond.h"

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

namespace diamond {

std::vector<std::string> rows(char middle_letter) {
    const std::size_t maximum_level =
        static_cast<std::size_t>(middle_letter - 'A');
    const std::size_t width = 2 * maximum_level + 1;
    std::vector<std::string> result;

    for (std::size_t level = 0; level <= maximum_level; ++level) {
        std::string row(width, ' ');
        const std::size_t letter = level;
        const std::size_t opposite_letter = width - 1U - level;
        const char letter_char = static_cast<char>('A' + level);

        row[letter] = letter_char;
        row[opposite_letter] = letter_char;
        result.push_back(row);
    }
    for (std::size_t level = maximum_level; level-- > 0;) {
        std::string row(width, ' ');
        const std::size_t letter = level;
        const std::size_t opposite_letter = width - 1U - level;
        const char letter_char = static_cast<char>('A' + level);

        row[letter] = letter_char;
        row[opposite_letter] = letter_char;
        result.push_back(row);
    }
    return result;
}

}  // namespace diamond
