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

namespace charm::v1r87_37414::grade_school {
struct Appeal { std::string student; std::size_t expected_version; int delta; };
std::optional<std::map<std::string,std::pair<int,std::size_t>>> replay_grade_appeals(const std::map<std::string,int>& initial, const std::vector<Appeal>& appeals);
}

namespace charm::v1r87_37414::grade_school {
std::optional<std::map<std::string,std::pair<int,std::size_t>>> replay_grade_appeals(const std::map<std::string,int>& initial, const std::vector<Appeal>& appeals) {
std::map<std::string,std::pair<int,std::size_t>> state;
for(auto [s,v]:initial){if(s.empty()||v<0||v>100)return std::nullopt;
state[s]={v,0};
}for(const auto&a:appeals){auto it=state.find(a.student);
if(a.student.empty()||it==state.end()||it->second.second!=a.expected_version)return std::nullopt;
long long next=static_cast<long long>(it->second.first)+a.delta;
if(next<0||next>100)return std::nullopt;
it->second={static_cast<int>(next),it->second.second+1};
}return state;

}
}
