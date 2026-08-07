#include "owned-duplicate-policy-build.h"

#include <cassert>

using namespace charm::v1n7::binary_search_tree;
int main() {
    auto r=build_owned_tree({4,2,6,2},DuplicatePolicy::right);assert(r&&r->inorder==(std::vector<int>{2,2,4,6})&&r->max_depth==2);
    assert(build_owned_tree({},DuplicatePolicy::reject)->max_depth==-1);
    assert(!build_owned_tree({1,1},DuplicatePolicy::reject));
    assert(build_owned_tree({1,1},DuplicatePolicy::left)->max_depth==1);
    assert(build_owned_tree({3,1,5},DuplicatePolicy::reject)->max_depth==1);
    return 0;
}
