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

namespace charm::v1r87_37414::allergies {
struct RotationEntry { int day; std::string allergen; };
std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_exposure_rotation(const std::vector<RotationEntry>& entries, const std::map<std::string,int>& cooldown_days);
}

namespace charm::v1r87_37414::allergies {
inline std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_exposure_rotation(const std::vector<RotationEntry>& entries, const std::map<std::string,int>& cooldown_days) {
std::map<std::string,std::pair<int,std::size_t>> last;
std::vector<std::pair<std::size_t,std::size_t>> out;
int prior=-1;
for(std::size_t i=0;i<entries.size();++i){const auto&e=entries[i];
auto c=cooldown_days.find(e.allergen);
if(e.day<0||e.day<=prior||e.allergen.empty()||c==cooldown_days.end()||c->second<0)return std::nullopt;
auto p=last.find(e.allergen);
if(p!=last.end()&&static_cast<long long>(e.day)-p->second.first<c->second)out.push_back({p->second.second,i});
last[e.allergen]={e.day,i};
prior=e.day;
}return out;

}
}
