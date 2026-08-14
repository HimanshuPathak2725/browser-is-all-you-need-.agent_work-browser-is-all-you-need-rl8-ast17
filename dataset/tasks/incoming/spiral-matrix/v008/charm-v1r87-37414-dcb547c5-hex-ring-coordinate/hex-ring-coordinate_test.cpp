#include "hex-ring-coordinate.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
require_case(hex_ring_coordinate(0)==AxialPoint{0,0});
require_case(hex_ring_coordinate(1)==AxialPoint{1,0});
require_case(hex_ring_coordinate(2)==AxialPoint{0,1});
require_case(hex_ring_coordinate(6)==AxialPoint{1,-1});
require_case(hex_ring_coordinate(7)==AxialPoint{2,0});
return 0;
}
