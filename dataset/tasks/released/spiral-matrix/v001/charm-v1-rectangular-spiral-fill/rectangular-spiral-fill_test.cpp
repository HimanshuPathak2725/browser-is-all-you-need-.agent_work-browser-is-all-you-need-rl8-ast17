#include "rectangular-spiral-fill.h"
#include <cassert>
#include <vector>
using charm::spiral::Corner;
using charm::spiral::fill;
int main() {
    assert(fill(0, 3, Corner::top_left, 1, 1).empty());
    assert((fill(1, 3, Corner::top_left, 5, 2) == std::vector<std::vector<long long>>{{5,7,9}}));
    assert((fill(2, 3, Corner::top_left, 1, 1) == std::vector<std::vector<long long>>{{1,2,3},{6,5,4}}));
    assert((fill(2, 3, Corner::top_right, 1, 1) == std::vector<std::vector<long long>>{{5,6,1},{4,3,2}}));
    assert((fill(2, 2, Corner::bottom_right, 10, -2) == std::vector<std::vector<long long>>{{6,4},{8,10}}));
    assert((fill(3, 1, Corner::bottom_left, 0, 3) == std::vector<std::vector<long long>>{{6},{3},{0}}));
    const auto repeat = fill(3, 4, Corner::bottom_right, -1, 0);
    for (const auto& row : repeat) for (long long value : row) assert(value == -1);
    return 0;
}
