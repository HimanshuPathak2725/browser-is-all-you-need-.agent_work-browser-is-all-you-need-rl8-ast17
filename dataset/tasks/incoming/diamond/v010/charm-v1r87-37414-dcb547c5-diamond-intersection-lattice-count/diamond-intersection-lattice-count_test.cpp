#include "diamond-intersection-lattice-count.cpp"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::diamond;
int main() {
CHECK(diamond_intersection_lattice_count({{0,0,1}})==5);
CHECK(diamond_intersection_lattice_count({{0,0,1},{1,0,1}})==2);
CHECK(diamond_intersection_lattice_count({{0,0,0},{1,0,0}})==0);
CHECK(!diamond_intersection_lattice_count({}));
CHECK(!diamond_intersection_lattice_count({{0,0,-1}}));
return 0;
}
