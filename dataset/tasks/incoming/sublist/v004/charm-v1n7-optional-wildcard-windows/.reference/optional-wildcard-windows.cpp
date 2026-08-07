#include <algorithm>
#include <array>
#include <climits>
#include <cstdlib>
#include <future>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <functional>
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

namespace charm::v1n7::sublist {

std::vector<std::size_t> optional_pattern_positions(const std::vector<int>& values, const std::vector<std::optional<int>>& pattern);
}

std::vector<std::size_t> charm::v1n7::sublist::optional_pattern_positions(const std::vector<int>& values,const std::vector<std::optional<int>>& pattern){std::vector<std::size_t> out;if(pattern.empty()){for(std::size_t i=0;i<=values.size();++i)out.push_back(i);return out;}if(pattern.size()>values.size())return out;for(std::size_t start=0;start+pattern.size()<=values.size();++start){bool match=true;for(std::size_t i=0;i<pattern.size();++i)if(pattern[i]&&*pattern[i]!=values[start+i]){match=false;break;}if(match)out.push_back(start);}return out;}
