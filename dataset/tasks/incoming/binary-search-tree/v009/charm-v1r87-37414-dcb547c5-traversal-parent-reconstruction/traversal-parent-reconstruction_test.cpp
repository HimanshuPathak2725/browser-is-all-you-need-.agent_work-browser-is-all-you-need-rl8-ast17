#include "traversal-parent-reconstruction.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
CHECK(reconstruct_preorder_parents({4,2,1,3,6},{1,2,3,4,6}).value()==std::vector<int>({-1,0,1,1,0}));
CHECK(reconstruct_preorder_parents({},{}).value().empty());
CHECK(!reconstruct_preorder_parents({1,1},{1,1}));
CHECK(!reconstruct_preorder_parents({1,2},{2,3}));
CHECK(!reconstruct_preorder_parents({1,2},{1}));
return 0;
}
