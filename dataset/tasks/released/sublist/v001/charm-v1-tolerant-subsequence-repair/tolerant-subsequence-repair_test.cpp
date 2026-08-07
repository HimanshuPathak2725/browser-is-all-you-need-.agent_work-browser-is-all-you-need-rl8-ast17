#include "tolerant-subsequence-repair.h"
#include <cassert>
#include <limits>
#include <vector>
using charm::sublist::tolerant_subsequence;
int main() {
    assert(!tolerant_subsequence({1}, {1}, -1));
    assert(tolerant_subsequence({1,2}, {}, 0) == std::vector<std::size_t>{});
    assert(tolerant_subsequence({1,4,7,10}, {2,8}, 1) == std::vector<std::size_t>({0,2}));
    assert(tolerant_subsequence({0,2,2,4}, {2,2}, 0) == std::vector<std::size_t>({1,2}));
    assert(!tolerant_subsequence({1,2}, {2,1}, 0));
    assert(tolerant_subsequence({5}, {7}, 2) == std::vector<std::size_t>({0}));
    assert(!tolerant_subsequence({std::numeric_limits<long long>::min()}, {std::numeric_limits<long long>::max()}, std::numeric_limits<long long>::max()));
    return 0;
}
