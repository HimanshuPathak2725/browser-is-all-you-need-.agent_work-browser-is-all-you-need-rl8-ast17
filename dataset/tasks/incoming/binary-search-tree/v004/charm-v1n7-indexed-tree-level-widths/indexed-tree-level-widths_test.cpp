#include "indexed-tree-level-widths.cpp"

#include <cassert>

using namespace charm::v1n7::binary_search_tree;
int main() {
    assert((strict_tree_level_widths({{4,1,2},{2,-1,-1},{6,-1,-1}}).value()==std::vector<std::size_t>{1,2}));
    assert(strict_tree_level_widths({})->empty());
    assert(!strict_tree_level_widths({{1,0,-1}}));
    assert(!strict_tree_level_widths({{2,1,-1},{3,-1,-1}}));
    assert(!strict_tree_level_widths({{1,-1,-1},{2,-1,-1}}));
    return 0;
}
