#include "voxel-shell-sums.h"

#include <cstdlib>

namespace { void require_case(bool condition) { if (!condition) std::abort(); } }

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
require_case(voxel_shell_sums({{{1,2},{3,4}}}).value()==std::vector<std::int64_t>{10});
std::vector<std::vector<std::vector<int>>> cube(3,std::vector<std::vector<int>>(3,std::vector<int>(3,1)));require_case(voxel_shell_sums(cube).value()==std::vector<std::int64_t>({26,1}));
require_case(!voxel_shell_sums({}));
require_case(!voxel_shell_sums({{}}));
require_case(!voxel_shell_sums({{{1}},{{1,2}}}));
return 0;
}
