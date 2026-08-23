#pragma once

#include <iostream>

namespace diamond {

/**
 * Prints a diamond shape using the specified character.
 * The character 'A' is at the top and bottom.
 * The supplied character is at the widest points.
 */
void print_diamond(char letter);

/**
 * Returns the number of rows in the diamond for the given character.
 */
int rows(char letter);

} // namespace diamond
