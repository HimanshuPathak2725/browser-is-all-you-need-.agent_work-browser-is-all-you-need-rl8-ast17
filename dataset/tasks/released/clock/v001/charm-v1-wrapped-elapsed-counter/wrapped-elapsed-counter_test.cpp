#include "wrapped-elapsed-counter.hpp"
#include <cassert>
#include <limits>
#include <optional>
using charm::clockwork::elapsed;
int main() {
    assert(elapsed(100, 500, 0) == std::optional<long long>(400));
    assert(!elapsed(1000, 500, 0));
    assert(elapsed(1000, 500, 1) == std::optional<long long>(940));
    assert(elapsed(0, 0, 0) == std::optional<long long>(0));
    assert(elapsed(0, 0, 2) == std::optional<long long>(2880));
    assert(!elapsed(-1, 0, 0) && !elapsed(0, 1440, 0));
    assert(!elapsed(0, 0, -1));
    assert(!elapsed(0, 0, std::numeric_limits<long long>::max()));
    return 0;
}
