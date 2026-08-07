#include "strict-glyph-diamond-validator.hpp"

#include <cassert>

using charm::v1n7::diamond::is_strict_glyph_diamond;
int main(){assert(is_strict_glyph_diamond({".*.","***",".*."},'*','.'));assert(is_strict_glyph_diamond({"x"},'x',' '));assert(!is_strict_glyph_diamond({},'*','.'));assert(!is_strict_glyph_diamond({"**","**"},'*','.'));assert(!is_strict_glyph_diamond({".*.","**.",".*."},'*','.'));return 0;}
