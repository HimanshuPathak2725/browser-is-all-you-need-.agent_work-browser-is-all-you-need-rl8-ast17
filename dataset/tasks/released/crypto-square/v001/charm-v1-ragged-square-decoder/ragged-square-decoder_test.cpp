#include "ragged-square-decoder.hpp"
#include <cassert>
#include <optional>
#include <string>
using charm::cryptosquare::decode_columns;
int main() {
    assert(decode_columns("") == std::optional<std::string>(""));
    assert(decode_columns("ac bd") == std::optional<std::string>("abcd"));
    assert(decode_columns("adg beh cf") == std::optional<std::string>("abcdefgh"));
    assert(decode_columns("ad beh cf") == std::nullopt);
    assert(decode_columns("abc d") == std::nullopt);
    assert(decode_columns("ab c de") == std::nullopt);
    assert(decode_columns("ab c!") == std::nullopt);
    assert(decode_columns("ab  c") == std::optional<std::string>("acb"));
    return 0;
}
