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

namespace charm::v1r87_37414::linked_list {

std::optional<int> persistent_common_tail(const std::vector<int>& next, int first_head, int second_head);
}

namespace charm::v1r87_37414::linked_list {
std::optional<int> persistent_common_tail(const std::vector<int>& next, int first_head, int second_head) {
auto valid=[&](int x){return x>=-1&&x<static_cast<int>(next.size());
};
if(!valid(first_head)||!valid(second_head))return std::nullopt;
for(int x:next)if(!valid(x))return std::nullopt;
std::vector<int> state(next.size());
std::function<bool(int)> dfs=[&](int i){if(i<0)return true;
if(state[i]==1)return false;
if(state[i]==2)return true;
state[i]=1;
if(!dfs(next[i]))return false;
state[i]=2;
return true;
};
for(std::size_t i=0;i<next.size();++i)if(!dfs(static_cast<int>(i)))return std::nullopt;
std::set<int> path;
for(int i=first_head;i>=0;i=next[i])path.insert(i);
for(int i=second_head;i>=0;i=next[i])if(path.count(i))return i;
return -1;

}
}
