#include <algorithm>
#include <array>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace charm::v1r87_37414::diamond {
struct ManhattanDiamond { int row; int col; int radius; };
std::optional<std::size_t> diamond_intersection_lattice_count(const std::vector<ManhattanDiamond>& diamonds);
}

namespace charm::v1r87_37414::diamond {
std::optional<std::size_t> diamond_intersection_lattice_count(const std::vector<ManhattanDiamond>& diamonds) {
if(diamonds.empty())return std::nullopt;
for(const auto&d:diamonds)if(d.radius<0||d.radius>500)return std::nullopt;
int lo_r=diamonds[0].row-diamonds[0].radius,hi_r=diamonds[0].row+diamonds[0].radius,lo_c=diamonds[0].col-diamonds[0].radius,hi_c=diamonds[0].col+diamonds[0].radius;
std::size_t count=0;
for(int r=lo_r;r<=hi_r;++r)for(int c=lo_c;c<=hi_c;++c)if(std::all_of(diamonds.begin(),diamonds.end(),[&](const auto&d){return std::abs(static_cast<long long>(r)-d.row)+std::abs(static_cast<long long>(c)-d.col)<=d.radius;}))++count;
return count;

}
}
