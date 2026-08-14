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

namespace charm::v1r87_37414::yacht {

std::optional<std::vector<std::size_t>> equal_sum_dice_partition(const std::vector<int>& dice);
}

namespace charm::v1r87_37414::yacht {
std::optional<std::vector<std::size_t>> equal_sum_dice_partition(const std::vector<int>& dice) {
if(dice.size()<2||dice.size()>24||std::any_of(dice.begin(),dice.end(),[](int x){return x<=0;}))return std::nullopt;
long long total=std::accumulate(dice.begin(),dice.end(),0LL);
if(total%2)return std::vector<std::size_t>{};
std::vector<std::size_t> best;
bool found=false;
std::uint64_t limit=std::uint64_t{1}<<dice.size();
for(std::uint64_t bits=1;bits+1<limit;++bits){if(!(bits&1))continue;
long long sum=0;
std::vector<std::size_t> pick;
for(std::size_t i=0;i<dice.size();++i)if(bits&(std::uint64_t{1}<<i)){sum+=dice[i];
pick.push_back(i);
}
if(sum*2==total&&(!found||pick<best)){best=pick;
found=true;
}}
return best;

}
}
