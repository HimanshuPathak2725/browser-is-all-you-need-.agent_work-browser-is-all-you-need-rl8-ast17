#include "keyed-square-transposition.h"
#include <cassert>
#include <optional>
#include <string>
#include <vector>
using charm::cryptosquare::encode_keyed;
int main() {
    assert(encode_keyed("", {}) == std::optional<std::string>(""));
    assert(!encode_keyed("", {0}));
    assert(encode_keyed("A b!12", {1, 0}) == std::optional<std::string>("ba 21"));
    assert(encode_keyed("abcdefghi", {2, 0, 1}) == std::optional<std::string>("cab fde igh"));
    assert(!encode_keyed("abcd", {0}));
    assert(!encode_keyed("abcd", {0, 0}));
    assert(!encode_keyed("abcd", {0, 2}));
    return 0;
}
