#include "known-bit-domain-decoder.h"

#include <cassert>

using namespace charm::v1n7::allergies;
int main() {
    const std::vector<AllergenBit> domain{{4U,"cats"},{1U,"eggs"},{2U,"nuts"}};
    assert((decode_known_allergies(5U, domain).value()==std::vector<std::string>{"eggs","cats"}));
    assert(decode_known_allergies(0U, domain)->empty());
    assert(!decode_known_allergies(8U, domain));
    assert(!decode_known_allergies(1U, {{3U,"bad"}}));
    assert(!decode_known_allergies(1U, {{1U,"x"},{2U,"x"}}));
    return 0;
}
