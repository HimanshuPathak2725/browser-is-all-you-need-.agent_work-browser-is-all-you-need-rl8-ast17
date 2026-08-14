#include "manhattan-voronoi-owners.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::diamond;
int main() {
CHECK(manhattan_voronoi_owners({{0,0},{4,0}},{{1,0},{2,0}}).value()==std::vector<int>({0,-1}));
CHECK(manhattan_voronoi_owners({},{{1,2}}).value()==std::vector<int>{-1});
CHECK(manhattan_voronoi_owners({{0,0}},{}).value().empty());
CHECK(!manhattan_voronoi_owners({{0,0},{0,0}},{}));
CHECK(manhattan_voronoi_owners({{2,3}},{{2,3}}).value()==std::vector<int>{0});
return 0;
}
