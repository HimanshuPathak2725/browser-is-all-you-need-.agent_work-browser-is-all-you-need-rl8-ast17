#include "hex-ring-coordinate.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
CHECK(hex_ring_coordinate(0)==AxialPoint{0,0});
CHECK(hex_ring_coordinate(1)==AxialPoint{1,0});
CHECK(hex_ring_coordinate(2)==AxialPoint{0,1});
CHECK(hex_ring_coordinate(6)==AxialPoint{1,-1});
CHECK(hex_ring_coordinate(7)==AxialPoint{2,0});
return 0;
}
