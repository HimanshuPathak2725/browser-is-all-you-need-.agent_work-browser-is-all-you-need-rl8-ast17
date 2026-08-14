#include "voxel-shell-sums.h"

#include <cstdlib>

#define CHECK(...) do { if (!static_cast<bool>((__VA_ARGS__))) std::abort(); } while (false)

using namespace charm::v1r87_37414::spiral_matrix;
int main() {
CHECK(voxel_shell_sums({{{1,2},{3,4}}}).value()==std::vector<std::int64_t>{10});
std::vector<std::vector<std::vector<int>>> cube(3,std::vector<std::vector<int>>(3,std::vector<int>(3,1)));CHECK(voxel_shell_sums(cube).value()==std::vector<std::int64_t>({26,1}));
CHECK(!voxel_shell_sums({}));
CHECK(!voxel_shell_sums({{}}));
CHECK(!voxel_shell_sums({{{1}},{{1,2}}}));
return 0;
}
