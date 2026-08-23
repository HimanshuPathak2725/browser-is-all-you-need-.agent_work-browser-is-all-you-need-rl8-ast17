#include "diamond.h"
#include <iostream>
#include <cmath>

namespace diamond {

void print_diamond(char letter) {
    // Determine the distance from 'A' to the input letter
    int n = static_cast<int>(letter - 'A');
    // The total height of the diamond is 2 * n + 1
    int height = 2 * n + 1;

    for (int i = 0; i < height; ++i) {
        // Calculate the current character index relative to 'A'
        // This handles the ascending left side and descending right side
        int c = std::abs(i - n);

        // Calculate the number of leading spaces
        int leading_spaces = n - c;

        // Calculate the number of trailing spaces to ensure symmetry
        // The trailing spaces are exactly twice the leading spaces
        int trailing_spaces = 2 * leading_spaces;

        // Print leading spaces
        for (int j = 0; j < leading_spaces; ++j) {
            std::cout << ' ';
        }

        // Print the current letter
        std::cout << static_cast<char>('A' + c);

        // Print trailing spaces
        for (int j = 0; j < trailing_spaces; ++j) {
            std::cout << ' ';
        }

        // Move to the next line
        std::cout << std::endl;
    }
}

int diamond::rows(char letter) {
    // The number of rows is 2 * (distance from A) + 1
    return 2 * (letter - 'A') + 1;
}

} // namespace diamond
