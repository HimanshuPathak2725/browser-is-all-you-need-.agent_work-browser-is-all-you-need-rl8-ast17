#include "clipped-diamond-repair.hpp"
#include <cassert>
#include <utility>
#include <vector>
using charm::diamond::Rect;
using charm::diamond::clipped_cells;
int main() {
    assert(clipped_cells(0, 0, -1, {0,0,2,2}).empty());
    assert(clipped_cells(0, 0, 1, {2,2,1,3}).empty());
    assert((clipped_cells(0, 0, 0, {-1,-1,2,2}) == std::vector<std::pair<int,int>>{{1,1}}));
    assert((clipped_cells(0, 0, 1, {0,0,2,2}) == std::vector<std::pair<int,int>>{{0,0},{1,0},{0,1}}));
    const auto cells = clipped_cells(5, 5, 2, {4,4,7,7});
    assert(cells.size() == 9);
    assert(cells.front() == std::make_pair(0,0) && cells.back() == std::make_pair(2,2));
    assert(clipped_cells(0, 0, 5, {1,1,1,4}).empty());
    return 0;
}
