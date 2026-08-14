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

namespace charm::v1r87_37414::kindergarten_garden {

std::optional<std::vector<bool>> eastward_shadow_profile(const std::vector<int>& heights, int slope);
}

namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<bool>> eastward_shadow_profile(const std::vector<int>& heights, int slope) {
if(slope<=0||std::any_of(heights.begin(),heights.end(),[](int h){return h<0;}))return std::nullopt;
std::vector<bool> out(heights.size());
long long best=std::numeric_limits<long long>::min();
for(std::size_t i=0;i<heights.size();++i){auto projected=static_cast<long long>(heights[i])+static_cast<long long>(slope)*static_cast<long long>(i);
out[i]=best>projected;
best=std::max(best,projected);
}return out;

}
}
