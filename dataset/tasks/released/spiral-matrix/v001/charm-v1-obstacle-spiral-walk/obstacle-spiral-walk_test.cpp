#include "obstacle-spiral-walk.cpp"
#include <cassert>
#include <vector>
using charm::spiral::Cell;
using charm::spiral::walk;
int main() {
    assert(walk({}, {0,0}).empty());
    assert(walk({"..","."}, {0,0}).empty());
    assert(walk({"#"}, {0,0}).empty());
    assert((walk({"."}, {0,0}) == std::vector<Cell>{{0,0}}));
    assert((walk({"...","..."}, {0,0}) == std::vector<Cell>{{0,0},{0,1},{0,2},{1,2},{1,1},{1,0}}));
    assert((walk({"...",".#.","..."}, {0,0}) == std::vector<Cell>{{0,0},{0,1},{0,2},{1,2},{2,2},{2,1},{2,0},{1,0}}));
    assert(walk({".."}, {-1,0}).empty());
    return 0;
}
