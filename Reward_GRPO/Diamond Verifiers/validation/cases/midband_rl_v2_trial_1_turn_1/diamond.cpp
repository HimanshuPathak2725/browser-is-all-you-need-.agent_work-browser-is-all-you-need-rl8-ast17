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
        std::ostringstream line;
        const std::size_t outer = maximum_level + 1;
        const std::size_t left = column < outer ? column : outer + column - width + 1;
        const std::size_t right = width - left;
        const std::size_t padding = maximum_level - left;
        const std::size_t letter_count = left + right;

        line << std::string(padding, ' ');
        if (letter_count == 1) {
            line << static_cast<char>('A' + left);
        } else {
            line << static_cast<char>('A' + left);
            line << static_cast<char>('A' + right);
        }
        line << std::string(padding, ' ');
        result.push_back(line.str());
    }
    return result;
}

}  // namespace diamond
