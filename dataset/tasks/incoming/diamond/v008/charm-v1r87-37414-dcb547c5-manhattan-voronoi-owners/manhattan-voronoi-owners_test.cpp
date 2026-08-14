#include "manhattan-voronoi-owners.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::diamond;
int main() {
require_case(manhattan_voronoi_owners({{0,0},{4,0}},{{1,0},{2,0}}).value()==std::vector<int>({0,-1}));
require_case(manhattan_voronoi_owners({},{{1,2}}).value()==std::vector<int>{-1});
require_case(manhattan_voronoi_owners({{0,0}},{}).value().empty());
require_case(!manhattan_voronoi_owners({{0,0},{0,0}},{}));
require_case(manhattan_voronoi_owners({{2,3}},{{2,3}}).value()==std::vector<int>{0});
return 0;
}
