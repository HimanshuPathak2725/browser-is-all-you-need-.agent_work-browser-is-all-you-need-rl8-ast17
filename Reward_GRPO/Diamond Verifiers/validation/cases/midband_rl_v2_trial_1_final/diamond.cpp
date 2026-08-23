#include "diamond.h"

#include <cstddef>
#include <sstream>
#include <string>
#include <vector>

namespace diamond {

std::vector<std::string> rows(char middle_letter) {
    const std::size_t maximum_level =
        static_cast<std::size_t>(middle_letter - 'A');
    const std::size_t width = 2 * maximum_level + 1;
    std::vector<std::string> result;

    for (std::size_t column = 0; column < width; ++column) {
        const std::size_t distance =
            std::abs(
                static_cast<std::ptrdiff_t>(column) -
                static_cast<std::ptrdiff_t>(maximum_level)
            );
        const std::size_t padding = maximum_level - distance;
        const std::size_t letter_count = 2 * distance + 1;
        const char letter = static_cast<char>('A' + maximum_level - distance);

        std::ostringstream line;
        line << std::string(padding, ' ');
        if (letter_count == 1) {
            line << letter;
        } else {
            line << letter;
            line << static_cast<char>(middle_letter);
            line << letter;
        }
        line << std::string(padding, ' ');
        result.push_back(line.str());
    }
    return result;
}

}  // namespace diamond
