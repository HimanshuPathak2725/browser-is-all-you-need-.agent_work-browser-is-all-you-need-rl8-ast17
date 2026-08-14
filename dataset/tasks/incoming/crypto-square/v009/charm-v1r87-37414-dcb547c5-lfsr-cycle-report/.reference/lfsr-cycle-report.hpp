#pragma once

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

namespace charm::v1r87_37414::crypto_square {

std::optional<std::pair<std::size_t,std::size_t>> lfsr_cycle_report(std::string_view seed, const std::vector<std::size_t>& taps);
}

namespace charm::v1r87_37414::crypto_square {
inline std::optional<std::pair<std::size_t,std::size_t>> lfsr_cycle_report(std::string_view seed, const std::vector<std::size_t>& taps) {
if(seed.empty()||seed.size()>20||taps.empty()||!std::all_of(seed.begin(),seed.end(),[](char c){return c=='0'||c=='1';}))return std::nullopt;
std::set<std::size_t> unique;
for(auto t:taps)if(t>=seed.size()||!unique.insert(t).second)return std::nullopt;
std::map<std::string,std::size_t> at;
std::string state(seed);
for(std::size_t step=0;;++step){auto [it,fresh]=at.emplace(state,step);
if(!fresh)return std::pair<std::size_t,std::size_t>{it->second,step-it->second};
char bit='0';
for(auto t:taps)if(state[t]=='1')bit=bit=='0'?'1':'0';
state=bit+state.substr(0,state.size()-1);
}
}
}
