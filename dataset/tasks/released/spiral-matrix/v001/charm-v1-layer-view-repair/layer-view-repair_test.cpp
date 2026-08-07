#include "layer-view-repair.h"
#include <cassert>
#include <vector>
using charm::spiral::layer_clockwise;
int main() {
    assert(layer_clockwise({}, 0).empty());
    assert(layer_clockwise({{1,2},{3}}, 0).empty());
    assert((layer_clockwise({{1,2,3}}, 0) == std::vector<int>{1,2,3}));
    assert((layer_clockwise({{1},{2},{3}}, 0) == std::vector<int>{1,2,3}));
    const std::vector<std::vector<int>> matrix{{1,2,3,4},{5,6,7,8},{9,10,11,12},{13,14,15,16}};
    assert((layer_clockwise(matrix,0) == std::vector<int>{1,2,3,4,8,12,16,15,14,13,9,5}));
    assert((layer_clockwise(matrix,1) == std::vector<int>{6,7,11,10}));
    assert(layer_clockwise(matrix,2).empty());
    return 0;
}
