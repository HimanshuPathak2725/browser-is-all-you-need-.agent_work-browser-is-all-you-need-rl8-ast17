#include "rank-interval-counts.hpp"

#include <cassert>

using namespace charm::v1n7::binary_search_tree;
int main() {
    assert((tree_rank_interval_sums({5,1,3},{{0,2},{1,3},{2,2}}).value()==std::vector<long long>{4,8,0}));
    assert(tree_rank_interval_sums({},{})->empty());
    assert(!tree_rank_interval_sums({1,1},{}));
    assert(!tree_rank_interval_sums({1},{{0,2}}));
    assert(tree_rank_interval_sums({-2,4},{{0,2}})->at(0)==2);
    return 0;
}
