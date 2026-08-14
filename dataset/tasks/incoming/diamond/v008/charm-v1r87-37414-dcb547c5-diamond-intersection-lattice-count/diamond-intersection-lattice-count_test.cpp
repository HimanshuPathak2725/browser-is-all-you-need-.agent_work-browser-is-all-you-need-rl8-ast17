#include "diamond-intersection-lattice-count.cpp"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::diamond;
int main() {
require_case(diamond_intersection_lattice_count({{0,0,1}})==5);
require_case(diamond_intersection_lattice_count({{0,0,1},{1,0,1}})==2);
require_case(diamond_intersection_lattice_count({{0,0,0},{1,0,0}})==0);
require_case(!diamond_intersection_lattice_count({}));
require_case(!diamond_intersection_lattice_count({{0,0,-1}}));
return 0;
}
