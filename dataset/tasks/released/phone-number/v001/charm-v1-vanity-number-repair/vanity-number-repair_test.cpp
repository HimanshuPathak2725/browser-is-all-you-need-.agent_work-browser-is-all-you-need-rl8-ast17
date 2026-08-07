#include "vanity-number-repair.h"
#include <cassert>
#include <optional>
#include <string>
using charm::phone::normalize_vanity;
int main() {
    assert(normalize_vanity("1-800-FLOWERS") == std::optional<std::string>("18003569377"));
    assert(normalize_vanity("212-PAINTER") == std::optional<std::string>("2127246837"));
    assert(normalize_vanity("+1 (800) FLOWERS") == std::optional<std::string>("+18003569377"));
    assert(!normalize_vanity("+212-PAINTER"));
    assert(!normalize_vanity("21+2PAINTER"));
    assert(!normalize_vanity("CALL"));
    assert(!normalize_vanity("212_PAINTER"));
    assert(normalize_vanity("9999999999") == std::optional<std::string>("9999999999"));
    return 0;
}
