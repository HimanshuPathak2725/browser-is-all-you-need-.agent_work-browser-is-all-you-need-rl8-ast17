#include "traversal-parent-reconstruction.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::binary_search_tree;
int main() {
require_case(reconstruct_preorder_parents({4,2,1,3,6},{1,2,3,4,6}).value()==std::vector<int>({-1,0,1,1,0}));
require_case(reconstruct_preorder_parents({},{}).value().empty());
require_case(!reconstruct_preorder_parents({1,1},{1,1}));
require_case(!reconstruct_preorder_parents({1,2},{2,3}));
require_case(!reconstruct_preorder_parents({1,2},{1}));
return 0;
}
